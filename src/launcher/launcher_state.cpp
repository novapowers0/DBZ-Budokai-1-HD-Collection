// dbz1 - Pre-game launcher screen implementation.

#include "launcher_state.h"

#include <rex/cvar.h>
#include <rex/logging.h>

#include <SDL3/SDL.h>

#include <windows.h>
#include <commdlg.h>

#include <algorithm>
#include <cstring>
#include <filesystem>
#include <string>
#include <vector>

#include "mods.h"
#include "settings.h"
#include "mod_pipeline.h"

// SDK cvars that the friendly UI drives.
REXCVAR_DECLARE(bool, fullscreen);
REXCVAR_DECLARE(bool, vsync);
REXCVAR_DECLARE(std::string, present_effect);

// Defined in src/launcher/settings.cpp (same executable).
REXCVAR_DECLARE(std::string, dbz1_fullscreen_mode);
REXCVAR_DECLARE(bool, dbz1_vsync);
REXCVAR_DECLARE(int32_t, dbz1_anisotropic);
REXCVAR_DECLARE(bool, dbz1_msaa_2x);
REXCVAR_DECLARE(int32_t, dbz1_swap_effect);
REXCVAR_DECLARE(std::string, dbz1_gpu_backend);
REXCVAR_DECLARE(std::string, dbz1_present_effect);
REXCVAR_DECLARE(std::string, dbz1_fsr_quality);
REXCVAR_DECLARE(int32_t, dbz1_frame_cap);
REXCVAR_DECLARE(std::string, dbz1_user_region);
REXCVAR_DECLARE(int32_t, dbz1_language);
REXCVAR_DECLARE(double, dbz1_gamma);
REXCVAR_DECLARE(double, dbz1_master_volume);
REXCVAR_DECLARE(double, dbz1_music_volume);
REXCVAR_DECLARE(double, dbz1_sfx_volume);
REXCVAR_DECLARE(double, dbz1_voice_volume);
REXCVAR_DECLARE(std::string, dbz1_audio_device);
REXCVAR_DECLARE(bool, dbz1_user_audio_jp);
REXCVAR_DECLARE(double, dbz1_deadzone);
REXCVAR_DECLARE(bool, dbz1_rumble);
REXCVAR_DECLARE(bool, dbz1_mnk_mode);
REXCVAR_DECLARE(bool, dbz1_dev_mode);
REXCVAR_DECLARE(bool, dbz1_diag_logging);

// MnK keybinds (defined in rexinput -> rexruntime.dll, shared storage).
REXCVAR_DECLARE(std::string, keybind_a);
REXCVAR_DECLARE(std::string, keybind_b);
REXCVAR_DECLARE(std::string, keybind_x);
REXCVAR_DECLARE(std::string, keybind_y);
REXCVAR_DECLARE(std::string, keybind_left_trigger);
REXCVAR_DECLARE(std::string, keybind_right_trigger);
REXCVAR_DECLARE(std::string, keybind_left_shoulder);
REXCVAR_DECLARE(std::string, keybind_right_shoulder);
REXCVAR_DECLARE(std::string, keybind_lstick_up);
REXCVAR_DECLARE(std::string, keybind_lstick_down);
REXCVAR_DECLARE(std::string, keybind_lstick_left);
REXCVAR_DECLARE(std::string, keybind_lstick_right);
REXCVAR_DECLARE(std::string, keybind_lstick_press);
REXCVAR_DECLARE(std::string, keybind_rstick_press);
REXCVAR_DECLARE(std::string, keybind_dpad_up);
REXCVAR_DECLARE(std::string, keybind_dpad_down);
REXCVAR_DECLARE(std::string, keybind_dpad_left);
REXCVAR_DECLARE(std::string, keybind_dpad_right);
REXCVAR_DECLARE(std::string, keybind_back);
REXCVAR_DECLARE(std::string, keybind_start);
REXCVAR_DECLARE(std::string, keybind_guide);

// Persisted wrappers defined in src/launcher/settings.cpp.
REXCVAR_DECLARE(std::string, dbz1_keybind_a);
REXCVAR_DECLARE(std::string, dbz1_keybind_b);
REXCVAR_DECLARE(std::string, dbz1_keybind_x);
REXCVAR_DECLARE(std::string, dbz1_keybind_y);
REXCVAR_DECLARE(std::string, dbz1_keybind_left_trigger);
REXCVAR_DECLARE(std::string, dbz1_keybind_right_trigger);
REXCVAR_DECLARE(std::string, dbz1_keybind_left_shoulder);
REXCVAR_DECLARE(std::string, dbz1_keybind_right_shoulder);
REXCVAR_DECLARE(std::string, dbz1_keybind_lstick_up);
REXCVAR_DECLARE(std::string, dbz1_keybind_lstick_down);
REXCVAR_DECLARE(std::string, dbz1_keybind_lstick_left);
REXCVAR_DECLARE(std::string, dbz1_keybind_lstick_right);
REXCVAR_DECLARE(std::string, dbz1_keybind_lstick_press);
REXCVAR_DECLARE(std::string, dbz1_keybind_rstick_press);
REXCVAR_DECLARE(std::string, dbz1_keybind_dpad_up);
REXCVAR_DECLARE(std::string, dbz1_keybind_dpad_down);
REXCVAR_DECLARE(std::string, dbz1_keybind_dpad_left);
REXCVAR_DECLARE(std::string, dbz1_keybind_dpad_right);
REXCVAR_DECLARE(std::string, dbz1_keybind_back);
REXCVAR_DECLARE(std::string, dbz1_keybind_start);

