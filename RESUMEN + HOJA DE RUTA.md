# RESUMEN + HOJA DE RUTA — DBZ Budokai 1 HD Collection (recompile ReXGlue + Launcher + Mods)

> **Propósito de este documento**: que una sesión nueva (nuevo contexto de IA o
> colaborador) entienda en 10 minutos qué es este proyecto, dónde está el código,
> qué se ha hecho, y **qué problemas están abiertos AHORA MISMO**. Es la puerta de
> entrada; para detalle técnico profundo leer `AGENTS.md` y las docs de
> `docs/re/` (referencias al final).

---

## 1. ¿Qué es esto?

Un **recompilador (ReXGlue)** del juego **DBZ Budokai 1 HD** (Xbox 360, PPC) a
**x86/Windows**, empaquetado como un **launcher** con:
- Botón **Play**: lanza el juego recompilado.
- Pestaña **Mods**: gestiona mods visualmente (activar/desactivar/editar).
- **Model pipeline**: portar modelos **B3 HD → B1 HD** y hacer **swaps B1 → B1**.

La parte original del juego (assets, `.xex`, bins de personajes) **NO se sube**
(copyright). Solo se suben a GitHub los fuentes de la herramienta + la lógica.

**Binarios**: `out\build\win-amd64-release\dbz1.exe` (NO el `dbz1.exe` de la raíz).
**Logs**: `out\build\win-amd64-release\logs\dbz1_NNN.log`.
**Crash dumps**: `out\build\win-amd64-release\crash_*.dmp` (ahora MiniDumpNormal, ~MB).
**Catálogo de personajes**: `mod center hd\cache\characters.cat` (generado por
`launcher_mod_pipeline.py catalog`).

---

## 2. Arquitectura del código (dónde está cada cosa)

| Ruta | Qué es |
|---|---|
| `src/main.cpp` | Recompilador + integración del launcher + carga de mods. |
| `src/launcher/launcher_state.{h,cpp}` | Estado/UI del launcher (pestañas, mods, pipeline). |
| `src/launcher/mod_pipeline.cpp` | Ejecución asíncrona de Python desde la UI (`_popen`). |
| `src/mods.cpp` | Detección de mods + `manifest.txt` + activación (`.disabled`). |
| `rexglue-sdk/src/filesystem/afs.cpp` | Carga de AFS y de overrides de mods (caches). |
| `mod center hd/launcher_mod_pipeline.py` | Orquestador Python: `catalog`/`swap`/`port`. |
| `mod center hd/characters_db.py` | **Catálogo maestro** de personajes (B1 HD, B3 HD, B1 PS2). |
| `mod center hd/swaps/swap_b1.py` | Swaps B1→B1 y **port** B3→B1 (genera el mod). |
| `mod center hd/conversores/install_b3_to_b1.py` | Port B3→B1: AWO + materiales + AZT + compresión + mod. |
| `mod center hd/paths.py` | Rutas portables (AFS B1/B3, tools/). |
| `mod center hd/cache/characters.cat` | Catálogo generado (formato abajo). |

**Formato del catálogo** (`characters.cat`):
```
juego|label|nombre|variante|jugable|nota|main|slot_geom|slot_tex|slot_acm|slot_csk|verts|awgs
```
Ejemplos relevantes:
```
B1|XPIC_BODY|Piccolo|Traje 1|1||1|1766|1767|1765|0|4337|11
B1|XNAP_BODY|Nappa|Traje 1|1||1|1387|1388|1386|0|6098|17
B3|XDBR_BODY|Dabura||1||1|176|0|0|0|2111|17
B3|XBRL_BODY|Broly||1||1|119|0|0|0|2799|15
```

---

## 3. Cómo funciona el sistema de mods

### Instalación
Un mod es una carpeta en `mods/<nombre>/` que sobrescribe entradas de los AFS.
El override se escribe en **TODOS** los `data_*.afs` de personaje porque el runtime
puede leer cualquiera según región/idioma (todas comparten la misma numeración de
bins). Estructura:

```
mods/<nombre>/
  us/
    data_en.afs/<entrada>/geom.bin
    data_en.afs/<entrada>/tex.bin
    data_fr.afs/...   (todos los data_*.afs)
    ...
  .disabled           <- si existe, el mod está DESACTIVADO
  manifest.txt        <- name/description/author/version/type/...
```

