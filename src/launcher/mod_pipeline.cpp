// dbz1 - Model pipeline integration (project-side).

#include "mod_pipeline.h"

#include <rex/filesystem.h>
#include <rex/logging.h>

#include "settings.h"

#include <cstdio>
#include <fstream>
#include <sstream>

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
  // streams end up in the pipe.
  std::string cmd = Quote(PythonExecutable()) + " " + Quote(PipelineScript().string());
  for (const std::string& a : args) {
    cmd += " " + a;
  }
  cmd += " 2>&1";

  worker_ = std::thread([this, cmd]() {
    FILE* pipe = _popen(cmd.c_str(), "r");
    if (!pipe) {
      AppendOutput("ERROR: no se pudo lanzar python.\n");
      running_.store(false);
      return;
    }
    char buf[512];
    size_t n;
    while ((n = fread(buf, 1, sizeof(buf) - 1, pipe)) > 0) {
      buf[n] = '\0';
      AppendOutput(std::string(buf, n));
    }
    const int rc = _pclose(pipe);
    if (rc != 0) {
      AppendOutput("\n[exit code " + std::to_string(rc) + "]\n");
    }
    running_.store(false);
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
                                   "--mod", mod};
  PushOpt(args, "--b3-afs", dbz1::settings::AfsB3Path());
  return args;
}

}  // namespace dbz1::launcher
