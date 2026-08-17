# PLAN — QoL, Widescreen y Launcher de Mods
> Copyright (c) NovaPowers. Released under the MIT License. Firmado por NovaPowers.
>

> 2026-08-17. Fase nueva tras consolidar los ports de modelos (B3→B1 100%
> funcional, vía viable) y descartar el port de movesets (lección 13).
> Contexto: `docs/planes/HOJA_DE_RUTA.md`.

---

## Fase A — Quality of Life (QoL)

| # | Tarea | Estado | Notas |
|---|---|---|---|
| A1 | **Crash dumps pequeños** | ✅ hecho | `src/main.cpp` SetupCrashHandler: `MiniDumpWithFullMemory` → `MiniDumpNormal` (4GB → ~MB). **Compilado y en el build.** Limpiados 5 dumps (~20GB). |
| A2 | Recompilar `dbz1.exe` con A1 + launcher nuevo | ✅ | Build OK (solo warning pre-existente `localtime`). |
| A3 | Limpieza automática de logs/dumps viejos | ✅ | `CleanupOldArtifacts()` en `main.cpp`: retiene los 10 últimos `logs/dbz1_*.log` y los 3 últimos `crash_*.dmp` al arrancar (OnPostSetup). |
| A4 | Hot-reload de mods real (sin reinicio) | 🔧 | El toggle y el override VFS resuelven en open-time; reiniciar sigue siendo necesario para que el juego relea los bins de personaje. |
| A5 | **Nombres/descripciones descriptivos de mods** | ✅ | `manifest.txt` (key=value) en cada mod: `name/description/author/version/type/source/target`. Inferencia automática de tipo (port_b3/swap_b1/moveset/audio/data) y conteo de archivos. Creados manifests para los 15 mods del proyecto. |
| A6 | **UI del launcher de mods mejorada** | ✅ | Tabla ImGui: checkbox de estado, título legible, descripción, ruta origen→destino, badge de tipo con color, indicador ON/OFF, tooltip con detalles, resumen "N mods (M enabled)". |

---

## Fase B — Widescreen

### ✅ Investigación completada (17/08) — conclusiones

1. **El combate YA es 16:9 nativo**: el HD Collection original (X360/PS3, 2012)
   renderiza el combate en 16:9 real (las pantallas de duelo se extendieron de
   4:3 a 16:9). El framebuffer guest es **1280×720** → en un monitor 16:9 no
   hay barras. **No hay nada que parchear para 16:9.**
2. **Menús y cutscenes son 4:3 con bordes decorativos** (no barras negras):
   así lo diseñó el HD original (bordes minimalistas). Fandom/Reviews lo
   confirman ("anything outside of battle gameplay is displayed in 4:3").
   Hacerlos 16:9 reales = rehacer la UI (modding de assets), no un parche de
   runtime.
3. **Técnica de la comunidad PCSX2 (sergx12/Arapapa)**: los pnach de
   widescreen buscan en el código del juego el aspect (1.3333→1.7777) y el
   FOV. Aplica a juegos PS2 4:3. Para el HD (X360) no hay pnach de la
   comunidad porque ya es 16:9 nativo.
4. **Rexglue recompilados (svr07/Sonic, etc.)**: los juegos X360 son nativos
   16:9; el recompilado presenta el framebuffer guest con upscaler FidelityFX
   (`D3D12Presenter` en rexglue-sdk). La swap chain usa el tamaño de la
   ventana; el upscaler escala el framebuffer 16:9 → en ventana 16:9 perfecto.
5. **Ultrawide (21:9)**: requeriría (a) que el guest renderice más ancho que
   1280 (parchear viewport/FOV de cámara en `generated/dbz1_recomp.*.cpp`,
   ~38MB de código guest recompilado) y (b) configuración del upscaler. RE
   profunda del motor, fuera del alcance inmediato.
6. **Cheat Table del B3 HD (local)**: solo offsets del roster PS3 (cambiar
   personaje), sin FOV/aspect → no útil para widescreen.

### Decisión

El widescreen 16:9 ya está resuelto por el juego (combate). El trabajo útil
restante es **confirmar empíricamente** que el usuario ve el combate sin
barras en su monitor y, si quiere ultrawide, asumir la RE del motor guest.


---

## Fase C — Launcher de Mods (integración UI de los pipelines)

Estado actual: los pipelines funcionan por CLI (`swap_b1.py`, `install_b3_to_b1.py`)
y el launcher solo lista mods con toggle `.disabled`. Objetivo: **generar y
gestionar mods desde la UI**.

### C1 — Catálogo de personajes (base para todo)