namespace {

// Playback device names as reported by SDL3. Cached across frames (the list
// only changes when devices are plugged/unplugged) and refreshed on demand via
// the "Refresh" button.
std::vector<std::string> g_audio_playback_devices;
bool g_audio_devices_enumerated = false;

void RefreshAudioPlaybackDevices() {
  g_audio_playback_devices.clear();
  // Audio device enumeration needs the audio subsystem initialized. This is
  // refcounted by SDL; the runtime re-initializes it (and eventually shuts it
  // down) on its own, so calling it here for enumeration is safe.
  SDL_InitSubSystem(SDL_INIT_AUDIO);
  int count = 0;
  SDL_AudioDeviceID* devices = SDL_GetAudioPlaybackDevices(&count);
  if (devices) {
    for (int i = 0; i < count; ++i) {
      const char* name = SDL_GetAudioDeviceName(devices[i]);
      if (name) {
        g_audio_playback_devices.emplace_back(name);
      }
    }
    SDL_free(devices);
  }
  g_audio_devices_enumerated = true;
}

// Edits a MnK keybind cvar with an ImGui text input. The cvar holds a
// VirtualKey name (e.g. "Space", "W"); empty means unbound.
void DrawKeybind(const char* label, std::string& cvar_value) {
  char buf[64] = {};
  std::memcpy(buf, cvar_value.c_str(),
              std::min(cvar_value.size(), sizeof(buf) - 1));
  if (ImGui::InputText(label, buf, sizeof(buf))) {
    cvar_value = buf;
  }
}

// Shows a native Windows "open file" dialog (GetOpenFileNameW) and returns the
// selected path, or an empty string if cancelled. Runs synchronously on the UI
// thread. The bundled SDL3 is built with the dummy dialog driver, so
// SDL_ShowOpenFileDialog never shows a real dialog — this native path is
// reliable on Windows.
std::string ShowNativeOpenFileDialog(const char* filter_label,
                                     const char* filter_spec) {
  OPENFILENAMEW ofn{};
  wchar_t file[MAX_PATH] = L"";
  ofn.lStructSize = sizeof(ofn);
  ofn.hwndOwner = nullptr;
  ofn.lpstrFilter = L"AFS archives (*.afs)\0*.afs\0All files (*.*)\0*.*\0";
  ofn.lpstrFile = file;
  ofn.nMaxFile = MAX_PATH;
  ofn.Flags = OFN_FILEMUSTEXIST | OFN_HIDEREADONLY | OFN_NOCHANGEDIR;
  ofn.lpstrDefExt = L"afs";
  (void)filter_label;
  (void)filter_spec;
  if (GetOpenFileNameW(&ofn)) {
    int len = WideCharToMultiByte(CP_UTF8, 0, ofn.lpstrFile, -1, nullptr, 0,
                                  nullptr, nullptr);
    if (len > 1) {
      std::string path(len - 1, '\0');
      WideCharToMultiByte(CP_UTF8, 0, ofn.lpstrFile, -1, &path[0], len,
                          nullptr, nullptr);
      return path;
    }
  }
  return std::string();
}

}  // namespace

