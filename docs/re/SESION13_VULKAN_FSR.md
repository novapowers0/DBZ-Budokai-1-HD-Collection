# SESIÓN 13 — Vulkan + FSR3 (FidelityFX) integrados (v0.5.0)

> 2026-08-20. Firmado por NovaPowers (MIT).
> Objetivo: activar el backend **Vulkan** y los **upscalers FidelityFX
> (CAS/FSR/FSR2/FSR3)** en Windows como base para la futura versión Linux
> (la SDK ReXGlue ya trae Vulkan nativo y FidelityFX de serie).

## Resumen

La SDK ReXGlue ya soportaba Vulkan (`REXGLUE_USE_VULKAN`) y el upscaler
FidelityFX (`REXGLUE_ENABLE_FIDELITYFX`) de serie; solo había que activarlos y
arreglar la coexistencia de ambos backends de UI con un ffx-api single-backend.
El runtime B1 ahora arranca con **D3D12** (por defecto, con FSR2/FSR3 temporal)
o **Vulkan** (seleccionable en la pestaña Video del launcher), y expone el
selector de upscaler + calidad FSR.

## Cambios

### SDK (`rexglue-sdk/`)

- **`src/ui/CMakeLists.txt`**: guards per-backend de FidelityFX. ffx-api se
  compila para UN backend (`FFX_API_BACKEND`), pero D3D12+Vulkan compilan
  juntos en Windows. Los presenters usaban el MISMO guard
  `REX_HAS_FIDELITYFX_RUNTIME` → sin el parche, un build FidelityFX de un solo
  backend no enlazaba el otro presenter. Ahora:
  - `REX_HAS_FIDELITYFX_DX12=1` si existe `amd_fidelityfx_dx12`.
  - `REX_HAS_FIDELITYFX_VK=1` si existe `amd_fidelityfx_vk`.
  - `REX_HAS_FIDELITYFX_RUNTIME` queda SOLO en `presenter.cpp` (código común
    backend-agnóstico: parseo de quality mode, etc.).
- **`src/ui/d3d12/d3d12_presenter.cpp`**: guards → `REX_HAS_FIDELITYFX_DX12`.
- **`src/ui/vulkan/vulkan_presenter.cpp`**: guards → `REX_HAS_FIDELITYFX_VK`.
- **`src/ui/rex_app.cpp`** (espejo en `rexglue/share/rexglue/rex_app.cpp`,
  que es la copia que se compila en dbz1): nueva cvar
  `REXCVAR_DEFINE_STRING(gpu_backend, "auto", "GPU", ...)` con lifecycle
  `kInitOnly`. En `SetupPresentation()`:
  ```cpp
  std::string backend = REXCVAR_GET(gpu_backend);
  if (backend == "auto") backend = "any";
  config_.graphics = rex::system::LoadGpuPlugin(config_.gpu_plugin, backend);
  ```
  `LoadGpuPlugin(name, backend="any")` (ya existía en `gpu_plugin_loader.cpp`);
  el plugin `rexgpu-xenos` (`plugin_main.cpp`) elige: `"any"`→D3D12 primero,
  `"d3d12"`, `"vulkan"`.

### Build de la SDK

```
cmake -S rexglue-sdk -B rexglue-sdk/out/build/win-amd64 -G "Ninja Multi-Config" \
  -DCMAKE_C_COMPILER="C:/Program Files/LLVM/bin/clang.exe" \
  -DCMAKE_CXX_COMPILER="C:/Program Files/LLVM/bin/clang++.exe" \
  -DREXGLUE_USE_D3D12=ON -DREXGLUE_USE_VULKAN=ON \
  -DREXGLUE_ENABLE_FIDELITYFX=ON -DREXGLUE_FIDELITYFX_BACKEND=dx12
cmake --build rexglue-sdk/out/build/win-amd64 --config Release --target rexruntime rexgpu-xenos
```

- **Nota build (a)**: `ffx-api/src/resource/ffx_api_dll.rc` viene en
  **UTF-16-LE** y `llvm-rc` falla ("UTF-16 (LE) byte order mark detected").
  Fix: convertir a UTF-8 sin BOM (se recompila el `.rc` con `-x c -E` +
  `llvm-rc`). Es una conversión in-place del archivo descargado en `_deps/`.
- **Nota build (b)**: warnings de `CMAKE_OBJECT_PATH_MAX` (rutas largas) en
  FidelityFX/SPIRV que NO rompen el build.
- **Salida**: `rexglue-sdk/out/win-amd64/Release/rexruntime.{dll,lib}` y
  `rexgpu-xenos.dll`; `rexglue-sdk/bin/amd_fidelityfx_dx12.dll` (el backend
  dx12 se enlaza como .lib dentro del ffx-api).

### Copia al proyecto

