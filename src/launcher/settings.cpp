// dbz1 - User settings layer implementation.

#include "settings.h"

#include <rex/cvar.h>
#include <rex/filesystem.h>
#include <rex/logging.h>

#include <filesystem>
#include <string>

// ---------------------------------------------------------------------------
// CVar definitions. These MUST live at global scope: the REXCVAR_DEFINE_*
// macros generate accessor functions (FLAGS_##name##_storage_()) that other
// TUs reference at global scope via REXCVAR_DECLARE/REXCVAR_GET.
// ---------------------------------------------------------------------------

// User-facing cvars (friendly categories so they show in the F4 settings tree
// grouped separately from the SDK's own "Display"/"GPU" cvars).
REXCVAR_DEFINE_INT32(dbz1_resolution_scale, 1, "DBZ1/Video",
                     "Internal render scale (1x-4x supersampling of the 720p framebuffer)")
    .range(1, 4)
    .lifecycle(rex::cvar::Lifecycle::kRequiresRestart);

REXCVAR_DEFINE_STRING(dbz1_fullscreen_mode, "windowed", "DBZ1/Video",
                      "Fullscreen mode: windowed, borderless, exclusive")
    .lifecycle(rex::cvar::Lifecycle::kRequiresRestart);

REXCVAR_DEFINE_BOOL(dbz1_vsync, true, "DBZ1/Video", "Vertical sync")
    .lifecycle(rex::cvar::Lifecycle::kHotReload);

REXCVAR_DEFINE_INT32(dbz1_anisotropic, 3, "DBZ1/Video",
                     "Anisotropic filtering: -1=auto, 0=off, 1x/2x/4x/8x/16x")
    .range(-1, 5)
    .lifecycle(rex::cvar::Lifecycle::kHotReload);

REXCVAR_DEFINE_BOOL(dbz1_msaa_2x, true, "DBZ1/Video", "Enable native 2x MSAA")
    .lifecycle(rex::cvar::Lifecycle::kHotReload);

REXCVAR_DEFINE_INT32(dbz1_swap_effect, 0, "DBZ1/Video",
                     "Swap post effect: 0=none, 1=fxaa, 2=fxaa_extreme")
    .range(0, 2)
    .lifecycle(rex::cvar::Lifecycle::kRequiresRestart);

REXCVAR_DEFINE_INT32(dbz1_frame_cap, 0, "DBZ1/Video", "Frame cap in FPS (0 = uncapped)")
    .range(0, 240)
    .lifecycle(rex::cvar::Lifecycle::kHotReload);

// Graphics backend for the GPU plugin. Persisted wrapper; forwarded to the SDK
// gpu_backend cvar (rex_app.cpp) in ApplyUserSettingsToSdk. Read before the GPU
// plugin loads, so it must be set at boot (kRequiresRestart).
REXCVAR_DEFINE_STRING(dbz1_gpu_backend, "auto", "DBZ1/Video",
                      "Graphics backend: auto (D3D12 first), d3d12 or vulkan")
    .allowed({"auto", "d3d12", "vulkan"})
    .lifecycle(rex::cvar::Lifecycle::kRequiresRestart);

// Present upscaler (FidelityFX). Forwarded to the SDK present_effect cvar in
// ApplyUserSettingsToSdk. FSR2/FSR3 temporal upscaling requires the FidelityFX
// runtime built for the active backend (D3D12 in this build).
REXCVAR_DEFINE_STRING(dbz1_present_effect, "bilinear", "DBZ1/Video",
                      "Present upscaler: bilinear, cas, fsr, fsr2, fsr3")
    .allowed({"bilinear", "cas", "fsr", "fsr2", "fsr3"})
    .lifecycle(rex::cvar::Lifecycle::kRequiresRestart);

// FSR quality mode, used when the present effect is fsr/fsr2/fsr3. Forwarded to
// the SDK present_fsr_quality_mode cvar in ApplyUserSettingsToSdk.
REXCVAR_DEFINE_STRING(dbz1_fsr_quality, "auto", "DBZ1/Video",
                      "FSR quality mode: auto, nativeaa, quality, balanced, performance, "
                      "ultra_performance")
    .allowed({"auto", "nativeaa", "quality", "balanced", "performance", "ultra_performance"})
    .lifecycle(rex::cvar::Lifecycle::kRequiresRestart);

// Region (assets folder). Persisted wrapper; forwarded to the shared dbz1_region
// (rexruntime.dll) in ApplyUserSettingsToSdk.
REXCVAR_DEFINE_STRING(dbz1_user_region, "us", "DBZ1/Video",
                      "Game region assets folder: us or eu")
    .allowed({"us", "eu"})
    .lifecycle(rex::cvar::Lifecycle::kRequiresRestart);