namespace dbz1::launcher {

LauncherDialog::LauncherDialog(rex::ui::ImGuiDrawer* drawer, std::function<void()> on_play)
    : ImGuiDialog(drawer), on_play_(std::move(on_play)) {}

void LauncherDialog::ShutdownPipeline() {
  mod_pipeline_.Shutdown();
}

void LauncherDialog::OnDraw(ImGuiIO& io) {
  // Center the launcher panel on the actual window and keep it within bounds,
  // so a window larger than 1280x720 (or a smaller one) never leaves the
  // controls stranded in a corner or off-screen.
  const float panel_w = std::min(1280.0f, io.DisplaySize.x);
  const float panel_h = std::min(720.0f, io.DisplaySize.y);
  ImGui::SetNextWindowSize(ImVec2(panel_w, panel_h), ImGuiCond_Always);
  ImGui::SetNextWindowPos(
      ImVec2((io.DisplaySize.x - panel_w) * 0.5f, (io.DisplaySize.y - panel_h) * 0.5f),
      ImGuiCond_Always);

  ImGui::Begin("DBZ Budokai HD Collection##launcher", nullptr,
               ImGuiWindowFlags_NoCollapse | ImGuiWindowFlags_NoMove |
                   ImGuiWindowFlags_NoResize | ImGuiWindowFlags_NoTitleBar);

  ImGui::TextColored(ImVec4(1.0f, 0.7f, 0.1f, 1.0f), "DBZ Budokai HD Collection");
  ImGui::TextDisabled("Recompiled with ReXGlue - Launcher");
  ImGui::Separator();

  const char* tabs[] = {"Video", "Audio", "Input", "Mods", "Dev"};
  ImGuiTabBarFlags flags = 0;
  if (ImGui::BeginTabBar("##launcher_tabs", flags)) {
    if (ImGui::BeginTabItem("Video")) {
      DrawVideoTab();
      ImGui::EndTabItem();
    }
    if (ImGui::BeginTabItem("Audio")) {
      DrawAudioTab();
      ImGui::EndTabItem();
    }
    if (ImGui::BeginTabItem("Input")) {
      DrawInputTab();
      ImGui::EndTabItem();
    }
    if (ImGui::BeginTabItem("Mods")) {
      DrawModsTab();
      ImGui::EndTabItem();
    }
    if (ImGui::BeginTabItem("Dev")) {
      DrawDevTab();
      ImGui::EndTabItem();
    }
    ImGui::EndTabBar();
  }

  ImGui::Separator();
  if (ImGui::Button("Save settings", ImVec2(180, 0))) {
    dbz1::settings::SaveUserSettings();
  }
  ImGui::SameLine();
  if (ImGui::Button("Play", ImVec2(240, 0)) || ImGui::IsKeyPressed(ImGuiKey_Enter, false)) {
    dbz1::settings::SaveUserSettings();
    dbz1::settings::ApplyUserSettingsToSdk();
    REXLOG_INFO("dbz1: launcher Play pressed, starting game");
    Close();
    if (on_play_) {
      on_play_();
    }
  }

  ImGui::End();
}

void LauncherDialog::DrawVideoTab() {
  ImGui::BeginChild("##video_settings", ImVec2(0, -40), true);

  // Game region: selects which assets folder (us or eu) game:\us resolves to.
  const char* region_options[] = {"USA", "EU (PAL)"};
  std::string region = REXCVAR_GET(dbz1_user_region);
  int region_idx = (region == "eu") ? 1 : 0;
  if (ImGui::Combo("Region", &region_idx, region_options, 2)) {
    REXCVAR_SET(dbz1_user_region, region_idx == 0 ? std::string("us") : std::string("eu"));
  }
  ImGui::TextDisabled("Selects the game assets (audio/text) for the region. Restart required.");

  // Language: English/French/Spanish/German/Italian. Uses data_XX.afs where
  // XX depends on the region: US layout uses _us/_fr/_sp, EUR layout uses
  // _eng/_fra/_spn/_ger/_ita.
  const int lang_ids[] = {1, 4, 5, 3, 6};
  const char* lang_labels[] = {"English", "Français", "Español", "Deutsch", "Italiano"};
  int lang_id = REXCVAR_GET(dbz1_language);
  int lang_idx = 0;
  for (int i = 0; i < 5; i++) {
    if (lang_ids[i] == lang_id) {
      lang_idx = i;
      break;
    }
  }
  if (ImGui::Combo("Language", &lang_idx, lang_labels, 5)) {
    REXCVAR_SET(dbz1_language, lang_ids[lang_idx]);
  }
  ImGui::TextDisabled("Selects the game's text/voice pack. Restart required.");

  // Internal render scale (supersampling of the 720p framebuffer).
  const int scale_options[] = {1, 2, 3, 4};
  const char* scale_labels[] = {"1x (native 720p)", "2x (1440p internal)", "3x (2160p internal)",
                                "4x (4320p internal)"};
  int scale = dbz1::settings::ResolutionScale();
  int scale_idx = scale - 1;
  if (scale_idx < 0) scale_idx = 0;
  if (scale_idx > 3) scale_idx = 3;
  if (ImGui::Combo("Internal resolution scale", &scale_idx, scale_labels, 4)) {
    dbz1::settings::SetResolutionScale(scale_options[scale_idx]);
  }
  ImGui::TextDisabled("Supersamples the 720p framebuffer internally (sharper image, higher GPU "
                      "cost). Restart required.");

  // Game refresh rate is fixed at 60 Hz (the game paces its logic by the guest
  // vblank count, so higher rates make it run too fast).
  ImGui::Text("Game refresh rate: 60 Hz (original)");
  ImGui::TextDisabled("Locked to 60 Hz. This game ties its logic to the vblank count, so "
                      "higher rates would speed the game up.");

  // Fullscreen mode. The SDK presents through a flip-model swap chain in
  // borderless fullscreen only; exclusive fullscreen is not supported, so
  // only Windowed and Borderless are offered (a legacy "exclusive" value in
  // the config file is treated as borderless).
  const char* modes[] = {"Windowed", "Borderless"};
  int mode_idx = 0;
  std::string mode = REXCVAR_GET(dbz1_fullscreen_mode);
  if (mode == "borderless" || mode == "exclusive")
    mode_idx = 1;
  if (ImGui::Combo("Fullscreen mode", &mode_idx, modes, 2)) {
    const char* v = mode_idx == 0 ? "windowed" : "borderless";
    rex::cvar::SetFlagByName("dbz1_fullscreen_mode", v);
  }
  ImGui::TextDisabled("Borderless fullscreen. Exclusive fullscreen is not supported by the renderer.");

  // VSync.
  bool vsync_val = REXCVAR_GET(dbz1_vsync);
  if (ImGui::Checkbox("VSync", &vsync_val)) {
    REXCVAR_SET(dbz1_vsync, vsync_val);
  }

  // Anisotropic filtering. The cvar stores -1..5 (Auto/Off/1x/2x/4x/8x/16x);
  // the combo index is cvar + 1.
  const char* aniso_options[] = {"Auto", "Off", "1x", "2x", "4x", "8x", "16x"};
  int aniso_idx = REXCVAR_GET(dbz1_anisotropic) + 1;
  if (aniso_idx < 0 || aniso_idx > 6) {
    aniso_idx = 0;
  }
  if (ImGui::Combo("Anisotropic filtering", &aniso_idx, aniso_options, 7)) {
    REXCVAR_SET(dbz1_anisotropic, aniso_idx - 1);
  }

  // Gamma correction (applied on top of the game's own gamma ramp).
  float gamma_val = static_cast<float>(REXCVAR_GET(dbz1_gamma));
  if (ImGui::SliderFloat("Gamma", &gamma_val, 0.5f, 2.0f, "%.2f")) {
    REXCVAR_SET(dbz1_gamma, static_cast<double>(gamma_val));
  }
  ImGui::TextDisabled("Brightness correction: lower = brighter, higher = darker.");

  // MSAA 2x toggle (the SDK only supports native 2x; 4x/8x are not available).
  bool msaa_2x = REXCVAR_GET(dbz1_msaa_2x);
  if (ImGui::Checkbox("MSAA 2x", &msaa_2x)) {
    REXCVAR_SET(dbz1_msaa_2x, msaa_2x);
  }
  ImGui::TextDisabled("Native 2x multisampling (4x/8x are not supported by the renderer).");

  // Swap post effect (FXAA). Applied to the final swap image at present time;
  // requires a restart of the game.
  const char* fxaa_options[] = {"None", "FXAA", "FXAA Extreme"};
  int fxaa = REXCVAR_GET(dbz1_swap_effect);
  if (fxaa < 0 || fxaa > 2) {
    fxaa = 0;
  }
  if (ImGui::Combo("Anti-aliasing (post)", &fxaa, fxaa_options, 3)) {
    REXCVAR_SET(dbz1_swap_effect, fxaa);
  }
  ImGui::TextDisabled("Fullscreen post anti-aliasing (FXAA). Requires game restart.");

  // Graphics backend. The SDK build ships both D3D12 and Vulkan; D3D12 is the
  // default and hosts the FidelityFX temporal upscaler (FSR2/FSR3) in this
  // build, while Vulkan is available for validation/portability.
  const char* backend_options[] = {"Auto (D3D12)", "D3D12", "Vulkan"};
  const char* backend_values[] = {"auto", "d3d12", "vulkan"};
  std::string backend = REXCVAR_GET(dbz1_gpu_backend);
  int backend_idx = 0;
  for (int i = 0; i < 3; i++) {
    if (backend == backend_values[i]) {
      backend_idx = i;
      break;
    }
  }
  if (ImGui::Combo("Graphics backend", &backend_idx, backend_options, 3)) {
    REXCVAR_SET(dbz1_gpu_backend, std::string(backend_values[backend_idx]));
  }
  ImGui::TextDisabled("D3D12 (default) or Vulkan graphics backend. Restart required.");

  // Present upscaler (FidelityFX). Applied to the final swap image at present
  // time; requires a game restart.
  const char* effect_options[] = {"Bilinear", "CAS (sharpening)", "FSR 1", "FSR 2",
                                  "FSR 3"};
  const char* effect_values[] = {"bilinear", "cas", "fsr", "fsr2", "fsr3"};
  std::string effect = REXCVAR_GET(dbz1_present_effect);
  int effect_idx = 0;
  for (int i = 0; i < 5; i++) {
    if (effect == effect_values[i]) {
      effect_idx = i;
      break;
    }
  }
  if (ImGui::Combo("Upscaler", &effect_idx, effect_options, 5)) {
    REXCVAR_SET(dbz1_present_effect, std::string(effect_values[effect_idx]));
  }
  ImGui::TextDisabled("Fullscreen upscaling. FSR 2/3 (temporal) need the FidelityFX runtime "
                      "on the D3D12 backend. Restart required.");

  // FSR quality mode, only meaningful for the temporal/resolution FSR modes.
  if (effect_idx >= 2) {
    const char* quality_options[] = {"Auto", "Native AA", "Quality", "Balanced", "Performance",
                                     "Ultra performance"};
    const char* quality_values[] = {"auto", "nativeaa", "quality", "balanced", "performance",
                                    "ultra_performance"};
    std::string quality = REXCVAR_GET(dbz1_fsr_quality);
    int quality_idx = 0;
    for (int i = 0; i < 6; i++) {
      if (quality == quality_values[i]) {
        quality_idx = i;
        break;
      }
    }
    if (ImGui::Combo("FSR quality", &quality_idx, quality_options, 6)) {
      REXCVAR_SET(dbz1_fsr_quality, std::string(quality_values[quality_idx]));
    }
    ImGui::TextDisabled("Target resolution for the FSR upscaler. Restart required.");
  }

  // Frame cap. Caps the host present rate only (drop-oldest on the display
  // side); the guest vblank pacing and thus the game speed are never affected.
  const int cap_options[] = {0, 60, 75, 120, 144, 165, 240};
  const char* cap_labels[] = {"Off", "60 Hz", "75 Hz", "120 Hz", "144 Hz", "165 Hz", "240 Hz"};
  int cap_hz = REXCVAR_GET(dbz1_frame_cap);
  int cap_idx = 0;
  for (int i = 0; i < 7; i++) {
    if (cap_options[i] == cap_hz) {
      cap_idx = i;
      break;
    }
  }
  if (ImGui::Combo("Frame cap", &cap_idx, cap_labels, 7)) {
    REXCVAR_SET(dbz1_frame_cap, cap_options[cap_idx]);
  }
  ImGui::TextDisabled("Limits how often frames reach the display; does not change game speed.");

  ImGui::EndChild();
}

void LauncherDialog::DrawAudioTab() {
  ImGui::BeginChild("##audio_settings", ImVec2(0, -40), true);

  double vol_min = 0.0;
  double vol_max = 1.0;

  double master = REXCVAR_GET(dbz1_master_volume);
  if (ImGui::SliderScalar("Master volume", ImGuiDataType_Double, &master, &vol_min, &vol_max,
                          "%.2f")) {
    REXCVAR_SET(dbz1_master_volume, master);
  }
  ImGui::TextDisabled("Master volume is applied on the mixed audio stream.");

  ImGui::Separator();

  // Japanese voices/music is not offered: the adx_jp.afs pack has a different
  // internal structure than the base pack, so a swap makes the game misindex
  // the audio and hang during startup. Would need a rebuilt pack (mod).
  ImGui::TextDisabled("Japanese voices/music (adx_jp) is not available yet.");
  ImGui::TextDisabled("The JP audio pack has an incompatible internal layout; a swap would "
                      "hang startup. Requires a rebuilt pack (modding).");

  // Output device selector. First entry is always "System default"; selecting
  // it clears the override so the audio driver uses SDL's default device.
  if (!g_audio_devices_enumerated) {
    RefreshAudioPlaybackDevices();
  }

  int current_idx = 0;
  const std::string current = REXCVAR_GET(dbz1_audio_device);
  for (size_t i = 1; i <= g_audio_playback_devices.size(); ++i) {
    if (g_audio_playback_devices[i - 1] == current) {
      current_idx = static_cast<int>(i);
      break;
    }
  }

  const int device_option_count = static_cast<int>(g_audio_playback_devices.size()) + 1;
  std::vector<const char*> device_options;
  device_options.reserve(device_option_count);
  device_options.push_back("System default");
  for (const std::string& name : g_audio_playback_devices) {
    device_options.push_back(name.c_str());
  }

  if (ImGui::Combo("Output device", &current_idx, device_options.data(), device_option_count)) {
    if (current_idx == 0) {
      REXCVAR_SET(dbz1_audio_device, std::string(""));
    } else {
      REXCVAR_SET(dbz1_audio_device, g_audio_playback_devices[current_idx - 1]);
    }
  }
  ImGui::SameLine();
  if (ImGui::Button("Refresh")) {
    RefreshAudioPlaybackDevices();
  }
  ImGui::TextDisabled("Audio output device. Applied on game start (restart required).");

  ImGui::Separator();
  ImGui::TextWrapped(
      "Per-channel volume (music/SFX/voice) is not yet available: the game "
      "pre-mixes its channels on the guest side, so they cannot be split at "
      "the host audio stage. Planned via guest voice-category support.");

  ImGui::EndChild();
}

void LauncherDialog::DrawInputTab() {
  ImGui::BeginChild("##input_settings", ImVec2(0, -40), true);

  double deadzone = REXCVAR_GET(dbz1_deadzone);
  double deadzone_min = 0.0;
  double deadzone_max = 0.9;
  if (ImGui::SliderScalar("Analog stick deadzone", ImGuiDataType_Double, &deadzone,
                          &deadzone_min, &deadzone_max, "%.2f")) {
    REXCVAR_SET(dbz1_deadzone, deadzone);
  }

  bool rumble = REXCVAR_GET(dbz1_rumble);
  if (ImGui::Checkbox("Enable vibration", &rumble)) {
    REXCVAR_SET(dbz1_rumble, rumble);
  }

  bool mnk_mode = REXCVAR_GET(dbz1_mnk_mode);
  if (ImGui::Checkbox("Enable keyboard/mouse emulation", &mnk_mode)) {
    REXCVAR_SET(dbz1_mnk_mode, mnk_mode);
  }
  ImGui::TextDisabled("Emulates a controller with keyboard and mouse. Use the keybinds below.");

  ImGui::Separator();
  ImGui::Text("Keyboard (MnK) mapping");
  ImGui::TextDisabled("Key names follow VirtualKey (e.g. Space, W, Up, LMB, RMB, MMB). "
                      "Empty = unbound.");

#define DBZ1_DRAW_KEYBIND(name)                                        \
  std::string name = REXCVAR_GET(dbz1_keybind_##name);                 \
  DrawKeybind(#name, name);                                            \
  REXCVAR_SET(dbz1_keybind_##name, name)
  DBZ1_DRAW_KEYBIND(a);
  DBZ1_DRAW_KEYBIND(b);
  DBZ1_DRAW_KEYBIND(x);
  DBZ1_DRAW_KEYBIND(y);
  DBZ1_DRAW_KEYBIND(left_trigger);
  DBZ1_DRAW_KEYBIND(right_trigger);
  DBZ1_DRAW_KEYBIND(left_shoulder);
  DBZ1_DRAW_KEYBIND(right_shoulder);
  DBZ1_DRAW_KEYBIND(lstick_up);
  DBZ1_DRAW_KEYBIND(lstick_down);
  DBZ1_DRAW_KEYBIND(lstick_left);
  DBZ1_DRAW_KEYBIND(lstick_right);
  DBZ1_DRAW_KEYBIND(lstick_press);
  DBZ1_DRAW_KEYBIND(rstick_press);
  DBZ1_DRAW_KEYBIND(dpad_up);
  DBZ1_DRAW_KEYBIND(dpad_down);
  DBZ1_DRAW_KEYBIND(dpad_left);
  DBZ1_DRAW_KEYBIND(dpad_right);
  DBZ1_DRAW_KEYBIND(back);
  DBZ1_DRAW_KEYBIND(start);
#undef DBZ1_DRAW_KEYBIND

  ImGui::TextDisabled("Full button remapping is available in the in-game Settings overlay (F4).");
  ImGui::EndChild();
}

namespace {

// Maps an inferred/mod manifest type to a friendly label and color.
const char* ModTypeLabel(const std::string& type) {
  if (type == "port_b3") return "Port B3->B1";
  if (type == "swap_b1") return "Swap B1->B1";
  if (type == "moveset") return "Moveset";
  if (type == "audio") return "Audio";
  if (type == "data") return "Data";
  return "Other";
}

ImVec4 ModTypeColor(const std::string& type) {
  if (type == "port_b3") return ImVec4(0.45f, 0.90f, 0.45f, 1.0f);
  if (type == "swap_b1") return ImVec4(0.45f, 0.75f, 1.00f, 1.0f);
  if (type == "moveset") return ImVec4(1.00f, 0.45f, 0.45f, 1.0f);
  if (type == "audio") return ImVec4(0.80f, 0.60f, 1.00f, 1.0f);
  return ImVec4(0.70f, 0.70f, 0.70f, 1.0f);
}

}  // namespace

void LauncherDialog::DrawModsTab() {
  ImGui::BeginChild("##mods_settings", ImVec2(0, -40), true);

  ImGui::TextWrapped(
      "Mods override entries inside the game's .afs containers (models, move "
      "sets, textures) without repacking. A mod is a folder here:");
  ImGui::TextDisabled("mods/<name>/us/<file.afs>/<entry_index>/...");
  ImGui::Separator();

  const std::vector<dbz1::ModInfo> mods = dbz1::ListMods();
  if (mods.empty()) {
    ImGui::TextDisabled("No mods found in the 'mods' folder next to the executable.");
  } else {
  // Summary line.
  int enabled_count = 0;
  for (const dbz1::ModInfo& mod : mods) {
    if (mod.enabled) ++enabled_count;
  }
  ImGui::TextColored(ImVec4(0.80f, 0.80f, 0.80f, 1.0f), "%d mods (%d enabled)",
                     static_cast<int>(mods.size()), enabled_count);
  ImGui::Separator();

  const float table_w = ImGui::GetContentRegionAvail().x;
  if (ImGui::BeginTable("##mods_table", 4,
                        ImGuiTableFlags_BordersInnerV |
                            ImGuiTableFlags_NoHostExtendX)) {
    ImGui::TableSetupColumn("", ImGuiTableColumnFlags_WidthFixed, 28.0f);
    ImGui::TableSetupColumn("Mod", ImGuiTableColumnFlags_WidthStretch);
    ImGui::TableSetupColumn("Type", ImGuiTableColumnFlags_WidthFixed,
                            std::min(130.0f, table_w * 0.18f));
    ImGui::TableSetupColumn("", ImGuiTableColumnFlags_WidthFixed, 44.0f);
    ImGui::TableHeadersRow();

    for (const dbz1::ModInfo& mod : mods) {
      ImGui::TableNextRow();
      const float row_h = ImGui::GetFrameHeight() + ImGui::GetStyle().CellPadding.y;

      // Checkbox (enable/disable).
      ImGui::TableSetColumnIndex(0);
      bool current = mod.enabled;
      ImGui::SetCursorPosY(ImGui::GetCursorPosY() +
                           (row_h - ImGui::GetFrameHeight()) * 0.5f);
      if (ImGui::Checkbox(("##mod_" + mod.name).c_str(), &current)) {
        dbz1::SetModEnabled(mod.name, current);
      }

      // Name + description.
      ImGui::TableSetColumnIndex(1);
      const std::string& title =
          mod.display_name.empty() ? mod.name : mod.display_name;
      ImVec4 title_col = mod.enabled ? ImVec4(1.0f, 1.0f, 1.0f, 1.0f)
                                     : ImVec4(0.55f, 0.55f, 0.55f, 1.0f);
      ImGui::TextColored(title_col, "%s", title.c_str());
      if (!mod.description.empty()) {
        ImGui::TextDisabled("%s", mod.description.c_str());
      } else if (mod.source.empty() && mod.target.empty()) {
        ImGui::TextDisabled("%s", mod.name.c_str());
      }
      if (!mod.source.empty() || !mod.target.empty()) {
        std::string route = mod.source;
        if (!route.empty()) route += " -> ";
        route += mod.target;
        ImGui::TextDisabled("%s", route.c_str());
      }
      ImGui::TextDisabled("%d file%s", mod.file_count,
                          mod.file_count == 1 ? "" : "s");

      // Type badge + status; full details in a tooltip.
      ImGui::TableSetColumnIndex(2);
      ImGui::TextColored(ModTypeColor(mod.type), "%s", ModTypeLabel(mod.type));
      if (mod.enabled) {
        ImGui::SameLine();
        ImGui::TextColored(ImVec4(0.35f, 0.85f, 0.35f, 1.0f), "ON");
      }
      if (ImGui::IsItemHovered()) {
        ImGui::SetTooltip("%s\n%s\nAuthor: %s\nVersion: %s\nType: %s\nSource: %s\nTarget: %s",
                          title.c_str(),
                          mod.description.empty() ? "(no description)" : mod.description.c_str(),
                          mod.author.empty() ? "-" : mod.author.c_str(),
                          mod.version.empty() ? "-" : mod.version.c_str(),
                          ModTypeLabel(mod.type), mod.source.c_str(),
                          mod.target.c_str());
      }

      // Edit manifest button.
      ImGui::TableSetColumnIndex(3);
      if (ImGui::SmallButton(("##edit_" + mod.name).c_str())) {
        editing_mod_ = true;
        edit_mod_name_ = mod.name;
        std::string d = dbz1::GetModManifestValue(mod.name, "description");
        std::string a = dbz1::GetModManifestValue(mod.name, "author");
        std::string v = dbz1::GetModManifestValue(mod.name, "version");
        std::memcpy(edit_desc_buf_, d.c_str(),
                    std::min(d.size(), sizeof(edit_desc_buf_) - 1));
        edit_desc_buf_[std::min(d.size(), sizeof(edit_desc_buf_) - 1)] = '\0';
        std::memcpy(edit_author_buf_, a.c_str(),
                    std::min(a.size(), sizeof(edit_author_buf_) - 1));
        edit_author_buf_[std::min(a.size(), sizeof(edit_author_buf_) - 1)] = '\0';
        std::memcpy(edit_version_buf_, v.c_str(),
                    std::min(v.size(), sizeof(edit_version_buf_) - 1));
        edit_version_buf_[std::min(v.size(), sizeof(edit_version_buf_) - 1)] = '\0';
      }
      if (ImGui::IsItemHovered()) {
        ImGui::SetTooltip("Editar descripcion / autor / version (manifest.txt)");
      }
    }
    ImGui::EndTable();
  }

  // Inline edit dialog for the selected mod's manifest.
  if (editing_mod_) {
    ImGui::Separator();
    ImGui::TextColored(ImVec4(0.90f, 0.85f, 0.50f, 1.0f), "Editar mod: %s",
                       edit_mod_name_.c_str());
    ImGui::Text("Descripcion");
    ImGui::InputTextMultiline("##edit_desc", edit_desc_buf_,
                              sizeof(edit_desc_buf_), ImVec2(-1.0f, 64.0f));
    ImGui::Text("Autor");
    ImGui::InputText("##edit_author", edit_author_buf_,
                     sizeof(edit_author_buf_));
    ImGui::Text("Version");
    ImGui::InputText("##edit_version", edit_version_buf_,
                     sizeof(edit_version_buf_));
    if (ImGui::Button("Guardar", ImVec2(120, 0))) {
      dbz1::SetModManifestValue(edit_mod_name_, "description", edit_desc_buf_);
      dbz1::SetModManifestValue(edit_mod_name_, "author", edit_author_buf_);
      dbz1::SetModManifestValue(edit_mod_name_, "version", edit_version_buf_);
      editing_mod_ = false;
      pending_manifest_reload_ = true;
    }
    ImGui::SameLine();
    if (ImGui::Button("Cancelar", ImVec2(120, 0))) {
      editing_mod_ = false;
    }
    ImGui::SameLine();
    ImGui::TextDisabled("El texto se guarda en %s/manifest.txt",
                        edit_mod_name_.c_str());
  }
  }

  ImGui::Separator();
  DrawModPipelineTab();

  ImGui::EndChild();
}

void LauncherDialog::DrawModPipelineTab() {
  ImGui::SeparatorText("Model pipeline");
  ImGui::TextDisabled("Porta modelos de Budokai 3 HD al B1, o hace swaps B1->B1 "
                      "con el catalogo del juego. Genera el mod y lo activa.");

  // --- Source archives (.afs) ---
  ImGui::SeparatorText("Archivos fuente (.afs)");
  ImGui::TextDisabled("Selecciona tus copias de los AFS si el juego no esta en "
                      "la ubicacion por defecto. Vacio = autodeteccion.");
  if (!afs_bufs_synced_) {
    std::string b1 = dbz1::settings::AfsB1Path();
    std::string b3 = dbz1::settings::AfsB3Path();
    std::memcpy(afs_b1_buf_, b1.c_str(), std::min(b1.size(), sizeof(afs_b1_buf_) - 1));
    afs_b1_buf_[std::min(b1.size(), sizeof(afs_b1_buf_) - 1)] = '\0';
    std::memcpy(afs_b3_buf_, b3.c_str(), std::min(b3.size(), sizeof(afs_b3_buf_) - 1));
    afs_b3_buf_[std::min(b3.size(), sizeof(afs_b3_buf_) - 1)] = '\0';
    afs_bufs_synced_ = true;
  }

  auto draw_afs_row = [this](const char* label, const char* id, char* buf,
                             size_t bufsz, int dialog_target) {
    ImGui::Text("%s", label);
    ImGui::SameLine();
    ImGui::SetNextItemWidth(360);
    if (ImGui::InputText(id, buf, bufsz)) {
      if (dialog_target == 1) {
        dbz1::settings::SetAfsB1Path(buf);
      } else {
        dbz1::settings::SetAfsB3Path(buf);
      }
    }
    ImGui::SameLine();
    if (ImGui::Button(("Buscar##" + std::string(id)).c_str())) {
      // Native Windows file dialog (the bundled SDL3 uses the dummy dialog
      // driver, so SDL_ShowOpenFileDialog would never open one). Runs
      // synchronously on the UI thread, so no thread-safety concerns.
      const std::string path = ShowNativeOpenFileDialog(
          "AFS archives (*.afs)", "*.afs");
      if (!path.empty()) {
        std::memcpy(buf, path.c_str(), std::min(path.size(), bufsz - 1));
        buf[std::min(path.size(), bufsz - 1)] = '\0';
        if (dialog_target == 1) {
          dbz1::settings::SetAfsB1Path(path);
        } else {
          dbz1::settings::SetAfsB3Path(path);
        }
      }
    }
  };

  draw_afs_row("AFS B1 HD (data_us/sp/fr/en/ge/it):", "##afs_b1", afs_b1_buf_,
               sizeof(afs_b1_buf_), 1);
  draw_afs_row("AFS B3 HD (data_cmn.afs):", "##afs_b3", afs_b3_buf_,
               sizeof(afs_b3_buf_), 2);
  if (ImGui::Button("Usar ubicaciones por defecto", ImVec2(220, 0))) {
    // Clear the custom paths (empty = autodeteccion: data_us.afs del B1 y
    // data_cmn.afs del B3) and regenerate the catalog with them.
    dbz1::settings::SetAfsB1Path("");
    dbz1::settings::SetAfsB3Path("");
    afs_b1_buf_[0] = '\0';
    afs_b3_buf_[0] = '\0';
    catalog_load_attempted_ = false;
    if (!mod_pipeline_.IsRunning()) {
      mod_pipeline_.ScanCharacters();
    }
  }
  ImGui::SameLine();
  ImGui::TextDisabled("El catalogo se regenera con las rutas elegidas.");

  // Lazy-load the character catalog once (first draw).
  if (!catalog_load_attempted_) {
    catalog_load_attempted_ = true;
    mod_pipeline_.LoadCatalog();
  }

  const auto& b1 = mod_pipeline_.B1();
  const auto& b3 = mod_pipeline_.B3();

  if (!mod_pipeline_.CatalogLoaded()) {
    ImGui::TextWrapped("El catalogo de personajes no existe todavia. Escanealo "
                       "una vez (tarda ~1 min):");
    if (ImGui::Button("Scan characters", ImVec2(180, 0))) {
      mod_pipeline_.ScanCharacters();
    }
  } else {
    // Reload the catalog once a background scan finishes.
    if (scan_was_running_ && !mod_pipeline_.IsRunning()) {
      mod_pipeline_.LoadCatalog();
    }
    scan_was_running_ = mod_pipeline_.IsRunning();

    const bool b1_empty = b1.empty();
    const bool b3_empty = b3.empty();
    if (b1_empty && b3_empty) {
      ImGui::TextDisabled("Catalogo vacio.");
    } else {

    // --- Port B3 -> B1 ---
    ImGui::SeparatorText("Port B3 -> B1 (modelo de Budokai 3 al B1)");
    if (b3_empty || b1_empty) {
      ImGui::TextDisabled("Faltan personajes B3 o B1 en el catalogo.");
    } else {
      if (pipeline_b3_idx_ >= (int)b3.size()) pipeline_b3_idx_ = -1;
      if (pipeline_b1_dst_idx_ >= (int)b1.size()) pipeline_b1_dst_idx_ = -1;

      ImGui::Text("Modelo B3 (origen)");
      ImGui::SameLine();
      ImGui::SetNextItemWidth(320);
      if (ImGui::BeginCombo("##b3_src", pipeline_b3_idx_ >= 0
                                ? b3[pipeline_b3_idx_].DisplayName().c_str()
                                : "Selecciona...")) {
        for (int i = 0; i < (int)b3.size(); ++i) {
          const bool selected = (pipeline_b3_idx_ == i);
          if (ImGui::Selectable(b3[i].DisplayName().c_str(), selected)) {
            pipeline_b3_idx_ = i;
          }
          if (selected) ImGui::SetItemDefaultFocus();
        }
        ImGui::EndCombo();
      }
      ImGui::SameLine();
      ImGui::TextDisabled("(%d modelos)", static_cast<int>(b3.size()));
      ImGui::Text("Personaje B1 (destino)");
      ImGui::SameLine();
      ImGui::SetNextItemWidth(320);
      if (ImGui::BeginCombo("##b1_dst", pipeline_b1_dst_idx_ >= 0
                                ? b1[pipeline_b1_dst_idx_].DisplayName().c_str()
                                : "Selecciona...")) {
        for (int i = 0; i < (int)b1.size(); ++i) {
          const bool selected = (pipeline_b1_dst_idx_ == i);
          if (ImGui::Selectable(b1[i].DisplayName().c_str(), selected)) {
            pipeline_b1_dst_idx_ = i;
          }
          if (selected) ImGui::SetItemDefaultFocus();
        }
        ImGui::EndCombo();
      }
      ImGui::SameLine();
      ImGui::TextDisabled("(%d modelos)", static_cast<int>(b1.size()));
      const bool can_port = pipeline_b3_idx_ >= 0 && pipeline_b1_dst_idx_ >= 0;
      const bool b3_afs_set = !dbz1::settings::AfsB3Path().empty();
      const bool b1_afs_set = !dbz1::settings::AfsB1Path().empty();
      if (!b3_afs_set || !b1_afs_set) {
        ImGui::TextColored(ImVec4(1.0f, 0.8f, 0.3f, 1.0f),
                           "AVISO: %s%sArchivos fuente no seleccionados; "
                           "se usara la autodeteccion.",
                           b3_afs_set ? "" : "AFS B3 (data_cmn.afs) vacio. ",
                           b1_afs_set ? "" : "AFS B1 (data_us.afs) vacio. ");
      }
      ImGui::BeginDisabled(!can_port || mod_pipeline_.IsRunning());
      if (ImGui::Button("Portar modelo B3 -> B1", ImVec2(220, 0))) {
        mod_pipeline_.PortB3ToB1(b3[pipeline_b3_idx_], b1[pipeline_b1_dst_idx_]);
      }
      ImGui::EndDisabled();
      if (can_port) {
        const ModChar& src = b3[pipeline_b3_idx_];
        const ModChar& dst = b1[pipeline_b1_dst_idx_];
        ImGui::TextDisabled("%s (bin %d, %d verts)%s -> %s (slots %d/%d)%s",
                            src.DisplayName().c_str(), src.geom, src.verts,
                            src.playable ? "" : "  [NO JUGABLE]",
                            dst.DisplayName().c_str(), dst.geom, dst.tex,
                            dst.playable ? "" : "  [NO JUGABLE]");
      }
    }

    // --- Swap B1 -> B1 ---
    ImGui::SeparatorText("Swap B1 -> B1 (desde el propio Budokai 1 HD)");
    if (b1_empty) {
      ImGui::TextDisabled("Faltan personajes B1 en el catalogo.");
    } else {
      // Only characters with a real geom slot are usable as swap source.
      std::vector<int> swap_src_idx, swap_dst_idx;
      for (int i = 0; i < (int)b1.size(); ++i) {
        if (b1[i].geom != 0) {
          swap_src_idx.push_back(i);
          swap_dst_idx.push_back(i);
        }
      }
      if (pipeline_b1_src_idx_ >= (int)swap_src_idx.size()) pipeline_b1_src_idx_ = -1;
      if (pipeline_swap_dst_idx_ >= (int)swap_dst_idx.size()) pipeline_swap_dst_idx_ = -1;

      ImGui::Text("Origen");
      ImGui::SameLine();
      ImGui::SetNextItemWidth(320);
      ImGui::BeginDisabled(mod_pipeline_.IsRunning());
      if (ImGui::BeginCombo("##swap_src", pipeline_b1_src_idx_ >= 0
                                ? b1[swap_src_idx[pipeline_b1_src_idx_]].DisplayName().c_str()
                                : "Selecciona...")) {
        for (int i = 0; i < (int)swap_src_idx.size(); ++i) {
          const bool selected = (pipeline_b1_src_idx_ == i);
          if (ImGui::Selectable(b1[swap_src_idx[i]].DisplayName().c_str(), selected)) {
            pipeline_b1_src_idx_ = i;
          }
          if (selected) ImGui::SetItemDefaultFocus();
        }
        ImGui::EndCombo();
      }
      ImGui::EndDisabled();
      ImGui::SameLine();
      ImGui::TextDisabled("(%d modelos)", static_cast<int>(swap_src_idx.size()));
      ImGui::Text("Destino");
      ImGui::SameLine();
      ImGui::SetNextItemWidth(320);
      ImGui::BeginDisabled(mod_pipeline_.IsRunning());
      if (ImGui::BeginCombo("##swap_dst", pipeline_swap_dst_idx_ >= 0
                                ? b1[swap_dst_idx[pipeline_swap_dst_idx_]].DisplayName().c_str()
                                : "Selecciona...")) {
        for (int i = 0; i < (int)swap_dst_idx.size(); ++i) {
          const bool selected = (pipeline_swap_dst_idx_ == i);
          if (ImGui::Selectable(b1[swap_dst_idx[i]].DisplayName().c_str(), selected)) {
            pipeline_swap_dst_idx_ = i;
          }
          if (selected) ImGui::SetItemDefaultFocus();
        }
        ImGui::EndCombo();
      }
      ImGui::EndDisabled();
      ImGui::SameLine();
      ImGui::TextDisabled("(%d modelos)", static_cast<int>(swap_dst_idx.size()));
      if (!dbz1::settings::AfsB1Path().empty() == false) {
        ImGui::TextColored(ImVec4(1.0f, 0.8f, 0.3f, 1.0f),
                           "AVISO: AFS B1 (data_us.afs) no seleccionado; "
                           "se usara la autodeteccion.");
      }
      const bool can_swap = pipeline_b1_src_idx_ >= 0 && pipeline_swap_dst_idx_ >= 0;
      ImGui::BeginDisabled(!can_swap || mod_pipeline_.IsRunning());
      if (ImGui::Button("Swap B1 -> B1", ImVec2(220, 0))) {
        mod_pipeline_.SwapB1ToB1(b1[swap_src_idx[pipeline_b1_src_idx_]],
                                 b1[swap_dst_idx[pipeline_swap_dst_idx_]]);
      }
      ImGui::EndDisabled();
      if (can_swap) {
        const ModChar& src = b1[swap_src_idx[pipeline_b1_src_idx_]];
        const ModChar& dst = b1[swap_dst_idx[pipeline_swap_dst_idx_]];
        ImGui::TextDisabled("%s (geom %d)%s -> %s (slots %d/%d)%s",
                            src.DisplayName().c_str(), src.geom,
                            src.playable ? "" : "  [NO JUGABLE]",
                            dst.DisplayName().c_str(), dst.geom, dst.tex,
                            dst.playable ? "" : "  [NO JUGABLE]");
      }
    }
  }
  }

  // --- Output / status ---
  ImGui::Separator();
  if (mod_pipeline_.IsRunning()) {
    ImGui::TextColored(ImVec4(1.0f, 0.8f, 0.2f, 1.0f),
                       "Working... el pipeline esta ejecutandose (comprimir + "
                       "validar + instalar). Puede tardar ~1 min.");
    ImGui::ProgressBar(-1.0f, ImVec2(-1.0f, 0.0f),
                       "Procesando...");
    ImGui::TextDisabled("No cambies la seleccion de modelos mientras corre.");
  } else if (!mod_pipeline_.Output().empty()) {
    const std::string& out = mod_pipeline_.Output();
    const bool has_error =
        out.find("ERROR") != std::string::npos ||
        out.find("INCOMPATIBLE") != std::string::npos;
    ImGui::TextColored(has_error ? ImVec4(1.0f, 0.3f, 0.3f, 1.0f)
                                 : ImVec4(0.3f, 1.0f, 0.3f, 1.0f),
                       has_error ? "ERROR: el mod no se instalo." : "Done.");
  }
  const std::string out = mod_pipeline_.Output();
  if (!out.empty()) {
    std::memcpy(output_buf_, out.c_str(),
                std::min(out.size(), sizeof(output_buf_) - 1));
    output_buf_[std::min(out.size(), sizeof(output_buf_) - 1)] = '\0';
    ImGui::InputTextMultiline("##pipeline_out", output_buf_,
                              sizeof(output_buf_), ImVec2(-1.0f, 180.0f),
                              ImGuiInputTextFlags_ReadOnly);
  }
  ImGui::TextDisabled("Los mods generados se activan solos y se listan arriba.");
}

void LauncherDialog::DrawDevTab() {
  ImGui::BeginChild("##dev_settings", ImVec2(0, -40), true);

  bool dev_mode = REXCVAR_GET(dbz1_dev_mode);
  if (ImGui::Checkbox("Enable Dev mode (F10 overlay)", &dev_mode)) {
    REXCVAR_SET(dbz1_dev_mode, dev_mode);
  }
  ImGui::TextDisabled("Dev mode adds an in-game overlay (F10) with hot toggles for\n"
                      "diagnostics and test switches while the game runs.");

  bool show_fps = dbz1::settings::ShowFps();
  if (ImGui::Checkbox("Show FPS counter in-game", &show_fps)) {
    dbz1::settings::SetShowFps(show_fps);
  }
  ImGui::TextDisabled("Displays a small corner window with the current FPS while\n"
                      "playing. Independent of the F10 dev overlay.");

  bool diag = REXCVAR_GET(dbz1_diag_logging);
  if (ImGui::Checkbox("GPU diagnostic logging (dbz1_gpu_diag.log)", &diag)) {
    REXCVAR_SET(dbz1_diag_logging, diag);
  }
  ImGui::TextDisabled("Writes per-frame GPU diagnostics. Large log files. Keep off normally.");

  ImGui::EndChild();
}

}  // namespace dbz1::launcher
