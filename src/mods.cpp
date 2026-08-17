// dbz1 - Mod manager (project-side, no SDK changes).

#include "mods.h"

#include <rex/filesystem.h>
#include <rex/logging.h>

#include <algorithm>
#include <fstream>
#include <system_error>

namespace dbz1 {

std::filesystem::path ModsRoot() {
  // Mods live next to the project assets (project_root/mods), NOT next to the
  // executable: the build output dir is wiped on each clean recompile. Derive
  // the project root by walking up from the exe until an "assets" folder is
  // found (same heuristic as OnConfigurePaths).
  auto exe_dir = rex::filesystem::GetExecutableFolder();
  std::filesystem::path probe = exe_dir;
  for (int depth = 0; depth < 6; ++depth) {
    if (std::filesystem::is_directory(probe / "assets")) {
      return probe / "mods";
    }
    probe = probe.parent_path();
  }
  // Fallback: alongside the executable.
  return exe_dir / "mods";
}

namespace {

// A mod can be disabled in two equivalent ways:
//   1. Its folder name ends with ".disabled"  (e.g. "foo.disabled")
//   2. It contains a ".disabled" marker file   (mods/foo/.disabled)
// Normalize both so the launcher shows the real folder name once, with the
// correct enabled state.
bool EndsWithDotDisabled(const std::string& name) {
  const std::string suffix = ".disabled";
  return name.size() >= suffix.size() &&
         name.compare(name.size() - suffix.size(), suffix.size(), suffix) == 0;
}

std::string StripDotDisabled(const std::string& name) {
  return EndsWithDotDisabled(name)
             ? name.substr(0, name.size() - std::string(".disabled").size())
             : name;
}

bool FolderHasDisabledMarker(const std::filesystem::path& dir) {
  return std::filesystem::exists(dir / ".disabled");
}

bool FolderIsDisabled(const std::filesystem::path& dir,
                      const std::string& name) {
  return EndsWithDotDisabled(name) || FolderHasDisabledMarker(dir);
}

// Reads a simple "key=value" manifest (one per line, '#' = comment) from a
// folder, optionally falling back to "manifest.txt". Unknown keys are ignored.
void LoadManifest(const std::filesystem::path& dir, ModInfo& info) {
  std::ifstream in(dir / "manifest.txt");
  if (!in.is_open()) {
    return;
  }
  std::string line;
  while (std::getline(in, line)) {
    // Trim trailing CR and whitespace.
    while (!line.empty() && (line.back() == '\r' || line.back() == ' ' ||
                             line.back() == '\t')) {
      line.pop_back();
    }
    if (line.empty() || line[0] == '#') {
      continue;
    }
    const size_t eq = line.find('=');
    if (eq == std::string::npos) {
      continue;
    }
    std::string key = line.substr(0, eq);
    std::string value = line.substr(eq + 1);
    // Trim leading whitespace of key/value.
    auto trim = [](std::string& s) {
      size_t b = 0;
      while (b < s.size() && (s[b] == ' ' || s[b] == '\t')) ++b;
      s.erase(0, b);
    };
    trim(key);
    trim(value);
    if (key == "name") info.display_name = value;
    else if (key == "description") info.description = value;
    else if (key == "author") info.author = value;
    else if (key == "version") info.version = value;
    else if (key == "type") info.type = value;
    else if (key == "source") info.source = value;
    else if (key == "target") info.target = value;
  }
}


// Infers a mod's type from its folder layout when no manifest is present, and
// counts the files it overrides. Types:
//   port_b3  -> any data_*.afs contains both 2450 (geom) and 2451 (tex)
//   swap_b1  -> any data_*.afs contains 2450 but no 2451 (uses the slot's own tex)
//   moveset  -> any data_*.afs contains 2445/2448 (skeleton/animation)
//   audio    -> any adx_*.afs override (music/voices: adx_us.afs, adx_jp.afs,
//              adx_usa.afs, adx_jpn.afs, ...)
//   data     -> anything else
void InferTypeAndCount(const std::filesystem::path& dir, ModInfo& info) {
  bool has_data = false, has_2450 = false, has_2451 = false,
       has_anim = false, has_audio = false;
  int count = 0;
  std::error_code ec;
  for (const auto& entry :
       std::filesystem::recursive_directory_iterator(dir, ec)) {
    if (!entry.is_regular_file()) {
      continue;
    }
    const std::string rel =
        rex::path_to_utf8(entry.path().lexically_relative(dir));
    ++count;
    // Audio: any adx_*.afs (US layout: adx_us.afs; JP: adx_jp.afs; custom
    // packs may use adx_usa.afs / adx_jpn.afs). Also catch entry-level
    // overrides inside an adx_*.afs folder.
    if (rel.find("adx_") != std::string::npos &&
        (rel.find(".afs") != std::string::npos ||
         rel.find(".adx") != std::string::npos)) {
      has_audio = true;
    }
    // Character data lives in ANY data_*.afs (data_sp/us/fr/en/ge/it share
    // the same bin numbering). Match the data_ prefix.
    const size_t data_pos = rel.find("data_");
    const bool is_data_afs =
        data_pos != std::string::npos &&
        rel.find(".afs", data_pos) != std::string::npos;
    if (is_data_afs) {
      has_data = true;
      const size_t afs_pos = rel.find(".afs", data_pos);
      const std::string after = rel.substr(afs_pos + 4);
      // Path is .../data_XX.afs/<entry_index>/...
      const size_t slash = after.find_first_of("/\\");
      std::string idx =
          slash == std::string::npos ? after : after.substr(0, slash);
      if (idx == "2450") has_2450 = true;
      if (idx == "2451") has_2451 = true;
      if (idx == "2445" || idx == "2448") has_anim = true;
    }
  }
  info.file_count = count;
  if (info.type.empty()) {
    if (has_audio) info.type = "audio";
    else if (has_data && has_2450 && has_2451) info.type = "port_b3";
    else if (has_data && has_2450) info.type = "swap_b1";
    else if (has_data && has_anim) info.type = "moveset";
    else if (has_data) info.type = "data";
    else info.type = "other";
  }
}

}  // namespace

std::vector<ModInfo> ListMods() {
  std::vector<ModInfo> result;
  std::error_code ec;
  const std::filesystem::path mods_root = ModsRoot();
  if (!std::filesystem::is_directory(mods_root, ec)) {
    return {};
  }
  for (const auto& mod_entry : std::filesystem::directory_iterator(mods_root, ec)) {
    if (!mod_entry.is_directory()) {
      continue;
    }
    const std::string raw_name = rex::path_to_utf8(mod_entry.path().filename());
    // Skip duplicates: if both "foo" and "foo.disabled" exist, prefer the
    // non-suffixed entry (the launcher only ever creates the marker-file form).
    if (EndsWithDotDisabled(raw_name) &&
        std::filesystem::exists(mods_root / StripDotDisabled(raw_name))) {
      continue;
    }
    ModInfo info;
    info.name = StripDotDisabled(raw_name);
    info.enabled = !FolderIsDisabled(mod_entry.path(), raw_name);
    LoadManifest(mod_entry.path(), info);
    InferTypeAndCount(mod_entry.path(), info);
    result.push_back(std::move(info));
  }
  // Enabled first, then disabled (each group alphabetical).
  std::stable_sort(result.begin(), result.end(),
                   [](const ModInfo& a, const ModInfo& b) {
                     if (a.enabled != b.enabled) {
                       return a.enabled;
                     }
                     return a.name < b.name;
                   });
  return result;
}

void SetModEnabled(const std::string& mod_name, bool enable) {
  const std::filesystem::path mods_root = ModsRoot();
  const std::filesystem::path mod_dir = mods_root / mod_name;
  const std::filesystem::path marker = mod_dir / ".disabled";
  std::error_code ec;
  if (enable) {
    std::filesystem::remove(marker, ec);
    // Also restore a folder that had been renamed "foo.disabled".
    const std::filesystem::path suffixed = mods_root / (mod_name + ".disabled");
    if (!std::filesystem::exists(mod_dir) &&
        std::filesystem::exists(suffixed)) {
      std::filesystem::rename(suffixed, mod_dir, ec);
    }
  } else {
    std::filesystem::create_directories(mod_dir, ec);
    std::ofstream marker_file(marker);
    marker_file << "disabled\n";
  }
  REXLOG_INFO("dbz1: mod '{}' {}", mod_name, enable ? "enabled" : "disabled");
}

namespace {

std::filesystem::path ModDir(const std::string& mod_name) {
  return ModsRoot() / StripDotDisabled(mod_name);
}

std::string ReadManifestValue(const std::filesystem::path& manifest,
                              const std::string& key) {
  std::ifstream in(manifest);
  if (!in.is_open()) {
    return "";
  }
  std::string line;
  while (std::getline(in, line)) {
    while (!line.empty() && (line.back() == '\r' || line.back() == ' ' ||
                             line.back() == '\t')) {
      line.pop_back();
    }
    const size_t eq = line.find('=');
    if (eq == std::string::npos) {
      continue;
    }
    std::string k = line.substr(0, eq);
    auto trim = [](std::string& s) {
      size_t b = 0;
      while (b < s.size() && (s[b] == ' ' || s[b] == '\t')) ++b;
      s.erase(0, b);
    };
    trim(k);
    if (k == key) {
      std::string v = line.substr(eq + 1);
      trim(v);
      return v;
    }
  }
  return "";
}

}  // namespace

std::string GetModManifestValue(const std::string& mod_name,
                                const std::string& key) {
  return ReadManifestValue(ModDir(mod_name) / "manifest.txt", key);
}

bool SetModManifestValue(const std::string& mod_name, const std::string& key,
                         const std::string& value) {
  const std::filesystem::path dir = ModDir(mod_name);
  const std::filesystem::path manifest = dir / "manifest.txt";
  std::error_code ec;
  std::filesystem::create_directories(dir, ec);

  // Read all existing lines, dropping the target key.
  std::vector<std::string> keep;
  if (std::filesystem::exists(manifest, ec)) {
    std::ifstream in(manifest);
    std::string line;
    while (std::getline(in, line)) {
      while (!line.empty() && (line.back() == '\r' || line.back() == ' ' ||
                               line.back() == '\t')) {
        line.pop_back();
      }
      const size_t eq = line.find('=');
      bool drop = false;
      if (eq != std::string::npos) {
        std::string k = line.substr(0, eq);
        auto trim = [](std::string& s) {
          size_t b = 0;
          while (b < s.size() && (s[b] == ' ' || s[b] == '\t')) ++b;
          s.erase(0, b);
        };
        trim(k);
        drop = (k == key);
      }
      if (!drop) keep.push_back(line);
    }
  }
  if (!value.empty()) {
    keep.push_back(key + "=" + value);
  }
  std::ofstream out(manifest);
  if (!out.is_open()) {
    REXLOG_WARN("dbz1: no se pudo escribir manifest de '{}'", mod_name);
    return false;
  }
  for (const auto& line : keep) {
    out << line << "\n";
  }
  REXLOG_INFO("dbz1: manifest '{}' key '{}' actualizada", mod_name, key);
  return true;
}

}  // namespace dbz1
