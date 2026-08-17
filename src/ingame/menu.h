// dbz1 - In-game overlay menu (F10) with Dev mode toggles.
//
// Shows a compact overlay while the game runs: FPS, frame time, and (when dev
// mode is enabled) hot switches for diagnostics and testing. All toggles are
// applied immediately while the game keeps running.

#pragma once

#include <imgui.h>

#include <rex/ui/imgui_dialog.h>

namespace dbz1::ingame {

// Overlay shown with F10 while in-game.
class InGameMenu : public rex::ui::ImGuiDialog {
 public:
  InGameMenu(rex::ui::ImGuiDrawer* drawer) : ImGuiDialog(drawer) {}

 protected:
  void OnDraw(ImGuiIO& io) override;

 private:
  void DrawDevModeSection();
};

}  // namespace dbz1::ingame
