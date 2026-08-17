# HOJA DE RUTA — DBZ Budokai HD Collection
> Copyright (c) NovaPowers. Released under the MIT License. Firmado por NovaPowers.
>

> Estado del proyecto y fases. Actualizado: 12/08/2026.

---

## Fase 0 — Estabilización (En curso)

- ✅ Intro, menús, combate jugable; module transitions; logros; shader storage; guardado.
- ✅ **Startup rápido (~0.63s a launcher shown, 13/08):** el "1.5s" era el gamepad SDL
  bloqueante; arreglado (input_backend=xinput + gamepad async). Cuello de botella actual =
  device D3D12 + DXGI (~412ms de 629ms), inherente a D3D12.
- 🔧 Black screens en transiciones (presentaciones/cinemáticas) → fase final de depuración.
- 🔧 Shader storage cache: YA es rápido (22KB, 2-40ms); el retraso era el gamepad.

## Fase 1 — Calidad de vida y Launcher (✅ casi todo)

| Feature | Estado |
|---|---|
| Launcher GUI Windowed/Borderless | ✅ (exclusive no soportado) |
| MSAA 2x, VSync, Frame cap, 720p/1080p/1440p/2160p, FXAA, refresh 60-165 | ✅ cableados |
| Anisotropic + Gamma (0.5-2.0 → cvar gamma_override → gamma ramp guest) | ✅ |
| Master volume + Output device selector (cvar audio_output_device → SDLAudioDriver) | ✅ |
| Audio por canal music/sfx/voice | ⛔ Inviable (el guest pre-mezcla) |
| Deadzones, Vibración, MnK (mnk_mode + 20 keybinds dbz1_*; defaults A=J B=K X=I Y=U LT=Q RT=E LS=Shift RS=F) | ✅ |
| Persistencia dbz1_user.toml | ✅ LoadConfig/SaveConfig |

> ⚠️ **Arquitectura (importante):** los cvars compartidos launcher↔runtime deben definirse
> SOLO en archivos compilados en `rexruntime.dll` (`src/system/*`, `src/audio/sdl/*`,
> `src/input/*`). `rexui` se enlaza en exe Y DLL → un cvar en `src/ui/` genera dos storages
> y el launcher no escribe el que el runtime lee. `video_mode_refresh_rate` ya se movió a
> `src/system/video_mode_refresh_rate_flag.cpp`.

## Fase 2 — Multi-región (✅ US/EUR)