Reglas de compresión/padding (críticas):
- Compresión con `xbcompress.exe /N:2048` (NUNCA `/N:32`).
- **Padding al tamaño REAL del slot destino** (función `slot_pads()` en
  `swap_b1.py`), no padding fijo. `tex.bin` debe tener **al menos** el
  `entry_size` del slot original o el runtime hace EOF al leer → textura/port roto.
- Overlay sin reempaquetar el AFS; el runtime resuelve el override por
  nombre AFS + entrada.

### Activación
- Mod ACTIVO: carpeta sin `.disabled`.
- Mod INACTIVO: carpeta con archivo `.disabled` dentro. **NO** renombrar la carpeta.

### El runtime cachea los mods
`rexglue-sdk/src/filesystem/afs.cpp` escanea los mods **una sola vez** por arranque
(`g_mod_dirs_scanned` + `g_afs_override_neg_cache`). Por eso, si se instala/activa
un mod **después** de que el launcher ya escaneó, hay que llamar a
`AfsResetModCache()` antes de `LaunchModule()`. Ese fix YA está en
`src/main.cpp` (línea ~148) y **ya está recompilado** en el `dbz1.exe` nuevo.

---

## 4. 🔴 PROBLEMAS ABIERTOS (estado tras la sesión del 19/08 tarde)

### 4.1 — ✅ RESUELTO (19/08): Play crashea tras crear/activar mods
- **Causa raíz**: el `ModPipeline` del launcher (miembro de `LauncherDialog`)
  tiene un `std::thread worker_` que queda **joinable** tras cada operación
  (catalog/port/swap). Al pulsar Play, el diálogo se auto-destruye
  (`ImGuiDialog::Draw` → `delete this` al cerrar) y el destructor destruye el
  thread joinable → **`std::terminate`** (`mods` creados + Play = crash
  determinista en cuanto se había abierto la pestaña Mods / corrido el pipeline).
- **Evidencia**: logs 025 (15:33:00) y 027 (15:35:30) mostraban
  `launcher Play pressed` → `std::terminate called!` sin llegar a
  `OnPreLaunchModule`. En 026/028 (sin worker) Play funcionaba.
- **Fix aplicado y recompilado** (exe 19/08 15:58):
  - `ModPipeline::Shutdown()` + destructor que hacen `join()` del worker.
  - `LauncherDialog::ShutdownPipeline()` llamado en el callback de Play ANTES de
    destruir el diálogo (evita el `std::terminate` del thread joinable).
  - try/catch en el worker del pipeline y en el launch diferido de
    `ReXApp::LaunchModule()` → cualquier excepción residual se loguea en vez de
    abortar.
- **Validación pendiente**: pulsar Play tras abrir Mods/pipeline con el exe nuevo.

### 4.2 — ✅ RESUELTO (19/08): Mod Dabura→Piccolo "no hacía cambios"
- **Causa (doble)**:
  1. El mod `port_XDBR_BODY_176_to_1766` estaba **desactivado** (`.disabled`) y
     sin `manifest.txt` (`manage_mods()` desactiva los demás al instalar uno nuevo).
  2. **El runtime carga el traje por defecto de Piccolo en 1768/1769** (4110
     verts), NO 1766/1767 (4337) que el catálogo etiqueta "Traje 1". Instalar el
     port SOLO en 1766/1767 → no se veía en combate.
- **Fix**: `swap_b1.install()` acepta `dest_pairs` (todos los trajes) y el
  pipeline expande `--dest-label` a todos los pares del personaje. El port
  Dabura→Piccolo ahora se instala en **1766/1767, 1768/1769, 1770/1771 y
  1772/1773** (todos los AFS). Mod reactivado con manifest. Lo mismo para
  Dabura→Tenshinhan (363/364 + 365/366).
- **Nota**: con varios mods activos a la vez se solapan los overrides de los
  mismos slots (el último activado gana). Mantener **uno solo activo** a la vez
  (el instalador ya desactiva los demás).

### 4.3 — ✅ CAUSA RAÍZ ENCONTRADA (19/08): Broly B3 → Nappa B1 crash
- **Intento**: `port_XBRL_BODY_119_to_1387` = **Broly B3 (XBRL, bin 119) → Nappa B1
  (XNAP, geom 1387 / tex 1388)**.