| Desde | A | Para |
|---|---|---|
| `out/win-amd64/Release/rexruntime.dll` | `rexglue/bin/`, `out/build/win-amd64-release/` | runtime |
| `out/win-amd64/Release/rexruntime.lib` | `rexglue/lib/` | link de dbz1 |
| `out/win-amd64/Release/rexgpu-xenos.dll` | `rexglue/bin/`, `out/build/win-amd64-release/` | plugin GPU |
| `rexglue-sdk/bin/amd_fidelityfx_dx12.dll` | `rexglue/bin/`, `out/build/win-amd64-release/` | **FFX runtime** |

⚠️ `rexruntime.dll` IMPORTA `amd_fidelityfx_dx12.dll` (verificado en la tabla
de imports) → el DLL de FidelityFX es OBLIGATORIO junto al exe, también en el
zip del release.

### Launcher (`src/`)

- **`launcher/settings.cpp`**: cvars de usuario (categoría `DBZ1/Video`,
  lifecycle `kRequiresRestart`, se persisten a `dbz1_user.toml`):
  - `dbz1_gpu_backend`: `auto`/`d3d12`/`vulkan` (default `auto`).
  - `dbz1_present_effect`: `bilinear`/`cas`/`fsr`/`fsr2`/`fsr3` (default
    `bilinear`, igual que la SDK).
  - `dbz1_fsr_quality`: `auto`/`nativeaa`/`quality`/`balanced`/`performance`/
    `ultra_performance` (default `auto`).
  - Forward en `ApplyUserSettingsToSdk()`: `SetSdkString("gpu_backend", ...)`
    (por nombre, no linkeable), `REXCVAR_SET(present_effect, ...)` (símbolo
    linkeable), `SetSdkString("present_fsr_quality_mode", ...)`.
- **`launcher/launcher_state.cpp`** (pestaña Video, tras FXAA):
  - Combo "Graphics backend" (Auto/D3D12/Vulkan).
  - Combo "Upscaler" (Bilinear/CAS/FSR1/FSR2/FSR3).
  - Combo "FSR quality" (solo visible con FSR/FSR2/FSR3).
  - Declaraciones REXCVAR_DECLARE de las 3 cvars nuevas.

## Validación (runtime, RTX 4070 SUPER)

| Escenario | Config | Resultado |
|---|---|---|
| D3D12 default | `gpu_backend=auto`, `present_effect=bilinear` | plugin 'xenos' cargado, DXGI adapter RTX 4070 SUPER, GPU init OK, sin crash |
| Vulkan | `gpu_backend=vulkan` | instancia **Vulkan 1.4.357**, device **1.4.341** (RTX 4070 SUPER), sin crash |
| FSR3 | `gpu_backend=auto`, `present_effect=fsr3` | warning "experimental temporal upscaler path" → rama FSR3 activa, sin crash |

Log de arranque (12s) limpio en los 3 casos: `Runtime initialized successfully`,
`Loading XEX image: game:\default.xex`.

**Pendiente**: verificación VISUAL del render en juego con Vulkan y con FSR3
(la validación fue de inicialización + ausencia de crash).

## Nota: dbz1_user.toml corrupto

`dbz1_user.toml` fallaba al parsear ("expected hex digit, saw 's'") porque las
rutas AFS se guardaron con backslashes (`C:\Users\...`) → `\U` se lee como
escape unicode. Fix local: rutas con `/`. Es un caso del bug de persistencia ya
conocido (lección 31).

## Base para Linux (Fase 2)

- El mismo build SDK en Linux compila con `REXGLUE_USE_VULKAN=ON` por defecto
  y `FIDELITYFX_BACKEND=vk` → **FSR3 temporal en Vulkan nativo**.
- Portar al launcher los 2 trozos Win32: `CreateProcessW`+pipes
  (`launcher/mod_pipeline.cpp`) y `GetOpenFileNameW` (`launcher_state.cpp`);
  `main.cpp` ya está guardado con `#if REX_PLATFORM_WIN32`.
- CI ready-to-play: patrón de `PROYECTOS IA\Bloody Roar 2\LINUX_BUILD_GUIDE.md`
  (repo privado `generated/` + PAT + workflow `workflow_dispatch`).

## Archivos tocados

- `rexglue-sdk/src/ui/CMakeLists.txt`
- `rexglue-sdk/src/ui/d3d12/d3d12_presenter.cpp`
- `rexglue-sdk/src/ui/vulkan/vulkan_presenter.cpp`
- `rexglue-sdk/src/ui/rex_app.cpp` = `rexglue/share/rexglue/rex_app.cpp`
- `src/launcher/settings.cpp`
- `src/launcher/launcher_state.cpp`
- `rexglue-sdk/out/build/win-amd64/_deps/fidelityfx-src/ffx-api/src/resource/ffx_api_dll.rc`
  (convertido UTF-16→UTF-8, in-place en el fetch)