- ✅ EUR: `default.xex` y `default_eur.xex` son **byte-idénticos**; el juego hardcodea
  `game:\us\` y construye nombres por `xeXGetGameRegion`. Fix: región=eur→PAL(0xFF0000);
  montar assets EUR en `game:\us`; redirect data_us→data_en para inglés.
- ✅ Layout EUR: `data_cmn.afs` + `data_eng/fra/spn/ger/ita.afs` + `adx_usa/adx_jpn.afs`.
- ✅ Idiomas EN/FR/ES/DE/IT (user_language cvar).
- ✅ **Audio EUR resuelto (13/08):** el pack EUR (`adx_jp.afs`, 1531) difiere del US (1541)
  en orden/contenido; el motor indexa por posición calibrado al US. Fix en
  `virtual_file_system.cpp`: para EUR, el pack de audio se resuelve al US (`assets/us/adx_us.afs`).
  El mod og_music funciona.
- ✅ **60Hz fijado:** la lógica se pacea por contador de vblank → valores >60 aceleran.
  Eliminado el selector >60.
- 📋 NTSC-J: más adelante.

## Fase 3 — Modding Ecosystem

| Feature | Estado |
|---|---|
| Mod loader override por entrada AFS | ✅ **FUNCIONA (13/08, validado)** — hook HostPathFile::ReadSync redirige entradas a `mods/<mod>/us/<afs>/<índice>` (archivo o carpeta). Bugs corregidos: negative cache por contenedor + condición invertida en AfsFindModOverride. Validado con swap de música (adx_us.afs 111=opening, 1255=menú). Handles cacheados + negative cache → el audio streaming no se ralentiza. |
| Subcarpetas por mod + toggle | ✅ `mods/<mod>/us/<afs>/<índice>`; activación por `.disabled` DENTRO de la carpeta |
| Model swaps HD | ✅ **GRAN LOGRO (16/08)**: swap de bins HD B1→B1 **100% funcional** (Android 19 X19G→Tenshinhan). Clave: **par geom (#AWO) + tex (#AZT) del MISMO personaje**, bin completo instalado tal cual. El runtime dibuja el bin completo (mesh group, IB, bones, UVs) SIN validar conteos del slot (46 bones/15 AWG/4601 verts en slot de 42/23/4272). Herramienta: `swaps/swap_b1.py`. Ver `docs/tutoriales/MODEL_SWAPS_METODOLOGIA.md`. |
| Port B3→B1 (bins) | 🔬 NUEVO ENFOQUE (16/08) — el swap B1→B1 demostró que el runtime usa el bin completo tal cual y NO exige conteos fijos → el port B3→B1 solo necesita convertir sellos (flag +0x0C→0x2, type2 0x29BD/0x1B5→0x1BD, bones remap por labels) + **AZT del MISMO personaje**. El crash del port Gero era tex mismatch, no el mesh group. Herramienta: `conversores/port_b3_to_b1.py`. Ver `docs/re/SESION9_MODEL_SWAPS_B1_B1.md`. |
| Texture packs por hash XXH3 | 🔧 Hash detection + file lookup listos; sustitución real de datos requiere DDS loader (to-do) |
| Mods por entrada (música/menús) | ✅ adx_us.afs (1541 pistas) validado; reemplazo ADX sin crash. AFS/AFL/LZX formato documentado. |
| Hot-reload | 🔧 Botón "Reload mods" invalida caché; los mods aún requieren reinicio |
| API scripting Lua/C# | 📋 Pendiente (último) |

> **Ecosistema de modding B1 investigado (12/08):** Budokai Modding Tool V1.5, AMT Tools,
> Animation Editor, Bone Addition Tool, AFS Packer/Explorer. Modelos `.bin`, texturas
> `.amt`, animaciones `.amo`. Cada personaje = ~12 archivos en AFS (AMO/AMT/AMM/BSK/BCM/
> BFC/SPX/DBS_*). Ver INVESTIGACION_MODDING_BUDOKAI.md.
> Camino más rápido = override de `.afs` completo; meta = override por entrada.

## Fase 4 — Features avanzadas (opcional, largo plazo)

Save states (F5/F9 + thumbnails), Rewind, Cheats (.cht/.pnach), Achievements custom,
Netplay/Rollback, TAS tools, Debugger integrado, Profiling/telemetría overlay.

## Notas históricas clave

- **Blackout del duelo — DIAGNOSTICADO (13/08):** es la animación de entrada (vsM
  casi-identidad diagonal 240f). Fix probado `dbz1_force_clip_disabled` (forzar
  clip_disable=true) NO eliminó el blackout → se revirtió. Documentado, no bloquea.
  Ver INVESTIGACION_BLACKOUT_DUELO.md.
- **Comparación con otros recomp:** svr07 usa el MISMO runtime GPU (rexglue-sdk-yukes
  v0.7.3 → command_processor/render_target_cache/texture_cache byte-idénticos a rexglue
  0.9.0) → el blackout NO es bug del runtime GPU compartido. Sonic Unleashed usa
  XenonRecomp + dxcompiler; Zelda 64 es port N64.
- **Frame cap:** primero arreglado (guard `>0.0` sobre acumulador en 0 = no-op), luego
  re-diseñado a SOLO la ruta de repaint del UI thread (el present del guest siempre ocurre).
- **120 Hz conseguido (12/08):** sin speedup en combate (no va x2), sin comportamientos
  raros; quedan microstutters leves (compilación de shaders nuevos, se calienta la cache).
- **Ventana fuera de pantalla:** resolución >monitor rompía el launcher → clamp a límites
  del display (no fullscreen) + presets fijos 720p/1080p/1440p/2160p (sin slider 100-400%).
- **Hz del monitor:** el guest vblank está fijado a 60Hz; cambiar Hz del monitor con la app
  abierta puede provocar device loss D3D12 → reiniciar tras cambiar resolución/Hz.
- **Microstutters:** código TEMP DEBUG en pipeline_cache.cpp forzaba dump_shaders +
  d3d12_dxbc_disasm en cada compilación → eliminado (dump solo explícito).
- **Combo anisotrópico:** off-by-one corregido (índice = cvar+1).
- **Launcher centrado:** panel centrado en la ventana real (no fijo 1280x720).
- **Binario de trabajo:** `build/Release/dbz1.exe` (ver docs/ESTRUCTURA.md).