# Referencia — Ecosistema ReXGlue y aprendizajes para la Fase 1
> Copyright (c) NovaPowers. Released under the MIT License. Firmado por NovaPowers.
>

> Generado 11/08/2026 durante la investigación previa a la Fase 1.
> Doc completa descargada en `rexglue_docs_llms-full.txt.txt` (13.410 líneas).

---

## 1. Contexto del ecosistema (hallazgos de la investigación online)

- **Nuestro proyecto** es el "DBZ Budokai HD Recompiled" de WistfulHopes (107★, 20/02/2026).
  El mismo dev tiene en marcha Raging Blast 2 recomp.
- **ReXGlue** (tomcl7/Tom Clay): SDK de recompilación estática Xbox 360 → C++ nativo.
  Xenia-based, inspirado en XenonRecomp/rexdex. C++23 + Clang 18+. v0.9.0 local.
- **Proyectos hermanos (ReXGlue):**
  - `birabittoh/NocturneRecomp` (318★, Castlevania SOTN XBLA) — **mejor plantilla**:
    mismo esquema config.toml/manifest, scripts, y patrones de settings/launcher.
  - `rexglue/reblue` (Blue Dragon, 160★) — del propio Tom Clay.
  - `rexglue/demo-iruka` — proyecto demo del SDK.
- **NocturneRecomp usa SDK fork nightly** (`sotn-nightly-20260806-9162e3d4`) con hooks que
  **nuestra v0.9.0 NO tiene** (`OnCreateUserSettingsOverlay`, `mod_registry`, `config_path()`,
  `OnLoadXexImage`, etc.). **No actualizar:** v0.9.0 es estable y tiene nuestros fixes locales.
- **Sonic Unleashed Recompiled** (hedge-dev): referencia conceptual de UX (menú de opciones
  navegable con mando, high-res, MSAA, ultrawide, fast-forward), pero usa runtime propio
  (XenonRecomp/XenosRecomp) — su código no encaja directamente.
- ReXGlue tiene **wiki** + docs mintlify + Discord oficial (feedback loop: fixes de la
  comunidad se integran al SDK).

---

## 2. Lo que YA trae el SDK v0.9.0 (¡mucho está hecho!)

### 2.1. SettingsDialog integrado (F4)
`src/ui/overlay/settings_overlay.cpp` — `rex::ui::SettingsDialog`:
- Lista **todos los cvars** del registro, agrupados por categoría (árbol).
- Edición por tipo (bool/int/double/string/combo con constraints).
- Badges de ciclo de vida: `[live]` (hot-reload), `[restart]`, `[init-only]`.
- Keybinds rebindeables en caliente con captura de tecla + detección de conflictos.
- Botón **"Save to config"** → `rex::cvar::SaveConfig(config_path_)`.
- Registrado en `rex_app.cpp:403` con bind F4.

### 2.2. Sistema de keybinds
`include/rex/ui/keybinds.h` — `RegisterBind(name, default_key, desc, callback)`,
`ProcessKeyEvent(e)` en OnKeyDown. Cvars tipo string en categoría "Keybinds" → visibles
y persistibles desde el SettingsDialog. Ya usados para F3 (debug overlay), F4 (settings),
Backtick (console), F7 (achievements).

### 2.3. Cvars ya existentes (definidos en la SDK)
- **Ventana/Video:** `fullscreen`, `resolution` (string), `window_width`, `window_height`,
  `monitor`, `video_mode_width/height/refresh_rate`, `vsync` (en audio/input? — hay uno
  `vsync` definido; NocturneRecomp define el suyo para Vulkan).
- **Presenter:** `present_letterbox`, `present_effect` (CAS/FSR/...), `present_cas_*`,
  `present_fsr_*`, `present_dither`, `present_safe_area_*`, `present_allow_overscan_cutoff`.
- **D3D12:** `d3d12_adapter`, `d3d12_debug`, `d3d12_break_on_error`, `d3d12_bindless`,
  `d3d12_allow_variable_refresh_rate_and_tearing`, `d3d12_submit_on_primary_buffer_end`.
- **Audio:** `audio_mute` (bool), `ffmpeg_verbose`. **NO hay volúmenes por canal** (faltan).
- **Input:** `mnk_mode`, `mnk_sensitivity`, keybinds completos (`keybind_a/b/x/y/...`,
  `keybind_lstick_*`, etc.), `input_backend`, `hid_mappings_file`.
- **GPU/Debug:** `gpu_plugin`, `dump_shaders`, `store_shaders`, `dump_path`,
  `async_shader_compilation`, `render_target_path_d3d12`, etc.

