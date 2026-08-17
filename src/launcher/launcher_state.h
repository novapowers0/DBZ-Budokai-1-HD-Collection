// dbz1 - Pre-game launcher screen (ImGui dialog).
//
// Shows a friendly settings screen before the game boots. Pressing "Play"
// dismisses the dialog and triggers the module launch. Also owns the toggle
// that decides whether to skip the launcher entirely on the next run.

#pragma once

#include <functional>

#include <imgui.h>

#include <rex/ui/imgui_dialog.h>

#include "mod_pipeline.h"

namespace dbz1::launcher {

// Dialog shown before the game starts. On "Play", invokes on_play and closes
// itself.
class LauncherDialog : public rex::ui::ImGuiDialog {
 public:
  LauncherDialog(rex::ui::ImGuiDrawer* drawer, std::function<void()> on_play);

 protected:
  void OnDraw(ImGuiIO& io) override;

 private:
  void DrawVideoTab();
  void DrawAudioTab();
  void DrawInputTab();
  void DrawDevTab();
  void DrawModsTab();
  void DrawModPipelineTab();

  std::function<void()> on_play_;
  int active_tab_ = 0;
  ModPipeline mod_pipeline_;
  // Selected indices into the pipeline catalogs (-1 = none).
  int pipeline_b3_idx_ = -1;
  int pipeline_b1_dst_idx_ = -1;
  int pipeline_b1_src_idx_ = -1;
  bool catalog_load_attempted_ = false;
  bool scan_was_running_ = false;
  char output_buf_[8192] = {};
  // Mod manifest editing state.
  bool editing_mod_ = false;
  std::string edit_mod_name_;
  char edit_desc_buf_[2048] = {};
  char edit_author_buf_[256] = {};
  char edit_version_buf_[128] = {};
  bool pending_manifest_reload_ = false;
  // AFS source-archive path buffers (pipeline). Mirrors the persisted cvars.
  char afs_b1_buf_[512] = {};
  char afs_b3_buf_[512] = {};
  bool afs_bufs_synced_ = false;
  // Pending SDL file-dialog target: 1 = B1, 2 = B3.
  int afs_dialog_target_ = 0;

  // SDL file-dialog callback (launcher owns the userdata).
  static void AfsDialogCallback(void* userdata, const char* const* filelist,
                                int filter);
};

}  // namespace dbz1::launcher
