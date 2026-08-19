// dbz1 - Model pipeline integration (project-side, no SDK changes).
//
// Wraps the validated Python pipelines (mod center hd/launcher_mod_pipeline.py)
// so the launcher can scan the game catalogs and run model ports/swaps from
// the UI. Python is invoked asynchronously; output is captured for display.

#pragma once

#include <atomic>
#include <filesystem>
#include <mutex>
#include <string>
#include <thread>
#include <vector>

namespace dbz1::launcher {

// One character entry from the catalog (characters.cat).
struct ModChar {
  std::string game;    // "B1" or "B3"
  std::string label;   // e.g. "XGOK_BODY"
  std::string name;    // friendly name, e.g. "Goku"
  std::string variant; // outfit/transformation, e.g. "SSJ" ("" for main)
  bool playable = true; // 1/0 in catalog (non-playable = story/cutscene model)
  std::string note;    // e.g. "No jugable (historia)"
  bool is_main = true; // 1 = main row (valid destination), 0 = extra outfit
  int geom = 0;        // slot geom (B1) or AMB bin (B3)
  int tex = 0;         // slot tex
  int acm = 0;         // slot skeleton
  int csk = 0;         // slot animations
  int verts = 0;
  int awgs = 0;

  // Friendly label shown in the UI: "Name (Variant)" or just "Name".
  std::string DisplayName() const {
    if (variant.empty()) return name;
    return name + " (" + variant + ")";
  }
};

class ModPipeline {
 public:
  ModPipeline() = default;
  ~ModPipeline();

  // Joins the worker thread if one is running. Safe to call multiple times.
  // MUST be called before the owner is destroyed: a joinable std::thread
  // destroyed would call std::terminate (this crashed the launcher on Play
  // whenever a pipeline op had been started and the self-deleting dialog was
  // torn down).
  void Shutdown();

  // Reads the cached catalog from disk. Returns false if missing.
  bool LoadCatalog();

  const std::vector<ModChar>& B1() const { return b1_; }
  const std::vector<ModChar>& B3() const { return b3_; }
  bool CatalogLoaded() const { return loaded_; }

  // Asynchronous operations. Poll IsRunning() to know when done; read the
  // output via Output().
  void ScanCharacters();
  void PortB3ToB1(const ModChar& b3_src, const ModChar& b1_dst);
  void SwapB1ToB1(const ModChar& b1_src, const ModChar& b1_dst);

  bool IsRunning() const { return running_.load(); }
  // Full accumulated output of the last/current run.
  std::string Output() const;

 private:
  void RunAsync(const std::vector<std::string>& args);
  void AppendOutput(const std::string& text);
  // Builds the argument list for each command, injecting the configured
  // source-archive paths (empty strings are omitted so the Python side uses
  // its own defaults).
  std::vector<std::string> CatalogArgs() const;
  std::vector<std::string> SwapArgs(const ModChar& b1_src,
                                    const ModChar& b1_dst,
                                    const std::string& mod) const;
  std::vector<std::string> PortArgs(const ModChar& b3_src,
                                    const ModChar& b1_dst,
                                    const std::string& mod) const;

  std::vector<ModChar> b1_;
  std::vector<ModChar> b3_;
  bool loaded_ = false;
  std::atomic<bool> running_{false};
  mutable std::mutex mutex_;
  std::string output_;
  std::thread worker_;
};

}  // namespace dbz1::launcher
