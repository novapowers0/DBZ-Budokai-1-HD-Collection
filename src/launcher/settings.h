// dbz1 - User settings layer for the launcher / quality-of-life features.
//
// User-facing cvars live in their own file (dbz1_user.toml) so the advanced
// SDK cvars in dbz1_config.toml are never mixed with player options. This
// layer defines the cvars, loads/saves them, and maps friendly options onto
// the SDK's own cvars (resolution, fullscreen, vsync, ...).

#pragma once

#include <filesystem>

namespace dbz1::settings {

// CVar accessors for the launcher UI (defined in settings.cpp).
// Model pipeline source archives (empty = auto-detect).
std::string AfsB1Path();
void SetAfsB1Path(const std::string& path);
std::string AfsB3Path();
void SetAfsB3Path(const std::string& path);

// Optional FPS overlay (shown in-game in a small corner window).
bool ShowFps();
void SetShowFps(bool on);

// Load dbz1_user.toml (no-op if it does not exist). Must be called after
// rex::cvar::LoadConfig for the SDK config so user values win.
void LoadUserSettings();

// Write all user cvars to dbz1_user.toml.
void SaveUserSettings();

// Absolute path of the user settings file (next to the executable).
std::filesystem::path UserSettingsPath();

// Apply the user video cvars to the SDK's resolution/window cvars. Called
// before window creation (in OnConfigurePaths) so they take effect at boot.
void ApplyUserSettingsToSdk();

// Internal render scale (1x-4x supersampling of the 720p framebuffer).
// Applied at startup via draw_resolution_scale_x/y.
int32_t ResolutionScale();

// Set the internal render scale (1/2/3/4).
void SetResolutionScale(int32_t scale);

}  // namespace dbz1::settings
