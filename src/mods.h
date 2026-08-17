// dbz1 - Mod manager (project-side, no SDK changes).
//
// Manages the "mods" folder next to the executable. A mod is a subfolder that
// replaces game files by providing whole-file copies (e.g. a repacked .afs).
// The launcher lists mods and toggles enable/disable via a ".disabled" marker.
// Whole-file overrides are resolved at open time by the SDK's VFS layer (the
// file is opened from the mod folder, not duplicated into the assets).

#pragma once

#include <filesystem>
#include <string>
#include <vector>

namespace dbz1 {

// Root folder where mods live (next to the executable).
std::filesystem::path ModsRoot();

// One mod as seen by the launcher. `enabled` reflects the effective state
// after normalizing both disable conventions (folder named "foo.disabled" OR
// a ".disabled" marker file inside the folder).
struct ModInfo {
  std::string name;
  bool enabled = true;
  // Optional metadata from a "manifest.txt" inside the mod folder (key=value
  // lines). Empty fields fall back to the folder name / inferred type.
  std::string display_name;
  std::string description;
  std::string author;
  std::string version;
  std::string type;     // e.g. "port_b3", "swap_b1", "audio", "moveset"
  std::string source;   // source character (e.g. "Gero (B3 HD)")
  std::string target;   // target slot (e.g. "Tenshinhan (B1)")
  // Human-readable file count inside the mod (0 when empty).
  int file_count = 0;
};

// List mod folders under the mods root. Enabled mods first, then disabled.
// Folder names ending in ".disabled" are reported with the suffix stripped.
std::vector<ModInfo> ListMods();

// Enable/disable a mod (creates/removes the ".disabled" marker).
void SetModEnabled(const std::string& mod_name, bool enable);

// Reads the raw manifest key for a mod ("" if the key is missing). Keys:
// name, description, author, version, type, source, target.
std::string GetModManifestValue(const std::string& mod_name,
                                const std::string& key);

// Sets a manifest key for a mod, creating/updating manifest.txt in the mod
// folder. Empty value removes the line. Returns false if the mod folder
// cannot be written to.
bool SetModManifestValue(const std::string& mod_name, const std::string& key,
                         const std::string& value);

}  // namespace dbz1