// Language (XLanguage ID: 1=English, 4=French, 5=Spanish; 3=German, 6=Italian
// exist in the enum but their PS2 packs are not compatible with the X360 build).
// Persisted wrapper; forwarded to the shared user_language cvar (rexruntime.dll).
REXCVAR_DEFINE_INT32(dbz1_language, 1, "DBZ1/Video",
                     "Game language: 1=English, 4=French, 5=Spanish")
    .range(1, 12)
    .lifecycle(rex::cvar::Lifecycle::kRequiresRestart);

// Japanese audio toggle. Persisted wrapper; forwarded to the shared dbz1_audio_jp
// (rexruntime.dll) in ApplyUserSettingsToSdk.
REXCVAR_DEFINE_BOOL(dbz1_user_audio_jp, false, "DBZ1/Audio",
                    "Use Japanese voice/music pack (adx_jp.afs)")
    .lifecycle(rex::cvar::Lifecycle::kRequiresRestart);

REXCVAR_DEFINE_DOUBLE(dbz1_gamma, 1.0, "DBZ1/Video", "Gamma correction (0.5 - 2.0)")
    .range(0.5, 2.0)
    .lifecycle(rex::cvar::Lifecycle::kHotReload);

REXCVAR_DEFINE_DOUBLE(dbz1_master_volume, 1.0, "DBZ1/Audio", "Master volume (0.0 - 1.0)")
    .range(0.0, 1.0)
    .lifecycle(rex::cvar::Lifecycle::kHotReload);

REXCVAR_DEFINE_DOUBLE(dbz1_music_volume, 1.0, "DBZ1/Audio", "Music volume (0.0 - 1.0)")
    .range(0.0, 1.0)
    .lifecycle(rex::cvar::Lifecycle::kHotReload);

REXCVAR_DEFINE_DOUBLE(dbz1_sfx_volume, 1.0, "DBZ1/Audio", "SFX volume (0.0 - 1.0)")
    .range(0.0, 1.0)
    .lifecycle(rex::cvar::Lifecycle::kHotReload);

REXCVAR_DEFINE_DOUBLE(dbz1_voice_volume, 1.0, "DBZ1/Audio", "Voice volume (0.0 - 1.0)")
    .range(0.0, 1.0)
    .lifecycle(rex::cvar::Lifecycle::kHotReload);

REXCVAR_DEFINE_STRING(dbz1_audio_device, "", "DBZ1/Audio",
                      "Output device name (empty = system default)")
    .lifecycle(rex::cvar::Lifecycle::kRequiresRestart);

REXCVAR_DEFINE_DOUBLE(dbz1_deadzone, 0.1, "DBZ1/Input", "Left stick deadzone (0.0 - 1.0)")
    .range(0.0, 0.9)
    .lifecycle(rex::cvar::Lifecycle::kHotReload);

REXCVAR_DEFINE_BOOL(dbz1_rumble, true, "DBZ1/Input", "Enable controller vibration")
    .lifecycle(rex::cvar::Lifecycle::kHotReload);

REXCVAR_DEFINE_BOOL(dbz1_mnk_mode, false, "DBZ1/Input",
                    "Enable keyboard/mouse controller emulation")
    .lifecycle(rex::cvar::Lifecycle::kHotReload);

