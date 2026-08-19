// dbz1 - Model pipeline integration (project-side).

#include "mod_pipeline.h"

#include <rex/filesystem.h>
#include <rex/logging.h>

#include <windows.h>

#include "settings.h"

#include <cstdio>
#include <exception>
#include <fstream>
#include <sstream>
#include <vector>

namespace dbz1::launcher {

namespace {

// Project root = the folder that contains "mods" (walk up from the exe until
// an "assets" folder is found; same heuristic as dbz1::ModsRoot).
std::filesystem::path ProjectRoot() {
  auto exe_dir = rex::filesystem::GetExecutableFolder();
  std::filesystem::path probe = exe_dir;
  for (int depth = 0; depth < 6; ++depth) {
    if (std::filesystem::is_directory(probe / "assets")) {
      return probe;
    }
    probe = probe.parent_path();
  }
  return exe_dir;
}

std::filesystem::path PipelineScript() {
  return ProjectRoot() / "mod center hd" / "launcher_mod_pipeline.py";
}

std::filesystem::path CatalogFile() {
  return ProjectRoot() / "mod center hd" / "cache" / "characters.cat";
}

// Quote a path/arg for the Windows command line.
std::string Quote(const std::string& s) { return "\"" + s + "\""; }

std::string PythonExecutable() {
  // Environment override first, then rely on PATH.
  if (const char* py = std::getenv("DBZ1_PYTHON"); py && *py) {
    return py;
  }
  return "python";
}

// Append a --key <value> pair to args when value is non-empty.
void PushOpt(std::vector<std::string>& args, const std::string& key,
             const std::string& value) {
  if (!value.empty()) {
    args.push_back(key);
    args.push_back(value);
  }
}

int ParseIntField(const std::string& s) {
  return s.empty() ? 0 : std::atoi(s.c_str());
}

}  // namespace

ModPipeline::~ModPipeline() {
  Shutdown();
}

void ModPipeline::Shutdown() {
  // Join any in-flight worker before this object (or its owner) is destroyed.
  // The worker only writes to members via AppendOutput and never waits on
  // anything else, so joining from the UI thread is safe (it just waits for
  // the python process to finish writing its output).
  if (worker_.joinable()) {
    worker_.join();
  }
}

bool ModPipeline::LoadCatalog() {
  std::lock_guard<std::mutex> lock(mutex_);
  b1_.clear();
  b3_.clear();
  loaded_ = false;

  std::ifstream in(CatalogFile());
  if (!in.is_open()) {
    REXLOG_WARN("dbz1: catalog not found at {}", CatalogFile().string());
    return false;
  }
  std::string line;
  while (std::getline(in, line)) {
    if (line.empty() || line[0] == '#') {
      continue;
    }
    // game|label|name|variant|playable|note|main|geom|tex|acm|csk|verts|awgs
    std::vector<std::string> parts;
    std::stringstream ss(line);
    std::string part;
    while (std::getline(ss, part, '|')) {
      parts.push_back(part);
    }
    if (parts.size() < 8) {
      continue;
    }
    ModChar c;
    c.game = parts[0];
    c.label = parts[1];
    c.name = parts[2];
    if (parts.size() > 3) c.variant = parts[3];
    if (parts.size() > 4) c.playable = ParseIntField(parts[4]) != 0;
    if (parts.size() > 5) c.note = parts[5];
    if (parts.size() > 6) c.is_main = ParseIntField(parts[6]) != 0;
    if (parts.size() > 7) c.geom = ParseIntField(parts[7]);
    if (parts.size() > 8) c.tex = ParseIntField(parts[8]);
    if (parts.size() > 9) c.acm = ParseIntField(parts[9]);
    if (parts.size() > 10) c.csk = ParseIntField(parts[10]);
    if (parts.size() > 11) c.verts = ParseIntField(parts[11]);
    if (parts.size() > 12) c.awgs = ParseIntField(parts[12]);
    if (c.game == "B3") {
      b3_.push_back(std::move(c));
    } else {
      b1_.push_back(std::move(c));
    }
  }
  loaded_ = true;
  REXLOG_INFO("dbz1: catalog loaded ({} B1, {} B3)", b1_.size(), b3_.size());
  return true;
}

std::string ModPipeline::Output() const {
  std::lock_guard<std::mutex> lock(mutex_);
  return output_;
}

void ModPipeline::AppendOutput(const std::string& text) {
  std::lock_guard<std::mutex> lock(mutex_);
  output_ += text;
}

void ModPipeline::RunAsync(const std::vector<std::string>& args) {
  if (running_.exchange(true)) {
    return;
  }
  {
    std::lock_guard<std::mutex> lock(mutex_);
    output_.clear();
  }
  if (worker_.joinable()) {
    worker_.join();
  }

  // Build the command line. Output is redirected to stderr too so both
  // streams end up in the pipe. The python executable itself is only quoted if
  // it contains spaces (a DBZ1_PYTHON path); a bare "python" must NOT be
  // quoted, because MSVC _popen then fails with ERROR_INVALID_NAME (WinError
  // 123). The script path and each argument ARE quoted so paths containing
  // spaces (e.g. "PROYECTOS IA") survive.
  const std::string py = PythonExecutable();
  std::string cmd = (py.find(' ') != std::string::npos) ? Quote(py) : py;
  cmd += " " + Quote(PipelineScript().string());
  for (const std::string& a : args) {
    cmd += " " + Quote(a);
  }

  // Diagnostic log so a failing pipeline command can be inspected.
  {
    std::ofstream dbg(rex::filesystem::GetExecutableFolder() / "pipeline_cmd.log",
                      std::ios::app);
    dbg << "CMD: " << cmd << "\n";
  }

  // Use CreateProcess instead of _popen: _popen hands the command to
  // "cmd.exe /c", which fails to parse quotes when the command starts with '"'
  // (e.g. "\"python\" ...") with the "volume label syntax" error, and it opens
  // a visible console window. CreateProcess launches python directly (no
  // cmd.exe), with CREATE_NO_WINDOW, redirecting stdout+stderr to a pipe so no
  // CMD window flashes. This is the same fix the sibling B3 project uses.
  worker_ = std::thread([this, cmd]() {
    try {
      HANDLE hOutRead = nullptr, hOutWrite = nullptr;
      SECURITY_ATTRIBUTES sa{};
      sa.nLength = sizeof(sa);
      sa.bInheritHandle = TRUE;
      if (!CreatePipe(&hOutRead, &hOutWrite, &sa, 0)) {
        AppendOutput("ERROR: no se pudo crear el pipe para python.\n");
        running_.store(false);
        return;
      }
      SetHandleInformation(hOutRead, HANDLE_FLAG_INHERIT, 0);

      STARTUPINFOW si{};
      si.cb = sizeof(si);
      si.dwFlags = STARTF_USESTDHANDLES;
      si.hStdOutput = hOutWrite;
      si.hStdError = hOutWrite;
      si.hStdInput = GetStdHandle(STD_INPUT_HANDLE);

      int wlen = MultiByteToWideChar(CP_UTF8, 0, cmd.c_str(), -1, nullptr, 0);
      std::vector<wchar_t> wcmd(wlen);
      MultiByteToWideChar(CP_UTF8, 0, cmd.c_str(), -1, wcmd.data(), wlen);

      PROCESS_INFORMATION pi{};
      const BOOL ok = CreateProcessW(nullptr, wcmd.data(), nullptr, nullptr,
                                     TRUE, CREATE_NO_WINDOW, nullptr, nullptr,
                                     &si, &pi);
      CloseHandle(hOutWrite);
      if (!ok) {
        AppendOutput("ERROR: CreateProcess fallo (WinError " +
                     std::to_string(GetLastError()) + ").\n");
        CloseHandle(hOutRead);
        running_.store(false);
        return;
      }

      char buf[4096];
      DWORD n = 0;
      while (ReadFile(hOutRead, buf, sizeof(buf), &n, nullptr) && n > 0) {
        buf[n] = '\0';
        AppendOutput(std::string(buf, n));
      }
      CloseHandle(hOutRead);

      WaitForSingleObject(pi.hProcess, INFINITE);
      DWORD rc = 0;
      GetExitCodeProcess(pi.hProcess, &rc);
      CloseHandle(pi.hThread);
      CloseHandle(pi.hProcess);
      if (rc != 0) {
        AppendOutput("\n[exit code " + std::to_string(rc) + "]\n");
      }
      running_.store(false);
    } catch (const std::exception& e) {
      REXLOG_ERROR("dbz1: pipeline worker exception: {}", e.what());
      AppendOutput("\n[ERROR interno del pipeline: " + std::string(e.what()) + "]\n");
      running_.store(false);
    } catch (...) {
      REXLOG_ERROR("dbz1: pipeline worker unknown exception");
      AppendOutput("\n[ERROR interno del pipeline: excepción desconocida]\n");
      running_.store(false);
    }
  });
}

void ModPipeline::ScanCharacters() {
  RunAsync(CatalogArgs());
}

void ModPipeline::PortB3ToB1(const ModChar& b3_src, const ModChar& b1_dst) {
  const std::string mod = "port_" + b3_src.label + "_" +
                          std::to_string(b3_src.geom) + "_to_" +
                          std::to_string(b1_dst.geom);
  auto args = PortArgs(b3_src, b1_dst, mod);
  RunAsync(args);
}

void ModPipeline::SwapB1ToB1(const ModChar& b1_src, const ModChar& b1_dst) {
  if (b1_src.geom == 0) {
    AppendOutput("ERROR: el personaje origen no tiene slot geom asignado.\n");
    return;
  }
  const std::string mod = "swap_" + b1_src.label + "_" +
                          std::to_string(b1_src.geom) + "_on_" +
                          std::to_string(b1_dst.geom);
  auto args = SwapArgs(b1_src, b1_dst, mod);
  RunAsync(args);
}

std::vector<std::string> ModPipeline::CatalogArgs() const {
  std::vector<std::string> args = {"catalog"};
  PushOpt(args, "--b1", dbz1::settings::AfsB1Path());
  PushOpt(args, "--b3", dbz1::settings::AfsB3Path());
  return args;
}

std::vector<std::string> ModPipeline::SwapArgs(const ModChar& b1_src,
                                               const ModChar& b1_dst,
                                               const std::string& mod) const {
  // Pass the specific source bin so the right outfit/transform is used
  // (multiple rows share the same label).
  std::vector<std::string> args = {"swap", "--origen",
                                   std::to_string(b1_src.geom),
                                   "--dest", std::to_string(b1_dst.geom),
                                   "--tex", std::to_string(b1_dst.tex),
                                   "--dest-label", b1_dst.label,
                                   "--mod", mod};
  PushOpt(args, "--b1", dbz1::settings::AfsB1Path());
  return args;
}

std::vector<std::string> ModPipeline::PortArgs(const ModChar& b3_src,
                                               const ModChar& b1_dst,
                                               const std::string& mod) const {
  std::vector<std::string> args = {"port", "--b3", b3_src.label,
                                   "--bin", std::to_string(b3_src.geom),
                                   "--dest", std::to_string(b1_dst.geom),
                                   "--tex", std::to_string(b1_dst.tex),
                                   "--dest-label", b1_dst.label,
                                   "--mod", mod};
  PushOpt(args, "--b3-afs", dbz1::settings::AfsB3Path());
  return args;
}

}  // namespace dbz1::launcher
