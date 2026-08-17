// dbz1 - In-game overlay menu implementation (F10).

#include "menu.h"

#include <rex/cvar.h>

// Defined in src/launcher/settings.cpp (same executable).
REXCVAR_DECLARE(bool, dbz1_dev_mode);
REXCVAR_DECLARE(bool, dbz1_diag_logging);
REXCVAR_DECLARE(int32_t, dbz1_resolution_scale);
REXCVAR_DECLARE(bool, dbz1_vsync);
REXCVAR_DECLARE(int32_t, dbz1_frame_cap);

namespace dbz1::ingame {

void InGameMenu::OnDraw(ImGuiIO& io) {
  ImGui::SetNextWindowSize(ImVec2(420, 0), ImGuiCond_FirstUseEver);
  ImGui::SetNextWindowBgAlpha(0.65f);
  if (!ImGui::Begin("dbz1##ingame", nullptr, ImGuiWindowFlags_NoCollapse)) {
    ImGui::End();
    return;
  }

  ImGui::Text("%.1f FPS (%.2f ms/frame)", io.Framerate, 1000.0f / io.Framerate);
  ImGui::Separator();

  bool dev_mode = REXCVAR_GET(dbz1_dev_mode);
  if (ImGui::Checkbox("Dev mode", &dev_mode)) {
    REXCVAR_SET(dbz1_dev_mode, dev_mode);
  }
  ImGui::TextDisabled("Dev mode exposes hot test switches used for debugging.");

  if (dev_mode) {
    DrawDevModeSection();
  }

  ImGui::Separator();
  ImGui::TextDisabled("F10 toggles this overlay. F4 opens advanced settings.");
  ImGui::End();
}

void InGameMenu::DrawDevModeSection() {
  ImGui::Separator();
  ImGui::TextColored(ImVec4(1.0f, 0.7f, 0.1f, 1.0f), "Dev mode");

  bool diag = REXCVAR_GET(dbz1_diag_logging);
  if (ImGui::Checkbox("GPU diagnostic logging (dbz1_gpu_diag.log)", &diag)) {
    REXCVAR_SET(dbz1_diag_logging, diag);
  }
  ImGui::TextDisabled("Per-frame GPU diagnostics. Writes a large log file.");

  // Internal render scale (supersampling of the 720p framebuffer).
  const int scale_options[] = {1, 2, 3, 4};
  const char* scale_labels[] = {"1x (native 720p)", "2x (1440p internal)", "3x (2160p internal)",
                                "4x (4320p internal)"};
  int scale = REXCVAR_GET(dbz1_resolution_scale);
  int scale_idx = scale - 1;
  if (scale_idx < 0) scale_idx = 0;
  if (scale_idx > 3) scale_idx = 3;
  if (ImGui::Combo("Internal resolution scale", &scale_idx, scale_labels, 4)) {
    REXCVAR_SET(dbz1_resolution_scale, scale_options[scale_idx]);
  }
  ImGui::TextDisabled("Supersamples the 720p framebuffer internally. Applies at next boot.");

  bool vsync = REXCVAR_GET(dbz1_vsync);
  if (ImGui::Checkbox("VSync", &vsync)) {
    REXCVAR_SET(dbz1_vsync, vsync);
  }

  int cap = REXCVAR_GET(dbz1_frame_cap);
  if (ImGui::SliderInt("Frame cap", &cap, 0, 240, cap == 0 ? "Uncapped" : "%d FPS")) {
    REXCVAR_SET(dbz1_frame_cap, cap);
  }
}

}  // namespace dbz1::ingame