### 2.4. Hooks de ReXApp disponibles en v0.9.0 (rex_app.h:98-238)
`OnPreSetup`, `OnLoadXexImage`, `OnPostSetup`, `OnCreateDialogs`, `OnShutdown`,
`OnConfigurePaths`, `OnFinalizePaths`, `OnConfigureFonts`, `OnPostInitLogging`,
`OnPostLoadXexImage`, `OnPreLaunchModule`, `OnPostLaunchModule`, `OnGuestThreadExit`,
`OnCreateImmediateDrawer`, `OnWindowResized`, `OnWindowPixelSizeChanged`,
`OnWindowCloseRequested`, `OnWindowFocusChanged`, `OnDpiScaleChanged`,
`OnWindowMinimized`, `OnWindowRestored`, `CreateAchievementsOverlay`,
`CreateAchievementNotificationDialog`, `SetupEnvironment`, `ConstructRuntime`,
`SetupPresentation`, `LaunchModule`.

### 2.5. Ciclo de arranque (rex_app.cpp)
`OnInitialize` → `SetupEnvironment()` (paths + LoadConfig del config_path)
→ `SetupPresentation()` (carga gpu_plugin, crea window 1280x720, fullscreen cvar,
presenter, overlays ImGui, OnCreateDialogs) → `ConstructRuntime()` → `LaunchModule()`
→ `OnPreLaunchModule` → `OnPostLaunchModule` → `main_thread->Resume()`.
**Clave para el launcher:** `LaunchModule()` es un método virtual del SDK
(`rex_app.h:238`) que se puede **no llamar** (gatear tras el botón "Jugar") o llamar
diferido. NocturneRecomp no lo usa así, pero la opción existe.

---

## 3. Patrones aprendidos de NocturneRecomp (app header, 08/2026)

- **Cvar propio encima de cvar SDK:**
  ```cpp
  REXCVAR_DEFINE_BOOL(vsync, true, "Video", "Enable vsync");
  REXCVAR_DECLARE(bool, vulkan_allow_present_mode_immediate);
  // En OnPreLaunchModule:
  REXCVAR_SET(vulkan_allow_present_mode_immediate, !REXCVAR_GET(vsync));
  ```
- **Settings de usuario en archivo separado**, cargado DESPUÉS del config del SDK para
  ganar sobre él:
  ```cpp
  bool SetupEnvironment() override {
    nocturne::ApplySettingDefaults();               // defaults antes de cargar config
    if (!rex::ReXApp::SetupEnvironment()) return false;
    if (std::filesystem::exists(user_settings_path()))
      rex::cvar::LoadConfig(user_settings_path());   // user settings ganan
    ...
  }
  std::filesystem::path user_settings_path() const { return user_data_root() / "settings.toml"; }
  ```
- **Título de ventana / icono:** `window()->SetTitle(...)`, `window()->SetIcon(png, size)`.
- **FPS del guest** vía `runtime()->mod_registry()->RegisterTick(...)` (hook de 0.9.0 NO
  tiene mod_registry — usar contador propio en command_processor si hace falta).
- **Pacer de framerate:** hilo propio con steady_clock (frame_pacer) — patrón para el
  frame cap.
- **Overlay settings amigable:** dialog ImGui dedicado (`CreateSettingsDialog`) con
  opciones nativas (no cvars crudos).

---

## 4. Decisiones para la Fase 1 en NUESTRO proyecto

1. **NO actualizar el SDK** (v0.9.0 estable + fixes locales). Trabajar sobre él.
2. **Launcher integrado** en el mismo exe (pantalla ImGui pre-juego) usando los hooks
   existentes. Para gatear el arranque: no llamar `LaunchModule()` hasta pulsar "Jugar".
3. **Archivo de usuario:** `dbz1_user.toml` junto al exe (o `user_data/dbz1/settings.toml`
   siguiendo el patrón Nocturne). Cargado tras el config principal.
4. **Capa friendly sobre cvars:** dialog ImGui propio (pestañas) que mapea opciones
   amigables → cvars del SDK. El SettingsDialog F4 queda para "avanzado".
5. **Faltan por crear (cvars nuevos):** volúmenes master/music/sfx/voice, frame cap,
   gamma/brillo, dev mode switches.
6. **F10 Dev mode:** overlay con switches en caliente: diag logs on/off, resolución
   interna por pruebas, toggles de efectos, etc.

---

## 5. Fuentes

- Docs ReXGlue (completa): `docs/referencias/rexglue_docs_llms-full.txt.txt`
- Índice: `docs/referencias/rexglue_docs_llms.txt.txt`
- SDK local: `rexglue-sdk/` (v0.9.0), en especial `src/ui/rex_app.cpp`,
  `src/ui/overlay/settings_overlay.cpp`, `include/rex/ui/*`, `include/rex/cvar.h`.
- NocturneRecomp: https://github.com/birabittoh/NocturneRecomp (patrón app).
- Sonic Unleashed Recompiled: referencia UX.
- ReXGlue wiki: https://github.com/rexglue/rexglue-sdk/wiki · Discord: https://discord.gg/CNTxwSNZfT