- **Causa raíz (lección 26)**: el runtime sirve el override leyendo
  `entry_size` bytes de la entrada original. El tex comprimido del port de
  Broly mide **30572 B**, pero el slot tex 1388 de Nappa solo tiene
  **18632 B** de entry_size → **el stream LZX se trunca** → descompresión
  corrupta → **crash 0xC0000005** al cargar el personaje. El padding del
  archivo a 33504 B NO ayuda: el juego lee solo los 18632 B del slot.
  El geom sí cabe (85030 ≤ 283952).
- **Evidencia**: dump `crash_20260819_153737.dmp` → ExceptionAddress
  `0x7ff7688ba2ee` justo tras `AFS entry override ... entry=1388 ... tex.bin`.
  Comparación: Gero (funciona) tex comprimido 24538 ≤ 33504 (slot 2451) ✓;
  CHZ (funciona) idem ✓; Broly (crash) 30572 > 18632 ✗.
- **Fix aplicado**: `swap_b1.install()` ahora valida que el comprimido quepa en
  el `entry_size` del slot ANTES de instalar → error claro en vez de mod roto:
  `tex comprimido (30572 B) NO cabe en el slot 1388 del AFS (18632 B)...`.
  El mod Broly quedó **desactivado** (estabilidad). Para portar Broly hace falta
  un destino con slot tex ≥ 30572 B (p. ej. Piccolo 1767=33702, Goku 1758=49574,
  Cell 357=49774) o reducir las texturas del AZT.

---

## 5. 📋 HOJA DE RUTA (orden sugerido)

1. ✅ **Arrancar**: el exe recompilado (`out/build/win-amd64-release/dbz1.exe`,
   19/08 15:58) incluye el fix del thread joinable + try/catch del launch.
2. ✅ **Fix de Play (4.1) aplicado y recompilado**; **validar en juego**: abrir
   Mods/pipeline y pulsar Play — ya no debe crashear.
3. ✅ **Dabura→Piccolo (4.2)**: causa doble resuelta — port ahora cubre TODOS
   los trajes de Piccolo (1766-1773) porque el juego carga 1768/1769 por defecto;
   mod reactivado con manifest. **Validar en juego**: Play → Piccolo → Dabura.
4. ✅ **Broly→Nappa (4.3)**: causa raíz = tex comprimido (30572 B) > slot 1388
   (18632 B) → truncación → crash. Validación añadida al pipeline; mod
   desactivado. Para Broly en otro slot: usar destino con tex ≥ 30572 B.
5. ✅ **Swap B1→B1**: pasó de `_popen` a **`CreateProcess`** (lección 29) para
   que no abra una ventana CMD vacía y no falle por comillas. Recompilado.
   **Validar en juego**: el swap ya debe ejecutarse y mostrar su output.
6. **Sincronizar con GitHub (`github/`)**: copiar fuentes modificados + docs y
   commitear (commit local `440b7c4`; **push pendiente** — el usuario lo hace
   o se reintenta con auth).
7. **Actualizar** este documento y `AGENTS.md` con las conclusiones de la sesión.

---

## 6. Referencias rápidas (detalle)

- `AGENTS.md` (raíz): la guía técnica consolidada (formato HD, formato PS2, lecciones 1-25).
- `docs/re/SESION10_PORT_B3_B1_FUNCIONAL.md` — port B3→B1 validado (Gero).
- `docs/re/SESION11_PORT_PS2_METODOLOGIA.md` — port PS2→HD + submesh.
- `docs/re/ANIMACIONES_MOVESETS_HD.md` — set de archivos del personaje + movesets.
- `docs/tutoriales/MODEL_SWAPS_METODOLOGIA.md` — swaps B1→B1 (par geom+tex).
- `docs/planes/PLAN_PORTS_FUNCIONALES.md` — hoja de ruta de ports.
- `docs/referencias/PERSONAJES_BINS.md` — personaje → bins.
- `mod center hd/characters_db.py` — catálogo maestro (fuente única).
- Proyecto hermano (guía de swaps B3): `DBZ Budokai 3 HD Collection\mod center hd\GUIA_SWAPS_Y_PORTS.md`.

---

*Firmado por NovaPowers. MIT License.*
*Última actualización: 2026-08-19 (4.1-4.3 resueltos en código + fix swap/CreateProcess + cobertura de todos los trajes; falta validación en juego y push GitHub).*