// MnK keybinds. These dbz1_* wrappers live in the launcher's registry so they
// persist to dbz1_user.toml; the values are forwarded to the shared keybind_*
// cvars (defined in rexinput -> rexruntime.dll) in ApplyUserSettingsToSdk.
// Defaults mirror the SDK's mnk_input_driver.cpp. Keyboard-only: the mouse
// buttons are NOT used so the cursor stays usable for menus. Empty = unbound.
#define DBZ1_KEYBIND(name, default_val)                                              \
  REXCVAR_DEFINE_STRING(dbz1_keybind_##name, default_val, "DBZ1/Input", "Key: " #name) \
      .lifecycle(rex::cvar::Lifecycle::kHotReload)
DBZ1_KEYBIND(a, "J");
DBZ1_KEYBIND(b, "K");
DBZ1_KEYBIND(x, "I");
DBZ1_KEYBIND(y, "U");
DBZ1_KEYBIND(left_trigger, "Q");
DBZ1_KEYBIND(right_trigger, "E");
DBZ1_KEYBIND(left_shoulder, "Shift");
DBZ1_KEYBIND(right_shoulder, "F");
DBZ1_KEYBIND(lstick_up, "W");
DBZ1_KEYBIND(lstick_down, "S");
DBZ1_KEYBIND(lstick_left, "A");
DBZ1_KEYBIND(lstick_right, "D");
DBZ1_KEYBIND(lstick_press, "C");
DBZ1_KEYBIND(rstick_press, "V");
DBZ1_KEYBIND(dpad_up, "Up");
DBZ1_KEYBIND(dpad_down, "Down");
DBZ1_KEYBIND(dpad_left, "Left");
DBZ1_KEYBIND(dpad_right, "Right");
DBZ1_KEYBIND(back, "Backspace");
DBZ1_KEYBIND(start, "Return");
#undef DBZ1_KEYBIND

// Dev mode switches (F10 overlay).
REXCVAR_DEFINE_BOOL(dbz1_dev_mode, false, "DBZ1/Dev", "Enable the F10 dev-mode overlay")
    .lifecycle(rex::cvar::Lifecycle::kHotReload);

// Optional in-game FPS counter (corner window, small).
REXCVAR_DEFINE_BOOL(dbz1_show_fps, false, "DBZ1/Dev", "Show an in-game FPS counter")
    .lifecycle(rex::cvar::Lifecycle::kHotReload);

// Model pipeline source archives. If set, the launcher uses these instead of
// the auto-detected ones. B1: any data_*.afs (sp/us/fr/en/ge/it) works — all
// share the same bin numbering. B3: data_cmn.afs.
REXCVAR_DEFINE_STRING(dbz1_afs_b1_path, "", "DBZ1/Dev",
                      "Path to a Budokai 1 data_*.afs (empty = auto-detect assets folder)")
    .lifecycle(rex::cvar::Lifecycle::kHotReload);
REXCVAR_DEFINE_STRING(dbz1_afs_b3_path, "", "DBZ1/Dev",
                      "Path to the Budokai 3 data_cmn.afs (empty = auto-detect B3 project)")
    .lifecycle(rex::cvar::Lifecycle::kHotReload);

// Diagnostic logging toggle. Shared with the GPU plugin via rexruntime.dll
// (src/system/dbz1_diag_flags.cpp); declared here (not defined) so F10 toggles
// the same storage the plugin reads.
REXCVAR_DECLARE(bool, dbz1_diag_logging);

// Skip the launcher screen on boot (quick testing / automation).
REXCVAR_DEFINE_BOOL(dbz1_skip_launcher, false, "DBZ1/Dev", "Skip the launcher on boot")
    .lifecycle(rex::cvar::Lifecycle::kRequiresRestart);

// SDK cvars we drive from the friendly settings. Only a few are exported as
// linkable symbols by rexruntime.dll (resolution, fullscreen, present_effect,
// user_language, audio_mute, host_present_from_non_ui_thread,
// d3d12_allow_variable_refresh_rate_and_tearing, video_mode_refresh_rate).
// The rest are read/written via rex::cvar::SetFlagByName / Query, which resolve
// by name at runtime without a linkable symbol.
REXCVAR_DECLARE(std::string, resolution);
REXCVAR_DECLARE(bool, fullscreen);
REXCVAR_DECLARE(std::string, present_effect);
REXCVAR_DECLARE(uint32_t, user_language);
REXCVAR_DECLARE(bool, audio_mute);
REXCVAR_DECLARE(bool, host_present_from_non_ui_thread);
REXCVAR_DECLARE(bool, d3d12_allow_variable_refresh_rate_and_tearing);
REXCVAR_DECLARE(double, video_mode_refresh_rate);

static void SetSdkString(const char* name, const std::string& value) {
  rex::cvar::SetFlagByName(name, value);
}
static void SetSdkBool(const char* name, bool value) {
  rex::cvar::SetFlagByName(name, value ? "true" : "false");
}
static void SetSdkInt(const char* name, int32_t value) {
  rex::cvar::SetFlagByName(name, std::to_string(value));
}
static void SetSdkDouble(const char* name, double value) {
  rex::cvar::SetFlagByName(name, std::to_string(value));
}

// Project-side region + audio-language state. The launcher defines these here
// (the pre-built rexruntime.dll does not export them) and forwards them via
// ApplyUserSettingsToSdk; region.cpp reads them to mount the assets folder.
REXCVAR_DEFINE_STRING(dbz1_region, "us", "DBZ1/Video",
                      "Game region assets folder: us or eu")
    .allowed({"us", "eu"})
    .lifecycle(rex::cvar::Lifecycle::kRequiresRestart);

REXCVAR_DEFINE_BOOL(dbz1_audio_jp, false, "DBZ1/Audio",
                    "Use the Japanese audio pack (adx_jp.afs) instead of English")
    .lifecycle(rex::cvar::Lifecycle::kRequiresRestart);

// SDK MnK keybinds (defined in rexinput -> rexruntime.dll).
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

// dbz1_keybind_* wrappers (persisted; defined above in this file).
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

namespace dbz1::settings {

std::filesystem::path UserSettingsPath() {
  return rex::filesystem::GetExecutableFolder() / "dbz1_user.toml";
}

void LoadUserSettings() {
  const auto path = UserSettingsPath();
  if (std::filesystem::exists(path)) {
    rex::cvar::LoadConfig(path);
    REXLOG_INFO("dbz1: user settings loaded from {}", path.string());
  } else {
    REXLOG_INFO("dbz1: no user settings file at {}, using defaults", path.string());
  }
}

void SaveUserSettings() {
  const auto path = UserSettingsPath();
  rex::cvar::SaveConfig(path);
  REXLOG_INFO("dbz1: user settings saved to {}", path.string());
}

int32_t ResolutionScale() { return REXCVAR_GET(dbz1_resolution_scale); }

void SetResolutionScale(int32_t scale) {
  REXCVAR_SET(dbz1_resolution_scale, scale);
}

std::string AfsB1Path() { return REXCVAR_GET(dbz1_afs_b1_path); }
void SetAfsB1Path(const std::string& path) {
  REXCVAR_SET(dbz1_afs_b1_path, path);
  SaveUserSettings();
}
std::string AfsB3Path() { return REXCVAR_GET(dbz1_afs_b3_path); }
void SetAfsB3Path(const std::string& path) {
  REXCVAR_SET(dbz1_afs_b3_path, path);
  SaveUserSettings();
}
bool ShowFps() { return REXCVAR_GET(dbz1_show_fps); }
void SetShowFps(bool on) {
  REXCVAR_SET(dbz1_show_fps, on);
  SaveUserSettings();
}

void ApplyUserSettingsToSdk() {
  // Internal render scale: sets draw_resolution_scale_x/y (supersampling of
  // the 720p framebuffer). The window stays at 720p; the internal buffer scales.
  SetSdkInt("draw_resolution_scale_x", ResolutionScale());
  SetSdkInt("draw_resolution_scale_y", ResolutionScale());

  // Fullscreen: map friendly mode to the SDK bool. Borderless/exclusive
  // distinction is handled by the launcher when entering fullscreen.
  REXCVAR_SET(fullscreen, REXCVAR_GET(dbz1_fullscreen_mode) != "windowed");

  // VSync: forward to the SDK cvar (resolved by name at runtime).
  SetSdkBool("vsync", REXCVAR_GET(dbz1_vsync));

  // Anisotropic filtering: forward to the shared SDK cvar.
  SetSdkInt("anisotropic_override", REXCVAR_GET(dbz1_anisotropic));

  // MSAA: forward the 2x toggle to the shared SDK cvar.
  SetSdkBool("native_2x_msaa", REXCVAR_GET(dbz1_msaa_2x));

  // Gamma: forward the user correction to the shared SDK cvar (applied on top
  // of the game's gamma ramp by the GPU plugin).
  SetSdkDouble("gamma_override", REXCVAR_GET(dbz1_gamma));

  // Swap post effect (FXAA): map the friendly int to the SDK preset string.
  switch (REXCVAR_GET(dbz1_swap_effect)) {
    case 1:
      SetSdkString("swap_post_effect", "fxaa");
      break;
    case 2:
      SetSdkString("swap_post_effect", "fxaa_extreme");
      break;
    default:
      SetSdkString("swap_post_effect", "none");
      break;
  }

  // Frame cap: caps the host present rate only (never the guest vblank pacing).
  SetSdkInt("frame_cap", REXCVAR_GET(dbz1_frame_cap));

  // Graphics backend: forwarded to the SDK gpu_backend cvar before the GPU
  // plugin loads (OnPreSetup -> LoadGpuPlugin). "auto" maps to D3D12 first.
  SetSdkString("gpu_backend", REXCVAR_GET(dbz1_gpu_backend));

  // Present upscaler (FidelityFX CAS/FSR/FSR2/FSR3) and its quality mode.
  REXCVAR_SET(present_effect, REXCVAR_GET(dbz1_present_effect));
  SetSdkString("present_fsr_quality_mode", REXCVAR_GET(dbz1_fsr_quality));

  // Guest video mode refresh rate: always 60 Hz. This game paces its main loop
  // by the guest vblank count, so raising it makes the game run too fast.
  REXCVAR_SET(video_mode_refresh_rate, 60.0);

  // Region: forward the persisted wrapper to the shared cvar (the runtime uses
  // it to mount game:\us to the selected region's assets folder).
  REXCVAR_SET(dbz1_region, REXCVAR_GET(dbz1_user_region));

  // Language: forward the persisted wrapper to the shared kernel cvar, which
  // the game reads via XGetLanguage / XConfig to pick data_XX.afs.
  REXCVAR_SET(user_language, uint32_t(REXCVAR_GET(dbz1_language)));

  // Japanese audio: forward the persisted wrapper to the shared cvar (the
  // runtime mounts game:\us\adx_us.afs -> adx_jp.afs when enabled).
  REXCVAR_SET(dbz1_audio_jp, REXCVAR_GET(dbz1_user_audio_jp));

  // Audio: master output volume applied at the SDL callback, and the output
  // device selected at audio-driver init (empty = system default).
  SetSdkDouble("master_volume", REXCVAR_GET(dbz1_master_volume));
  SetSdkString("audio_output_device", REXCVAR_GET(dbz1_audio_device));

  // Input: deadzone applied in the SDL input driver, rumble gates vibration,
  // and mnk_mode enables keyboard/mouse controller emulation.
  SetSdkDouble("deadzone", REXCVAR_GET(dbz1_deadzone));
  SetSdkBool("rumble", REXCVAR_GET(dbz1_rumble));
  SetSdkBool("mnk_mode", REXCVAR_GET(dbz1_mnk_mode));

  // MnK keybinds: forward the persisted wrappers onto the shared SDK cvars.
#define DBZ1_FORWARD_KEYBIND(name) \
  REXCVAR_SET(keybind_##name, REXCVAR_GET(dbz1_keybind_##name))
  DBZ1_FORWARD_KEYBIND(a);
  DBZ1_FORWARD_KEYBIND(b);
  DBZ1_FORWARD_KEYBIND(x);
  DBZ1_FORWARD_KEYBIND(y);
  DBZ1_FORWARD_KEYBIND(left_trigger);
  DBZ1_FORWARD_KEYBIND(right_trigger);
  DBZ1_FORWARD_KEYBIND(left_shoulder);
  DBZ1_FORWARD_KEYBIND(right_shoulder);
  DBZ1_FORWARD_KEYBIND(lstick_up);
  DBZ1_FORWARD_KEYBIND(lstick_down);
  DBZ1_FORWARD_KEYBIND(lstick_left);
  DBZ1_FORWARD_KEYBIND(lstick_right);
  DBZ1_FORWARD_KEYBIND(lstick_press);
  DBZ1_FORWARD_KEYBIND(rstick_press);
  DBZ1_FORWARD_KEYBIND(dpad_up);
  DBZ1_FORWARD_KEYBIND(dpad_down);
  DBZ1_FORWARD_KEYBIND(dpad_left);
  DBZ1_FORWARD_KEYBIND(dpad_right);
  DBZ1_FORWARD_KEYBIND(back);
  DBZ1_FORWARD_KEYBIND(start);
#undef DBZ1_FORWARD_KEYBIND

  REXLOG_INFO(
      "dbz1: applied user settings -> resolution={} fullscreen={} vsync={} "
      "anisotropic={} msaa_2x={} frame_cap={} swap_effect={} backend={} present_effect={} "
      "master_volume={:.2f} audio_device='{}' deadzone={:.2f} rumble={} mnk_mode={}",
      REXCVAR_GET(resolution), REXCVAR_GET(fullscreen) ? "true" : "false",
      rex::cvar::Query<bool>("vsync") ? "true" : "false",
      rex::cvar::Query<int32_t>("anisotropic_override"),
      rex::cvar::Query<bool>("native_2x_msaa") ? "true" : "false",
      rex::cvar::Query<int32_t>("frame_cap"),
      rex::cvar::Query<std::string>("swap_post_effect"),
      rex::cvar::Query<std::string>("gpu_backend"),
      rex::cvar::Query<std::string>("present_effect"),
      rex::cvar::Query<double>("master_volume"),
      rex::cvar::Query<std::string>("audio_output_device"),
      rex::cvar::Query<double>("deadzone"),
      rex::cvar::Query<bool>("rumble") ? "true" : "false",
      rex::cvar::Query<bool>("mnk_mode") ? "true" : "false");
}

}  // namespace dbz1::settings
