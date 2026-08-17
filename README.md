# DBZ Budokai 1 HD Collection — Recompile ReXGlue + Modding

Copyright (c) 2026 **NovaPowers**. Released under the MIT License (see `LICENSE`).

Recompilación de Dragon Ball Z Budokai 1 HD (Xbox 360) con el
[ReXGlue SDK](https://github.com/rexglue/rexglue-sdk), con sistema de
mods de modelos validado en juego.

> 📘 **Documentación principal**:
> - **Viabilidad del proyecto** (qué funciona y qué no): `docs/estado/VIABILIDAD_PROYECTO.md`
> - **Tutorial de mods paso a paso**: `docs/tutoriales/TUTORIAL_MODS.md`
> - **Formato de mods (técnico)**: `docs/tutoriales/FORMATO_MODS.md`
> - **Catálogo de personajes→bins**: `docs/referencias/PERSONAJES_BINS.md`

---

## ⚠️ Aclaración sobre el origen

Este proyecto se **rehízo desde cero** sobre el [ReXGlue SDK](https://github.com/rexglue/rexglue-sdk).
El repositorio [`WistfulHopes/DBZ1`](https://github.com/WistfulHopes/DBZ1) se
tomó **solo como referencia** (para entender la API del SDK y el flujo del
recompile), pero **NO se usó como base ni se copió su código**. El launcher,
el sistema de mods, la gestión de regiones EU/US y todas las herramientas de
`mod center hd/` son trabajo original de **NovaPowers**.

---

## Regiones EU/US

El juego es compatible con **ambas regiones** sin necesidad de un ejecutable
distinto:

- Los `.xex` europeo y americano son **byte-idénticos** (mismo binario) — la
  región no está en el ejecutable, sino en los **datos**.
- La región se elige en el launcher (pestaña *Video* → *Region*: `USA` o
  `EU (PAL)`), o vía cvar `dbz1_region`.
- Al cambiar de región se monta la carpeta de assets correspondiente
  (`assets/us` o `assets/eu`) en `game:\us`:
  - `assets/us/`: `data_us.afs`, `data_sp.afs`, `data_fr.afs`, `adx_us.afs` (voces EN)
  - `assets/eu/`: `data_en.afs`, `data_fr.afs`, `data_ge.afs`, `data_it.afs`,
    `data_sp.afs`, `adx_jp.afs` (voces JP)
- El idioma se elige en la pestaña *Video* → *Language* (usa el `data_XX.afs`
  correspondiente a la región).
- El guardado es compartido EU/US (independiente de la región montada).

---

## Estado (17/08/2026)

| Técnica | Estado |
|---|---|
| Swap nativo B1→B1 | ✅ **100% funcional** (validado: CHZ, Android 19) |
| Port B3 HD→B1 HD | ✅ **100% funcional** (validado: Dr. Gero) |
| Port PS2→HD | ⚠️ **VIABLE** — entra en combate sin crash, modelo deforme por decimación |
| Port de movesets | ❌ No viable sin RE completa (#ACM) |
| GameCube como fuente | ❌ Formato distinto (#ACO/#ACB) |

Herramientas: `mod center hd\` (swaps, ports, analizadores, exportadores).
Mods validados conservados: `mods\test_chz_ps2_texfix` (port PS2→HD),
`mods\test_gero_b3_to_b1_v2` (port B3→B1).

---

## Setup / Build

Requisitos: un compilador C++23 y CMake ≥ 3.25, y el [ReXGlue SDK](https://github.com/rexglue/rexglue-sdk)
(compilado o pre-built) disponible en el entorno (variable `REXSDK_DIR` o una
carpeta `rexglue/` junto al proyecto).

> **Nota sobre copyright**: este repositorio **no incluye los assets del
> juego**. Debes extraer los AFS de tu copia legal de *Dragon Ball Z: Budokai
> HD Collection* (Xbox 360) a la carpeta `assets/`. El código recompilado
> (`generated/`) también se genera a partir de tu `.xex`; no se distribuye.

1. Preparar los assets: extraer a `assets/` los `data_*.afs` del juego
   (`data_us`, `data_sp`, `data_fr`, `data_en`, `data_ge`, `data_it`).
   **No se requiere una ruta concreta**: todos comparten la misma numeración
   de bins y cualquiera sirve para los swaps.
2. Ejecutar el codegen (genera `generated/` a partir de `assets/default.xex`
   + `dbz1_config.toml` + `dbz1_manifest.toml`):
   ```
   cmake -S . -B out/build/win-amd64-release --preset win-amd64-release
   cmake --build out/build/win-amd64-release --target dbz1_codegen
   cmake --build out/build/win-amd64-release
   ```
3. **Lanzar**: `out\build\win-amd64-release\dbz1.exe`
   (NO usar el dbz1.exe de la raíz — es un build viejo).
4. Logs: `out\build\win-amd64-release\logs\dbz1_NNN.log`.

### Rutas portables

- Las herramientas detectan los AFS desde `assets/` o desde la raíz que les
  pases en el launcher (pestaña Mods → Archivos fuente).
- El proyecto B3 se localiza con la variable `DBZ3_ROOT` o como carpeta
  hermana `DBZ Budokai 3 HD Collection`.
- `xbcompress.exe`/`xbdecompress.exe` viven en `tools/` (o vía
  `DBZ1_XBCOMP_DIR`).

---

## Mods

Los mods viven en `mods/<nombre>/` y reemplazan entradas del AFS por
overlay (sin tocar los AFS originales):

```
mods/<mod>/us/data_sp.afs/2450/geom.bin   # modelo del slot 2450
mods/<mod>/us/data_sp.afs/2451/tex.bin    # textura del slot 2451
mods/<mod>/.disabled                      # si existe, el mod está OFF
```

> El override se instala en **todos** los `data_*.afs` de personaje, de modo
> que funciona independientemente del AFS concreto que elija el juego según
> región/idioma.

Crear un mod: ver `docs/tutoriales/TUTORIAL_MODS.md`.

---

## Créditos

- [ReXGlue](https://github.com/rexglue/rexglue-sdk) por las herramientas de
  recompilación.
- [WistfulHopes/DBZ1](https://github.com/WistfulHopes/DBZ1) como **referencia**
  de la API del SDK (no usado como base).
- Comunidad de modding de Budokai (herramientas y modelos de referencia).
- **NovaPowers** — autor del sistema de mods, launcher y herramientas de
  este proyecto.