✅ **Hecho**: `launcher_mod_pipeline.py catalog` escanea:
- B1 `data_sp.afs` → 26 personajes jugables (labels `XGOK_BODY`, `XTSH_BODY`...)
  con slots geom/tex/acm (pares del `scan_catalog` de swap_b1).
- B3 `data_cmn.afs` (proyecto hermano) → 56 personajes (contenedores `#AMB` con
  `*_BODY`; el AMB contiene AWO+AZT).
- Salida: `mod center hd/cache/characters.cat` (texto simple,
  `juego|label|nombre|slot_geom|slot_tex|slot_acm|slot_csk|verts|awgs`).
- Filtro: prefijos de personaje conocidos (normaliza `X` inicial, mapea
  `XGOK→Goku`...) y descarta efectos/escenarios (`EFT*`, `BACK`, `XBB*`...).

### C2 — Apartado "Port B3 → B1"

✅ **Hecho** (UI + orquestador): en la pestaña Mods → "Model pipeline":
- Combo "Modelo B3 (origen)" (catálogo B3) + combo "Personaje B1 (destino)".
- Botón "Portar modelo B3 -> B1" → `launcher_mod_pipeline.py port --b3 <label>
  --dest <slot> --tex <slot> --mod <name>`:
  1. Extrae el `#AMB` del bin del B3 (por label), descomprime.
  2. Extrae `#AWO` + `#AZT` del AMB (`extract_amb_awo.py`).
  3. `install_b3_to_b1.py` (port v2 + compresión + instalación + activación).
- Ejecución asíncrona (`ModPipeline` en C++): lanza `python` con `_popen` en un
  hilo, captura el output en la UI ("Working..."). Validado con `--dry`
  (Gero X20G_BODY → 2450/2451: extrae AMB 91 y arma el plan).

### C3 — Apartado "Model swap B1 → B1"

✅ **Hecho**: combos "Origen"/"Destino" (solo personajes B1 con slot geom real) +
botón "Swap B1 -> B1" → `launcher_mod_pipeline.py swap --origen <label>
--dest <slot> --tex <slot> --mod <name>` → `swap_b1.py`. Solo personajes con
geom ≠ 0 son elegibles como origen.

### C4 — Gestión de mods mejorada

✅ **Hecho** (ver Fase A5/A6): lista con nombre legible, descripción, ruta
origen→destino, tipo coloreado, estado ON/OFF, tooltip con autor/versión,
resumen de activos. El pipeline registra los mods generados (se listan arriba
automáticamente).

### C5 — Arquitectura

✅ **Hecho**: 
- `src/launcher/mod_pipeline.h/.cpp` — `ModPipeline` (C++): carga el catálogo,
  lanza `python <proyecto>/mod center hd/launcher_mod_pipeline.py ...` en un
  hilo (`_popen`, `2>&1`), captura el output. La ruta del proyecto se resuelve
  igual que `ModsRoot()` (subir desde el exe hasta `assets`).
- `src/launcher/launcher_state.cpp` `DrawModPipelineTab()` — UI de los combos y
  botones + caja de output en vivo.
- `mod center hd/launcher_mod_pipeline.py` — orquestador Python que reutiliza
  `swap_b1.py`, `extract_amb_awo.py` e `install_b3_to_b1.py` (no duplica la
  lógica de parsing).

---

## Fase D — Ports de modelos (continuar con lo validado)

- Portar más personajes B3→B1 con `install_b3_to_b1.py` (el pipeline es la vía
  viable). Priorizar personajes jugables en B3 con equivalente en B1:
  Goku, Vegeta, Piccolo, Gohan, Cell, Freezer, Androides.
- Catalogar los personajes B3 con su label de androide (X20G=Gero, X19G=A19,
  X17G=A17, X16G=A16, X18G=A18...) → `docs/referencias/PERSONAJES_B3_BINS.md`.
- Documentar los fallos conocidos por personaje (rig boca, pelo en calvos).

---

## Orden de ejecución sugerido

1. ✅ **A1-A3** — dumps pequeños + limpieza automática de logs/dumps.
2. ✅ **A5-A6** — manifest descriptivo + UI de mods mejorada.
3. ✅ **C1** — catálogo de personajes (26 B1 + 56 B3).
4. ✅ **C2** — port B3→B1 en la UI (validado con `--dry`, Gero).
5. ✅ **C3** — swap B1→B1 en la UI.
6. ✅ **B1** — investigación widescreen (combate ya es 16:9; menús 4:3 por diseño).
7. 📋 **Fase D** — portar más personajes con el pipeline validado.
8. 📋 **B2-B5** — widescreen 21:9 si se decide RE del motor guest.
