# SESIÓN 14 — Bundle del Model pipeline en el release (v0.5.1)

> Copyright (c) NovaPowers. Released under the MIT License. Firmado por NovaPowers.
> 2026-08-20.

## Problema

El usuario puede pensar que "no le funcionan los mods" porque el zip del
release NO incluía la toolchain de `mod center hd`. Resultado: el **Model
pipeline** (Scan characters / Port B3→B1 / Swap B1→B1) del launcher fallaba
para el usuario final — el launcher invoca `python mod center
hd/launcher_mod_pipeline.py` y, sin esa carpeta, no encontraba el script ni
generaba el catálogo.

## Aclaración: hay DOS niveles de "mods"

1. **Aplicar/cargar mods ya creados** (pestaña Mods: listar, activar/
   desactivar, editar manifest; y el runtime leyendo `mods/` vía afs.cpp) —
   **autocontenido en el exe + rexruntime.dll**, NO necesita Python ni
   "mod center hd".
2. **Crear mods con el Model pipeline** — **sí necesita** la toolchain Python
   + `tools/` (xbcompress) + `assets/` (+ `data_cmn.afs` del B3 para Port).

## Dependencias runtime reales del pipeline (trazadas por imports/subprocess)

`mod center hd/` (8 scripts, ~unos pocos cientos de KB):
- `launcher_mod_pipeline.py` (orquestador, invocado por el C++)
- `paths.py`, `characters_db.py`, `skin_colors.py`
- `swaps/swap_b1.py`
- `conversores/install_b3_to_b1.py` + `conversores/port_b3_to_b1_v2.py`
- `analizadores/extract_amb_awo.py`

`tools/` (5 archivos): `xbcompress.exe`, `xbdecompress.exe`, `MSVCP71.dll`,
`MSVCR71.dll`, `xbdm.dll` (sin las DLLs → 0xC0000135).

El resto del "mod center hd" (~1.7 GB, 4376 archivos) es tooling de análisis/
RE y NO se distribuye.

## Validación (layout empaquetado limpio)

- `paths.find_tool('xbcompress.exe')` resuelve a `<root>/tools/xbcompress.exe`.
- `catalog` → **OK: 109 modelos B1 + 183 B3** (coincide con el catálogo
  existente).
- `swap --dry` → resuelve `swap_b1.py` y muestra el comando completo.
- `port --bin 176 --dry` → extrae el AMB y resuelve
  `install_b3_to_b1.py ... --tint-skin auto`.

## Release v0.5.1

- El zip incluye: `dbz1.exe` + `rexruntime.dll` + `rexgpu-xenos.dll` +
  `amd_fidelityfx_dx12.dll` + `TracyClient.dll` + `mod center hd/` (runtime
  subset) + `tools/` + `RELEASE_README.md`.
- El README documenta los dos niveles de mods y los requisitos del pipeline
  (Python 3 + `assets/` + B3 para Port), y avisa de que todo vive junto al
  `.exe` (no mover solo el `.exe`).
- Cambios de código en esta sesión: ninguno en C++ (v0.5.1 es solo empaquetado
  + documentación). El exe es el mismo build que v0.5.0 con el fix UI de CAS/
  Vulkan [Experimental].
