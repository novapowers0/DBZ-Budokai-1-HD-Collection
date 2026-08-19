# AGENTS.md — DBZ Budokai 1 HD Collection (recompile ReXGlue)

> Copyright (c) NovaPowers. Released under the MIT License. Firmado por NovaPowers.
>
> 2026-08-19 (noche). Consolidado: **✅ 4.1 Play crash = thread joinable del
> ModPipeline destruido con el dialog (std::terminate) — FIX recompilado**.
> **✅ 4.2 Dabura→Piccolo válido (reactivado + manifest)**.
> **✅ 4.3 Broly→Nappa = lección 26: tex comprimido 30572 B > slot 1388 (18632 B)
> → truncación LZX → 0xC0000005; pipeline ahora valida y falla claro**.
> 2026-08-17. Consolidado v10-v12 + **model swaps B1→B1 100% funcionales** +
> **✅ PORT B3 HD→B1 HD 100% FUNCIONAL (Gero, validado en runtime)** +
> **moveset descartado (lección 13: #ACM no sustituible/generable sin RE)**.
> **✅ SWAP NATIVO CHZ HD COMPLETO → slot TSH validado** (lección 16: bin 352+353,
> 3 AWGs = cuerpo+manos, render perfecto). **Esqueleto B2 PS2 = HD 1:1**
> (Tenshinhan B2 PS2 entry 282/286: 42 labels base idénticos en el mismo orden).
> Formato HD: sec34 = vértice **44B stride**, offsets del header AWG0
> **RELATIVOS al AWG0**. Modelo base PS2 correcto = **B1 PS2**.
> **✅ PORT PS2→HD VIABLE (lecciones 22-24)**: el crash 0xC0000005 era TEX
> MISMATCH (no geometría). Con el par correcto (x_350+x_351) el port CHZ PS2→TSH
> **ENTRA EN COMBATE SIN CRASH** (mod `test_chz_ps2_texfix`). Deforforma por
> decimación voxel + descriptores uniformes → refinar para port fiel.
> **Guía de swaps para el proyecto B3**: `DBZ Budokai 3 HD Collection\mod center
> hd\GUIA_SWAPS_Y_PORTS.md` (principio del swap nativo, B3→B1 ✅, hoja de ruta
> B3→B3 y B1→B3; `awg_to_obj.py` del B3 arreglado 17/08).
> Docs de detalle: `docs/tutoriales/MODEL_SWAPS_METODOLOGIA.md`,
> `docs/re/SESION10_PORT_B3_B1_FUNCIONAL.md`, `docs/re/SESION9_MODEL_SWAPS_B1_B1.md`,
> `docs/re/ANIMACIONES_MOVESETS_HD.md` (set de archivos + movesets),
> `docs/re/SESION11_PORT_PS2_METODOLOGIA.md` (**NUEVA 17/08**: swap nativo CHZ,
> submesh data descifrado, mapeo B2 PS2→HD, hoja de ruta port PS2),
> `docs/planes/PLAN_QOL_WIDESCREEN_LAUNCHER.md` (hoja de ruta QoL/widescreen/launcher),
> `docs/re/SESION7_MESH_GROUP_COMPLETO.md`,
> `docs/re/SESION6_PORT_B2_B1_HD.md`, `docs/planes/PLAN_PORTS_FUNCIONALES.md`.

---

## 🔴 FORMATO HD (RE DEFINITIVA, verificado en TSH nativo slot_2450)

### Vértice sec34 (44B, layout de sesión 5 — CORRECTO)
```
+00 pos.x +04 pos.y +08 pos.z      (floats BE)
+12 weight (float, 0.7/0.8/0.9/1.0)
+16 BONE index (u32, VÁLIDO 1-34)
+20 nrm.x +24 nrm.y +28 nrm.z
+32 0xFFFFFFFF
+36 blend/scale
+40 uv
```
`n_sec = sec_size//44`. TSH nativo = **4272 verts**.

### Offsets del header AWG0 (+0x50) — RELATIVOS al AWG0 (NO absolutos)
```
+0x28 sec_off  → sec_abs  = AWG0 + val    (0xB20+0x24D0 = 0x2FF0)
+0x2C sec_size → n_sec = sec_size//44
+0x30 post_off → post_abs = AWG0 + val    (0xB20+0x30310 = 0x30E30 = sec+sec_size ✓)
+0x34 post_size
+0x38 siguiente zona (REL AWG0)
+0x3C bones count    +0x40 nombre (16B)
```

### Estructura física del #AWO (TSH slot_2450, 855584 B, 23 AWGs)
```
AWG0 header @0xB20 (0x50)
0xB60  label XTSH_BODY
0xB70..0x10A0 labels interleaved (0x20 c/u)
0x10A0..0x1410 12 mesh part headers (0x50 c/u)
0x1460..0x2130 42 ejes (0x50 c/u)
0x2180..0x24C8 42 arms (0x14 c/u: [bone, fin, 0, ini, 0])
0x2FF0..0x30E30 sec34 (4272 verts stride 44)   ← AWG0+0x24D0
0x30E30..0x36B6A zona post = IB u16 + sub-mesh
```

### Mesh part header (0x50B)
```
+00 4×128.0 (escala)  +10 4×weights [0.8,0.75,0.7,1.0]
+20:0 +24:5 +28:0 +2C:5
+30 grp_idx (0/1/2, FFFF=sombra)  +34 0xFFFFFFFF
+38/+3C type2 (0x1BD mesh, 0x11BD alt, 0x190 shadow, 0x199 special)
+40/+44 stride 0x44  +48/+4C 0
```

### Eje (0x50B)
```
+00..+0C quat local (x,y,z,w)  +10..+1C pos local (px,py,pz)
+20..+2C 4×1.0
+30 sello: 0x6000020F raíz, 0x9000020C/0x8000020C mesh,
          0x1000020C transición, 0x204/0x205 shadow, 0x9000020E/0x9800020E,
          0x90000208/0x80000208/0x10000208
+34 arm_ptr (REL AWG0) → arm 20B
+38 child +3C sibling +40 parent (→ labels)
⚠️ Leer desfasado +0x10 da falsa impresión de sello en +0x20 (19 ejes fantasma).
```

### Arm (20B) `[bone, fin, 0, ini, 0]`
- `ini`/`fin` = byte offsets **dentro del IB** (zona post). Ranges se solapan.
- TSH: solo 8 bones con mesh: 0[6576..7088], 9[6640..7968], 16[6704..8080],
  20[6768..8192], 24[6832..8496], 27[6896..8704], 31[6960..8816], 37[7024..9120].
- El arm del bone 20 existe pero su eje es "oculto" (sin sello) → leer los 42
  arms como zona contigua desde el arm_ptr del eje raíz.

### Sec34 nativo
- 2006/4272 slots (47%) son del bone 0 (XTSH_BODY raíz, coords world).
- Los huesos 1-32 = extremidades con pocos slots c/u.

---

## 🔴 MODELO BASE PS2 CORRECTO = B1, NO B2 (v12, 2026-08-15)

| Fuente | Labels | Verts | Parts | Traje |
|---|---|---|---|---|
| **B1 PS2 `TSH00.bin`** (en `Budokai 1 Models Converted to AMB\`) | `XTSH_BODY, TSH_WAIST, TSH_STMC, TSH_CHEST...` | 8476 | 23 | ✅ mismo que B1 HD |
| B2 `ent_282_amo.bin` | `TSH_BODY` (sin X) | 4427 | 14 | ❌ traje distinto |

- El port B2→B1 era error de base: traje distinto → solo 47% de slots encajaban.
- **Métrica**: pool world del B1 PS2 vs HD nativo = **4059/4272 slots (95%)
  con vecino <1.5, mediana 0.48**. El B2 solo 47%.
- **El bone_map por labels del B1 PS2 está MAL** (mapea 2→1, 4→2, 6→3 cuando
  son idénticos). Restringir por bone empeora (47% vs 95%). → **usar pool GLOBAL puro**.
- Los bins B1 PS2 (`XXX00.bin`) = #AMB con #AMO0@0x40. Los #ACM (`2445_TSH.bin`) son esqueleto, no malla.

---

## 🔴 BLOQUEADOR (matizado 16/08) — inyección parcial vs bin completo

**El runtime HD dibuja con el mesh group/IB que trae el bin instalado.** Esto
tiene DOS consecuencias:

1. **Inyectar SOLO coordenadas** de otro personaje sobre un bin nativo → muestra
   la topología del anfitrión (deforme). Solo funciona si la geometría es casi
   idéntica (mismo personaje, misma pose/traje). Única vía validada para
   retopología parcial = atajo v6/v8/v12 (mantener sec34 nativo, sustituir
   posiciones con vecino world PS2).
2. **✅ Instalar un bin #AWO COMPLETO de otro personaje B1** (mismo juego) →
   **funciona 100%**: el runtime renderiza el bin completo (mesh group, IB,
   bones, UVs incluidos). Es la base de los model swaps B1→B1. Requisito: el
   par geom (2450) + tex (2451) debe ser del MISMO personaje.
3. **✅ PORT B3→B1 100% FUNCIONAL (16/08, noche)** — vía del swap nativo: el
   runtime dibuja el bin completo tal cual, así que NO hace falta aplanar
   jerarquía ni reindexar bones. Un AWO B3 convertido (flag→0x2, type2→0x1BD,
   materiales B1, AZT con alpha DXT3 0xFF) + su AZT del MISMO personaje
   funciona en runtime. Validado con Gero B3→slot TSH.
   Pipeline: `conversores/install_b3_to_b1.py` (automático).

- Reconstruir sec34+IB con topología PS2 → **✅ VIABLE (17/08, lecciones 22-24)**:
  el crash 0xC0000005 era TEX MISMATCH. Con el par correcto (x_350+x_351)
  el port CHZ PS2→TSH entra en combate sin crash (mod `test_chz_ps2_texfix`).
  Deforme por decimación voxel (cell 0.148) + descriptores uniformes.

---

## 🟢 ESTADO DEL PORT (v10-v12 + PS2→HD validado 17/08)

| Versión | Qué | Resultado en juego |
|---|---|---|
| v10 | sec34 stride 44 + offsets REL, modelo B2 | 2032/4272 reemplazados |
| v12 | **modelo B1 PS2 TSH00 + pool GLOBAL** | **4059/4272 (95%)** |
| PS2→HD | **reconstrucción completa (amo0_to_awo.py + tex correcta)** | **ENTRA EN COMBATE SIN CRASH** (deforme) |

- v12 instalado en `mods/test_tsh_b2_stride16`. Mesh group/post intactos, solo
  posiciones cambiadas (media 0.59).
- **Problema residual (v12)**: deformidades en pies, muñequeras, cabeza y piernas
  (pocos vértices → el vecino más cercano aproxima mal); cintura/abdomen bien.
  Es inherente al matching por vecino (polígonos agrandados). El IB nativo no
  respeta la topología PS2 en zonas poco densas.
- **Port PS2→HD (17/08)**: reconstrucción completa con topología PS2 real —
  entra en combate sin crash con la textura del MISMO par (x_351). El modelo
  se ve deforme por decimación voxel agresiva + descriptores A/B uniformes.
  Refinar: decimación más conservadora + descriptores por-part reales.
- El Goku SS2 (personaje distinto) necesita la vía de retopología completa.

## PRÓXIMOS PASOS (port)
1. Afinar v12: decimar pool antes del matching, penalizar bone, suavizado.
2. Retomar retopología completa (obj_to_awg_hd desde OBJ con mesh group generado).
3. Para Goku SS2: usar `GOK00.bin` del mismo set (B1 PS2), nunca el del B2.
4. **✅ PORT B3→B1 100% FUNCIONAL (16/08, noche)**: `install_b3_to_b1.py`
   automatiza TODO (port + materiales + alpha AZT + comprimir + instalar mod).
   Validado con Gero B3→slot TSH: rig OK, materiales/specular OK, texturas OK,
   reacciones a daño OK. Fallos conocidos a documentar: (a) la mandíbula abre
   al recibir daño pero no al usar técnicas (rig boca B3); (b) Tenshinhan es
   calvo → los bones de pelo del Gero no responden (comen medio brazo).
   Detalle: `docs/re/SESION10_PORT_B3_B1_FUNCIONAL.md`.
5. **✅ MODEL SWAPS B1→B1 100% FUNCIONALES** (16/08, tarde): el crash del port
   era un **MISMATCH DE TEXTURA**, no el mesh group. A/B con bins B1 nativos
   (`52_u.bin` X20G y `49_u.bin` X19G en slot 2450 + tex del B3) → ambos
   crasheaban igual. Con el **par nativo completo del mismo personaje**
   (geom `49_u.bin` X19G en 2450 + tex `48_u.bin` AZT en 2451) el modelo
   **renderiza perfecto en combate**. El runtime exige que geom (2450) y tex
   (2451) correspondan al MISMO personaje. Las teorías de mesh group jerárquico
   y conteos fijos quedaron descartadas. Metodología completa:
   `docs/tutoriales/MODEL_SWAPS_METODOLOGIA.md`.
6. **⚠️ Identidad por labels**: `X19G` = **Android 19** (jugable, bins
   45/47/49), NO Dr. Gero. El Dr. Gero es `X20G`/`20G` = bins 52/53
   (no jugable, historia). Identificar SIEMPRE por el label `XXX_BODY`
   (`docs/referencias/PERSONAJES_BINS.md`).

---

## MODS (canónico)

- Instalación: el override se escribe en **TODOS los `data_*.afs` de
  personaje** (`mods/<mod>/us/data_XX.afs/<entrada>/geom.bin`) porque el
  runtime puede leer cualquiera según región/idioma y todos comparten la misma
  numeración de bins (2575 entradas). Overlay, sin reempaquetar. Compresión:
  `xbcompress.exe /N:2048` (NUNCA /N:32), padding a 290816 B con 0x00,
  round-trip verificado con `xbdecompress.exe`.
- ⚠️ **`tools/` necesita las DLLs junto a los .exe**: `xbcompress.exe`/
  `xbdecompress.exe` (XDK, x86) dependen de `MSVCP71.dll`, `MSVCR71.dll` y
  `xbdm.dll`. Sin ellas crashean con **0xC0000135** (STATUS_DLL_NOT_FOUND,
  rc 3221225781) y TODO el pipeline (catálogo/swap/port) falla — además el
  catálogo parece "funcionar" por caché stale en `%TEMP%\opencode\launcher_catalog`
  (`lzx_decompress` da por bueno el `.bin` viejo aunque `xbdecompress` crashee).
  El repo raíz ya lleva las 3 DLLs en `tools/` (19/08). Fuente de referencia:
  `DBZ Budokai 3 HD Collection\mod center\Xbox 360 Compression - Decompression
  tool from the XBOX Development Kit\`.
- **⚙️ Recompilar la SDK (19/08)**: el proyecto enlaza la SDK pre-compilada en
  `rexglue/` (`rexruntime.lib`/`rexruntime.dll`). `rex_app.cpp` se compila en el
  target dbz1 desde `rexglue/share/rexglue/rex_app.cpp` (copia instalada) — si
  se edita `rexglue-sdk/src/ui/rex_app.cpp` hay que copiarlo a esa ruta. Los
  cambios de `rexglue-sdk/src/filesystem/afs.cpp` (p. ej. `AfsResetModCache`)
  requieren reconstruir la SDK: `cmake --build rexglue-sdk/out/build/win-amd64
  --target rexruntime --config Release` + copiar `out/win-amd64/Release/
  rexruntime.dll` a `rexglue/bin/` y `out/build/win-amd64-release/`.
- **Bug UI "Buscar" AFS (19/08)**: la causa raíz es que **la `SDL3-static.lib`
  del bundle se compiló con el driver DUMMY de diálogo** (`SDL_DIALOG OFF`):
  `SDL_ShowOpenFileDialog` llama al callback con NULL al instante y **nunca abre
  un diálogo nativo** (verificado: ninguna SDL3-static.lib tiene
  `SDL_Windows_ShowFileDialog`/`Comdlg32.dll`/`GetOpenFileNameW`/`IFileOpenDialog`).
  **Corregido**: el botón "Buscar" ya NO usa SDL; usa **`GetOpenFileNameW`
  (commdlg) nativo de Windows**, síncrono en el hilo de UI
  (`ShowNativeOpenFileDialog` en `launcher_state.cpp`). Además se quitaron
  `ImGuiInputTextFlags_EnterReturnsTrue` de los campos AFS (commitean en cada
  edición) y `RunAsync` cita cada arg (rutas con espacios, p. ej. "PROYECTOS IA").
  "Usar ubicaciones por defecto" ahora regenera el catálogo con las rutas
  por defecto. **Autodetección estandarizada (19/08)**: B1 = `data_us.afs`,
  B3 = `data_cmn.afs` (antes prefería `data_sp.afs`).
- **⚠️ `_popen` + `"python"` citado = WinError 123 (19/08, validado)**: si el
  comando de `RunAsync` cita el ejecutable de python (`"python" "script" ...`),
  el `_popen` de MSVC falla con `El nombre de archivo, el nombre de directorio
  o la sintaxis de la etiqueta del volumen no son correctos` (ERROR_INVALID_NAME,
  exit 1) — reproducible con un programa C++ de test, pero `subprocess.run(
  shell=True)` de Python y `cmd /c` SÍ lo ejecutan (diferencia de `_popen`).
  **Solución**: NO citar `python` (solo se cita si `DBZ1_PYTHON` contiene
  espacios); citar siempre el script y cada arg. Validado: `python "script"
  "port" ...` exit 0 con `_popen`.
- **⚠️ Bug destino incorrecto en Port/Swap (19/08)**: `pipeline_b1_dst_idx_`
  estaba COMPARTIDO entre el combo de destino del **Port** (índice directo en
  `b1[]`) y el del **Swap** (índice en la lista FILTRADA `swap_dst_idx[]`, solo
  personajes con `geom != 0`). Al seleccionar el destino en un combo se corrompía
  el índice del otro → el Port escribía al personaje equivocado (Dabura→slot
  1766/Piccolo en vez de Tenshinhan Joven 363/364) y el Swap podía colgarse
  (índice fuera de rango de la lista filtrada). **Corregido**: se separó en
  `pipeline_b1_dst_idx_` (Port) y `pipeline_swap_dst_idx_` (Swap) en
  `launcher_state.{h,cpp}`. Regla: cada combo con lista distinta debe usar su
  propia variable de selección.
- Activación: **archivo `.disabled` DENTRO de la carpeta del mod**
  (`mods/foo/.disabled`). NO renombrar a `foo.disabled`. `src/mods.cpp` devuelve
  `ModInfo{name,enabled}` y normaliza; `rexglue-sdk/afs.cpp` no los carga (la DLL
  precompilada `rexruntime.dll` no incluye el cambio de afs.cpp todavía).
- Mods actuales (19/08): `port_XDBR_BODY_176_to_1766` (port Dabura→slot
  1766/1767/Piccolo) **activo con manifest** (port VÁLIDO: geom comp 73204 ≤
  160500, tex comp 23470 ≤ 33702). `port_XBRL_BODY_119_to_1387` (Broly→Nappa)
  **desactivado** — port INVIABLE: tex comprimido 30572 B > slot 1388 (18632 B)
  → truncación → crash (lección 26; el pipeline ahora valida y falla con error
  claro). `test_gero_b3_to_b1_v2` (port Gero B3→B1, **100% funcional**)
  **desactivado**. `test_chz_ps2_texfix` (port CHZ PS2→slot TSH
  2450/2451, **entra en combate SIN CRASH** con textura correcta x_351 — primera
  validación de reconstrucción PS2→HD completa; modelo deforme por decimación
  voxel) **desactivado**.
  `test_gero_moveset_19` (Gero v2 + #CSK X19G 2448)
  y `test_gero_on_a19` (Gero en slot A19) → **descartados** (crash/moveset no
  viable, ver lección 13); test_a19_on_tsh = swap Android 19 (X19G), **100%
  funcional** (geom `49_u.bin` + tex `48_u.bin`) → desactivado;
  example_music_swap, test_b3b1_pipeline_check, test_gero_b3_to_b1 (nombre
  viejo), test_gero_on_tenshinhan, test_piccolo_on_tenshinhan,
  test_tenshinhan_deform/grow/red/vanilla, test_tsh_b2_stride16,
  test_chz_ps2_* (variantes con tex incorrecta) → desactivados
  (marcador interno).
- Lanzamiento: `out\build\win-amd64-release\dbz1.exe` (NO el `dbz1.exe` de la
  raíz, es un build viejo). Logs: `out\build\win-amd64-release\logs\dbz1_NNN.log`.
  Crash silencioso → Visor de eventos Windows → Application Error.
- El override de mods hace match por nombre AFS + entrada, sin depender de la
  región de assets (`assets\eu` o `assets\us`).

### Rutas portables (para salir a GitHub)

- **Nada depende de rutas de usuario** (`C:\Users\...`). Todo se deriva de
  `mod center hd/paths.py`: assets/ del repo, tools/ (xbcompress), y el
  proyecto B3 (variable `DBZ3_ROOT` o carpeta hermana).
- **B1 AFS**: los modelos de personaje viven en CUALQUIER `data_*.afs`
  (`data_sp/us/fr/en/ge/it`), todos con la MISMA numeración de bins. El
  catálogo/swap acepta cualquiera (`--b1 <ruta>` o autodetección).
- **B3 AFS**: solo `data_cmn.afs` (donde están los modelos).
- Docs y herramientas firmados como **NovaPowers** (MIT). `tools/` lleva las
  herramientas de compresión para que el repo sea autocontenido.

---

## HERRAMIENTAS (`mod center hd\`)

| Herramienta | Función |
|---|---|
| `launcher_mod_pipeline.py` | **Orquestador para el launcher (17/08)**: catálogo de personajes B1/B3 (`catalog` → `cache/characters.cat`), swap B1→B1 (`swap`), port B3→B1 (`port`). Lo invoca la UI del launcher (pestaña Mods → Model pipeline). `--dry` solo muestra el plan. |
| `paths.py` | **Rutas portables**: detecta AFS B1 (cualquier `data_*.afs`) y B3 (`data_cmn.afs`), y las herramientas de compresión (`tools/`, `DBZ1_XBCOMP_DIR` o proyecto hermano). Sin rutas de usuario. |
| `characters_db.py` | **Catálogo maestro de personajes** (nombres, variantes, jugable/no-jugable de B1 HD, B3 HD y B1 PS2). |
| `swaps/swap_b1.py` | **MODEL SWAPS B1→B1 automatizados** (catálogo AFS + extraer par geom/tex + comprimir + instalar mod). `--list`, `--info`, `--origen`, `--dest`, `--tex` |
| `conversores/install_b3_to_b1.py` | **PORT B3 HD→B1 HD AUTOMÁTICO** (validado Gero): port AWO + materiales B1 + alpha AZT + comprimir + instalar mod. `install_b3_to_b1.py <awo_b3> <azt_b3> --mod <nombre>` |
| `conversores/port_b3_to_b1_v2.py` | Port B3→B1 (flag 0x2, type2 0x1BD/0x11BD, materiales B1, alpha AZT). `port_b3_to_b1_v2.py <awo_b3> <azt_b3> <out.awo> <out_azt.bin>` |
| `conversores/port_b3_to_b1_v4.py` | v2 + **retargeting por matrices bind** (transforma coords de bones huérfanos → evita estiramiento). `port_b3_to_b1_v4.py <awo_b3> <azt_b3> <out.awo> <out_azt.bin>` |
| `conversores/amo0_to_awo.py` | **Port PS2→HD REESCRITO con enfoque B3 (lecciones 22-24)**: triángulos reales FaceType + decimar por (bone,voxel) a buffers del template + rellenar EN POSICIÓN (delta=0) + descriptores A/B + arms intactos. **VALIDADO: entra en combate sin crash** con la textura del MISMO par (CHZ x_351). `amo0_to_awo.py <ps2.amb> <template.awo> <out>` |
| `analizadores/analyze_submesh*.py` | RE de los descriptores de submesh (rangos A/B, flags, mesh-ref) |
| `conversores/obj_to_awg_hd.py` | v8 validado (mismo personaje) |
| `conversores/build_awo_from_json.py` | retargeting inv_rigid (B3) |
| `conversores/retarget_hd.py` | `retarget_local(bind_src,bind_dst,local_src)` + align_joint |
| `analizadores/analyze_b1_hd.py` | estructura de un bin HD |
| `analizadores/catalog_b2_ps2.py` | **catálogo de personajes B2 PS2** (escanea AFS por labels `X??_BODY`, lista entries main+heads) |
| `analizadores/extract_amb_awo.py` | #AWO+#AZT desde #AMB HD |
| `exportadores/export_sec34_obj.py` | sec34 → OBJ |
| `exportadores/azt_to_dds.py` | texturas |
| `parsers/lib_ps2/extract_hd_mats.py` | ejes HD → world mats |
| `parsers/lib_ps2/` | parsers PS2 (parse_ps2_model, pose_matrix...) |
| `scripts_gero/` | ⚠️ port Gero B3→B1 ANTIGUO (rerig_*.py usan offsets pre-v10: bone+18, sec+0x34 → NO usar). El pipeline correcto es `port_b3_to_b1_v2.py` + `install_b3_to_b1.py` |
| `src_comunidad/` | OBJ_to_AMG, AMO_Compiler/Decompiler, Model-Rig Extractor, etc. |

Uso: `python build_awg_hd_full.py <bin_hd_base_mismo_personaje.awo> <modelo_ps2.amb> <out.bin>`

---

## LECCIONES CLAVE

1. **PS2 y HD guardan coords LOCALES al hueso** (bone index). La conversión es
   re-layout LE→BE + re-mapeo de bones, no cambiar coords. El align_joint solo
   hace falta si el esqueleto difiere en rotación (GOK vs TSH: WAIST/CHEST 90°,
   STMC/NRA 180°).
2. **El mesh group HD es jerárquico** (`$data` hueso → `$grp` mesh part →
   `$sub` submesh → verts `<$data, weight, pos, uv, nrm, color>` = 44B).
   JSON de referencia: `modding resources discord\research\00000002-...b3.AMO.json`
   (B3, jerárquico) y `0001-0001.AMO._skel-1.json` (B1, plano, XGOK).
3. **Flags de formato**: AWG `+0x0C` = 0x2 (B1) / 0x4 (B3). Mesh part `type2`
   = 0x1BD/0x11BD (B1) / 0x29BD (B3). El port B3→B1 requiere convertirlos.
4. **#AMB PS2** = `[header, #AMO, #AMT]`; **#AMB HD** = `[header, #AWO, #AZT]`
   (#AWO@0x40). **#ACM** = armatura (esqueleto), no malla.
5. **B2 PS2 usa el MISMO #AMO/#AMG que B1** (el traductor cubre ambos), pero el
   traje/personaje puede diferir (TSH B2 ≠ TSH B1). Verificar SIEMPRE con labels.
6. **Swap B1→B1 completo = par geom+tex del MISMO personaje** (16/08): instalar
   un #AWO entero de otro personaje en el slot funciona 100% si el #AZT (tex)
   corresponde al mismo personaje. El runtime NO exige conteos fijos del slot
   (X19G con 46 bones/15 AWG/4601 verts corre en slot TSH de 42/23/4272). El
   crash por tex mismatch → 0xC0000005. `X19G` = Android 19 (NO Gero).
7. El modelo de IA no soporta imágenes; describir capturas o usar qwen3-vl:4b.
8. **Auditoría de offsets (16/08)**: `analyze_b1_hd.py` y `export_sec34_obj.py`
   leían el sec34 desde `+0x34` (post_size) — CORREGIDOS a `+0x28`. El resto de
   scripts (`build_awg_hd_full`, `build_awg_retopo`, `build_b1_*`, `obj_to_awg_hd`,
   `port_b3_to_b1`, `port_personaje_a_tsh`, `swap_b1`) ya usaban `+0x28`. Los
   `scripts_gero/rerig_*.py` quedan obsoletos (bone +18, sec_off +0x34).
9. **Vía B3→B1 simplificada por el swap nativo** (16/08): el runtime dibuja el
   bin #AWO completo tal cual (mesh group, IB, bones, UVs) sin validar el slot
   → un #AWO B3 convertido (flag→0x2, type2→0x1BD) + su #AZT del MISMO
   personaje funciona SIN aplanar jerarquía ni reindexar bones. El crash del
   port Gero era tex mismatch, no el mesh group. **✅ VALIDADO (16/08 noche)**:
   Gero B3 HD→B1 HD renderiza perfecto en combate.
10. **Port B3→B1 requiere 2 cosas además de flag/type2** (16/08, validado):
    (a) **Materiales B1** en mesh parts no-sombra: escala 4×128.0 (B3 usa 1.0
    → cuerpo negro/sin specular) + weights torso 0.85/0.80/0.70/1.0, extremidades
    0.85/0.85/0.80/1.0 + type2→0x11BD (shader B1 alternativo con specular);
     (b) **AZT con alpha DXT3 a 0xFF** (el runtime B1 espera texturas opacas;
     el B3 usa DXT3 con alpha variable → cuerpo negro). Fallos conocidos:
     mandíbula abre al recibir daño pero no al usar técnicas (rig boca B3);
     calvos (TSH) → bones de pelo no responden (deforman brazos).
11. **Set de archivos del personaje HD** (16/08): el personaje completo en
    `data_sp.afs` NO es solo #AWO+#AZT. Set típico: `#ACM` (esqueleto, ej.
    TSH 2445) + `#CCM` (comandos/moveset, 2446) + `#CFC` (flags cara, 2447) +
    `#CSK` (tabla de ANIMACIONES/moveset, 2448) + `#SPX` (efectos, 2449) +
    `#AWO` (modelo, 2450) + `#AZT` (texturas, 2451). **Todos los #CSK tienen
    la MISMA estructura** (2037 animaciones, mismos IDs — solo difieren los
    keyframes) → intercambiables para portar movesets. Detalle:
    `docs/re/ANIMACIONES_MOVESETS_HD.md`.
12. **Retargeting de bones con matrices bind** (16/08): cambiar solo el bone
    index de vértices huérfanos (pelo→HEAD) SIN transformar coords ESTIRA la
    geometría porque los vértices están en coords LOCALES al bone origen.
    Solución correcta: transformar las coords con `local_dst = inv(M_dst) *
    M_src * local_src` (matrices bind world compuestas por jerarquía).
    Herramienta: `conversores/port_b3_to_b1_v4.py` (usa matrices bind del AWO).
13. **Moveset = #CSK sustituible; #ACM NO (17/08, concluido)**: instalar el
    #CSK de otro personaje en el slot (2448) **cambia el moveset** (hallazgo)
    pero con poses rotas (el #ACM del slot no coincide). Instalar el #ACM de
    otro personaje (2445) **rompe el modelo** (T-Pose). El #ACM HD contiene
    esqueleto + **expresiones faciales** (163 bloques `[9,0,cnt,off]` en el
    TSH, 6 en el X19G por ser androide) + tabla de labels de 32B al final.
    Generar un #ACM para el Gero (46 bones `X20G_*`) requiere reconstruir las
    9002 poses internas (RE completa): cambiar solo labels+conteo → crash
    **0xC0000005** (datos de poses indexados por nº de bones). **El port de
    movesets queda descartado por ahora; los ports de modelos son la vía
    viable.** El AWO del Gero B3 tiene 46 labels X20G_* (X20G_BODY, 20G_WAIST,
    20G_RLEGROT... X20G_HAIR1/2/3, X20G_SHD3). GameCube (.iso) NO es útil: sus
    `.acm` no tienen magic `#ACM` (formato distinto). Detalle:
    `docs/re/ANIMACIONES_MOVESETS_HD.md` §9-11. Mod actual: `test_gero_b3_to_b1_v2`.
14. **Crash dumps de 4GB (17/08)**: `src/main.cpp` usaba `MiniDumpWithFullMemory`
    en SetupCrashHandler → cada crash generaba ~4GB (`crash_*.dmp`). **Cambiado
    a `MiniDumpNormal`** (stacks, ~MB) — requiere recompilar. Limpiados 5 dumps
    (~20GB).
15. **Launcher: mods + pipeline de modelos (17/08)**: la pestaña Mods del
    launcher ahora tiene (a) gestión visual de mods con `manifest.txt`
    (name/description/author/version/type/source/target; inferencia de tipo
    por contenido: port_b3/swap_b1/moveset/audio/data + conteo de archivos) y
    (b) **Model pipeline**: catálogo de personajes (`launcher_mod_pipeline.py
    catalog` → `mod center hd/cache/characters.cat`, **109 modelos B1 + 183
    B3**), port B3→B1 y swap B1→B1 con combos y ejecución asíncrona de Python
    (`ModPipeline` en `src/launcher/mod_pipeline.cpp`, `_popen` + hilo, output
    en vivo). **Catálogo maestro**: `mod center hd/characters_db.py` (nombres,
    variantes, jugable/no-jugable de B1 HD, B3 HD y B1 PS2; fuente única).
    Formato cat: `juego|label|nombre|variante|jugable|nota|main|geom|tex|acm|csk|verts|awgs`
    — **una fila por modelo/traje** (main=1 la fila principal; variantes extra
    como "Traje 2"/"SSJ"...). El launcher muestra **nombre+variante** (ej.
    `Goku (SSJ2)`, `Uub`, `Mr. Satan`) y marca `[NO JUGABLE]` los modelos de
    historia (Dr. Gero, Dende, Roshi, Bulma...). **Dr. Gero distinguido**:
    `20G_FACE` = solo cara, `X20G_BODY` = cuerpo. Swaps usan el **bin
    específico** (varios modelos comparten label). Edición de descripción de
    mods en el launcher: botón Editar → `SetModManifestValue` escribe
    `manifest.txt` (description/author/version). El B3 (data_cmn.afs del
    proyecto hermano) usa `#AMB` que contiene AWO+AZT; los bins B3 del
    catálogo corresponden a la lista GH (coinciden con el AFS real). Limpieza
    automática de logs/dumps viejos en `OnPostSetup` (`CleanupOldArtifacts`,
    retiene 10 logs y 3 dumps).
16. **Swap nativo B1→B1 con bins HD del MISMO personaje = 100% (17/08, noche)**:
    el CHZ HD completo (geom bin 352 + tex 353, 3 AWGs = XCHZ_BODY + LHAND +
    RHAND) en el slot TSH **renderiza perfecto en combate** (validado). El bin
    350 (1 AWG, solo cuerpo) renderiza SIN manos (aparecen al atacar). El
    runtime NO exige nº de AWGs del slot. **Implicación**: para personajes que
    YA existen en B1 HD (CHZ, A19...), el swap nativo con bins HD completos es
    la vía definitiva; NO hace falta portar PS2. **El port PS2→HD solo es
    necesario para personajes que NO existen en HD** (o con traje distinto,
    ej. Tenshinhan B2 PS2).
17. **Geometría HD es RE-TOPOLOGIZADA (confirmado por RE del B3)**:
    `RE_PROGRESO.md` §15-19/§28 del proyecto hermano demostró que el HD usa
    vértices re-ordenados/re-computados con IB propio (triangle strip). Por
    eso **inyectar posiciones PS2 sobre el IB HD DEFORMA** (v12/build_awg_hd_full
    al 98.3% sigue deformando en brazos/manos/cabeza/piernas). La vía correcta
    para port PS2→HD es **reconstruir el bin completo**: sec34 + IB + arms +
    **zona de submesh data** (la pieza que faltaba en `amo0_to_awo.py`).
18. **Submesh data descifrado (17/08, CHZ HD nativo)**: entre arms y sec34 hay
    una zona de **23 descriptores de 0x60B** (un por mesh part). Cada descriptor:
    floats de transformación + `c08=inicio rango A`, `c0C=tamaño A`, `c10=inicio
    rango B`, `c14=tamaño B` (offsets RELATIVOS a otra base, contiguos) + label
    (XCHZ_BODY...) + string debug `max N m`. Los rangos A son CONTIGUOS y cubren
    los buffers. **`amo0_to_awo.py` no regeneraba esta zona** (copiaba la del
    TSH) → hang (no crash) al cargar. Los descriptores se generan desde los mesh
    parts PS2 (23 parts CHZ → 23 descriptores).
19. **Tenshinhan B2 PS2 extraído y mapeado (17/08)**: del `ps2_games\Budokai 2
    (USA)\USR\data_cmn.afs` entry 282 (`#AMB` → #AMO 772KB + #AMT 273KB) y 286
    (AMM). Parseado: **14 mesh parts, 4427 verts, 2944 skin**. Labels: los MISMO
    42 labels base que el TSH HD en el MISMO orden (`TSH_BODY, TSH_WAIST,
    TSH_STMC...`) + 24 labels extra (LHAND 01-38, FACE 01-45, en AWGs separados
    en HD). Esqueleto **1:1** con el HD → viable como primer port PS2→HD con
    traje distinto. Los labels del B2 PS2 se buscan escaneando el AMO completo
    (no solo el inicio). Catálogo B2 PS2: androides 16/17/18/20 = entries
    74/80/84/90, TSH=282/283/286, mini-modelos X??_HEAD ~1.7KB.
20. **GameCube (.iso GC del B1, `ps2_games\DragonBall Z - Budokai [NGC].iso`)**
    NO sirve para models swaps: usa formatos `#ACO/#ACB/#AMB` con `.act/.aco/
    .acm/.acb` (distinto al #AMO0 PS2 y #AWO HD). FST del GCM: offset en 0x424
    (bytes), tabla de 12B/entrada [type u8, nameoff u24, off u32, sz u32],
    strings tras las entradas. Los nombres de archivo NO corresponden a
    personajes (entry 967 "TSH" = #ACM de Trunks). Solo el AFS del **PS2** es
    fuente válida para ports. Detalle: `docs/re/SESION11_PORT_PS2_METODOLOGIA.md`.
21. **✅ DESCRIPTORES DE SUBMESH REGENERADOS (17/08, noche)**: `amo0_to_awo.py`
    reescrito regenera la zona de descriptores con los rangos A/B calculados
    del PS2 (A=vértices sec34 contiguos, B=índices IB con gaps de 2). El bin
    resultante (CHZ PS2 → slot TSH, 5227 verts, 6048 índices) **CARGA SIN CRASH
    en runtime** (antes colgaba con 0xc0000409 al copiar la zona del template).
    Formato definitivo del descriptor (0x60/0x70B según label):
    +00 hdr (0x500 cuerpo/0x400 extremidades), +08 A_start<<8, +0C A_size<<8,
    +10 B_start<<8, +14 (B_size<<8)|1, +18 label 16B, +28 flag tipo por label
    (0x9000000 BODY/0xD000000 manos/0x8000000 HEAD), +2C 0xF000000, +30 "max N m",
    +58 ptr mesh-ref<<8 (0x1158), +5C stride 44<<8 (0x2C00). Los labels PS2 se
    leen de la tabla de labels del AMG (loc en +0x1C, 0x20B por bone) y coinciden
    con los descriptores del template en el MISMO orden (CHZ part i ↔ desc i).
    Mod: `test_chz_ps2_regenerado` (desactivado).
22. **⚠️ BLOQUEADOR REAL DEL PORT (17/08, noche): la cadena mesh-ref/arms**.
    El bin regenerado CARGA (sin hang 0xc0000409) pero **crash 0xC0000005 +
    PM4_DRAW_INDX(0, 63, 0)** al entrar en combate. Causa raíz (corregida por
    el B3, CONSOLIDADO §13.5.14): **NO es regenerar la cadena mesh-ref — es
    CAMBIAR EL TAMAÑO del AWG0 + RE-MAPEAR ARMS**. El B3 probó empíricamente:
    (a) re-mapear arms crashea ("los offsets de los arms NO son rangos del IB
    a dibujar. El IB se dibuja completo; los offsets definen otra información
    (skinning)"); (b) AWG0 crece → crash combate (v4), encoge → no arranca
    (v5), **tamaño FIJO (delta=0) → FUNCIONA (v6)**. La vía correcta:
    decimar el PS2 para caber en los buffers del template + rellenar EN SU
    POSICIÓN (sec34, IB, descriptores) + **arms INTACTOS**.
23. **✅ PIPELINE CORREGIDO (17/08 noche): `amo0_to_awo.py` reescrito con el
    enfoque del B3**: parsea triángulos REALES (FaceType 1=strip zig-zag,
    0=triplete, submeshes en cadena header 0x20) — NO el IB secuencial del
    error de Janemba; decima por (bone, voxel) para caber en los buffers del
    template; rellena sec34/IB/descriptores EN SU POSICIÓN (delta=0, tamaño
    fijo); **no toca arms ni mesh-ref**. CHZ PS2→TSH: 23 parts, 3776 tris
    reales, decimado a 1406 verts/7542 idx (template 3082/8598), bin 166080 B
    idéntico al template.
24. **🔴 CAUSA RAÍZ DEL CRASH = TEX MISMATCH (17/08 noche, VALIDADO EN JUEGO)**:
    todos los tests del port usaban la textura INCORRECTA (x_353 = tex del
    bin 3-AWG 352) con el template 1-AWG (x_350). El par correcto del bin
    1-AWG es x_350+x_351 (catálogo: CHZ 1AWG=1432/1433, 3AWG=1435/1436).
    **Con la textura correcta (x_351) el port CHZ PS2→TSH ENTRA EN COMBATE
    SIN CRASH** (log limpio, mod `test_chz_ps2_texfix`). El modelo se ve
    **deforme** (la decimación por voxel cell=0.148 + descriptores uniformes
    no respetan la topología), pero la reconstrucción PS2→HD es VIABLE.
    El crash 0xC0000005 es SIEMPRE tex mismatch cuando geom y tex no son del
    MISMO par — verificar el par ANTES de testear (no asumir por cercanía).
25. **El port PS2→HD funciona pero DEFORMA** (17/08, validado): la vía completa
    (parseo FaceType + decimación + descriptores A/B uniformes + tamaño fijo +
    arms intactos + **textura del MISMO par**) entra en combate sin crash.
    La deformación viene de: (a) decimación voxel agresiva (cell 0.148,
    1406 de 4313 verts), (b) descriptores con rangos A/B UNIFORMES (no por
    part — el B3 krillin_rec los distribuye uniformemente como workaround).
    Para un port fiel: refinar descriptores por-part reales + decimación
    más conservadora. El swap nativo B1→B1 y el port B3→B1 siguen siendo
    las vías de mejor calidad.
26. **🔴 EL COMPRIMIDO DEBE CABER EN EL entry_size DEL SLOT (19/08, VALIDADO)**:
    el runtime sirve el override leyendo `entry_size` bytes de la entrada
    original del AFS (no el archivo completo). Si el bin COMPRIMIDO (lzx) de
    un port/swap supera ese tamaño, el stream se TRUNCA → descompresión
    corrupta → **crash 0xC0000005** al cargar el personaje. El padding del
    archivo a un tamaño mayor NO ayuda (el juego solo lee entry_size).
    Ejemplo: Broly B3→Nappa — tex comprimido 30572 B vs slot 1388 (18632 B) →
    crash; geom 85030 ≤ 283952 → OK. Gero→TSH funcionó porque su tex (24538 B)
    cabía en el slot 2451 (33504 B). `swap_b1.install()` AHORA valida esto y
    falla con error claro en vez de instalar un mod roto. Para portar un
    personaje con muchas texturas, elegir un destino con slot tex ≥ comprimido
    (Piccolo 1767=33702, Goku 1758=49574, Cell 357=49774) o reducir el AZT.
27. **Thread joinable destruido = std::terminate (19/08, VALIDADO)**: el
    `LauncherDialog` se auto-destruye al pulsar Play (`ImGuiDialog::Draw` →
    `delete this`). Su miembro `ModPipeline` tiene un `std::thread worker_`
    que queda joinable tras cada operación (catalog/port/swap) → al destruir el
    dialog, el destructor de `std::thread` llama `std::terminate` (crash
    determinista "Play tras abrir Mods"). Fix: `ModPipeline::Shutdown()`/destructor
    hacen join + se llama antes de destruir el dialog en el callback de Play +
    try/catch en el worker y en el launch diferido. Recompilado 19/08 15:58.
28. **🔴 EL PORT/SWAP DEBE CUBRIR TODOS LOS TRAJES DEL DESTINO (19/08, VALIDADO)**:
    el runtime carga el traje POR DEFECTO del personaje en un par de bins que
    NO siempre es el primero del bloque. Piccolo por defecto usa **1768/1769**
    (4110 verts), NO 1766/1767 (4337) que el catálogo marca como "Traje 1".
    Instalar el port SOLO en el par seleccionado → no se ve en combate.
    **Fix**: `swap_b1.install()` acepta `dest_pairs` (lista de pares geom:tex)
    y el pipeline (`launcher_mod_pipeline.py`) expande el `--dest-label` a TODOS
    los pares del personaje destino desde `characters.cat`. El override se
    escribe en todos los trajes y todos los `data_*.afs`. Se omiten (con aviso)
    los pares cuyo slot no admita el comprimido. Pasar `--dest-pairs` desde la
    CLI/launcher (el C++ ya lo propaga vía `--dest-label`).
29. **🔴 `_popen` abre ventana CMD y falla con comillas (19/08, FIX PORTADO DEL B3)**:
    el swap "abría un CMD que no hacía nada" porque `_popen` pasa el comando a
    `cmd.exe /c`, que falla al parsear comillas cuando el comando empieza con `"`
    (ej. `"python" ...`) con "sintaxis de la etiqueta del volumen", y además
    muestra una ventana de consola. **Fix**: `ModPipeline::RunAsync` ahora usa
    **`CreateProcess`** (sin cmd.exe) con `CREATE_NO_WINDOW`, redirigiendo
    stdout+stderr a un pipe — igual que el proyecto hermano B3
    (`DBZ Budokai 3 HD Collection\github\src\launcher\mod_pipeline.cpp`).
    También escribe `pipeline_cmd.log` (junto al exe) para depurar. Recompilado
    (exe 19/08 ~17:00).

---

## REFERENCIAS RÁPIDAS

- Personajes→bins: `docs/referencias/PERSONAJES_BINS.md`. TSH: 2445(#ACM)→
  2450(#AWO) 2451(#AZT). Goku: 368(#ACM)→380/381/536. X19G(Andr.19): 43(#CSK)→
  45/47/49(#AWO). Set completo del personaje: `docs/re/ANIMACIONES_MOVESETS_HD.md`.
- B1 PS2 models: `DBZ Budokai 3 HD Collection\modding resources update\Budokai 1
  Models Converted to AMB\XXX00.bin`.
- **B2 PS2 models**: `ps2_games\Budokai 2 (USA)\USR\data_cmn.afs`. Catálogo:
  `mod center hd\analizadores\catalog_b2_ps2.py`. TSH=282/283/286 (282=AMO+AMT
  traje alternativo, 283=XTSH, 286=AMM), androides 16/17/18/20=74/80/84/90,
  Goku=134/171/172, mini-modelos X??_HEAD ~1.7KB. Escanear labels `X??_BODY`
  en el AMO COMPLETO (no solo el inicio — el B2 los tiene dispersos).
- Formato de mods: `docs/tutoriales/FORMATO_MODS.md`.
- **LEER ANTES DE RETOMAR**: `docs/re/SESION6_PORT_B2_B1_HD.md` (pipeline v8,
  bloqueador, mesh group completo) y `docs/planes/PLAN_PORTS_FUNCIONALES.md`.