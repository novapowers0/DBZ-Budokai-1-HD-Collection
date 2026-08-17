# mod center hd — Herramientas del pipeline de modelos (DBZ Budokai HD Collection / B1)

> Actualizado: 16/08/2026 (port B3-B1 funcional + sesión 5 — RE definitiva de PS2/HD + reorganización).

---

## 1. QUÉ ES

Herramientas propias (Python) para portear modelos entre los juegos Budokai
y el **HD 360 (ReXGlue)**. Adaptadas al ecosistema del B1 HD, independientes
del proyecto B3.

## 2. ESTRUCTURA DE CARPETAS

```
mod center hd/
├── analizadores/        # Análisis / RE de bins HD
│   └── analyze_b1_hd.py
├── conversores/         # Conversión de modelos (PS2/B3 → HD)
│   ├── build_b1_goku_full.py      # PS2→HD (inyección en template)
│   ├── build_b1_reconstruct.py    # PS2→HD (reconstrucción sobre plantilla Piccolo)
│   ├── port_b3_to_b1.py           # B3 HD→B1 HD (re-mapeo de bones por labels)
        |-- port_b3_to_b1_v2.py   # PORT B3-B1 VALIDADO (sellos + materiales + alpha)
        |-- install_b3_to_b1.py   # Pipeline automatico B3-B1 (port + instalar mod)
│   ├── build_awo_from_json.py     # FBX JSON→HD (inv_rigid)
│   ├── b3iw_to_b1_ps2.py          # B3/IW→B1 PS2 (re-layout headers)
│   └── emd_to_awo_hd.py           # EMD→HD (Xenoverse/SDBH WM)
├── swaps/               # ✅ MODEL SWAPS B1→B1 automatizados (100% funcional)
│   ├── swap_b1.py                # Extraer par geom+tex → comprimir → instalar mod
│   └── README.md                 # Documentación de uso
├── exportadores/        # Exportación (OBJ, DDS, FBX)
│   ├── export_sec34_obj.py
│   ├── azt_to_dds.py
│   ├── fbx_ascii.py / fbx_parser.py
├── parsers/             # Parsers de formato
│   └── lib_ps2/         # PS2: extract_geometry, convert_personaje, pose_matrix,
│                        #       extract_hd_mats, parse_ps2_mesh
├── scripts_gero/        # EL PORT GERo B3→B1 QUE FUNCIONÓ (referencia)
│   ├── rerig_b3_to_b1.py   # Re-mapea bones de VÉRTICES (+18)
│   ├── rerig_arms.py       # Re-mapea bones de ARMS (mesh-ref blocks)  ★ CLAVE
│   ├── rerig_fino.py / rerig_fino2.py  # Retargeting con bind poses
│   └── gero_0_AWO.bin      # Bin HD del Gero B3 (funciona)
├── src_comunidad/       # Scripts de la comunidad (descargados, referencia)
└── referencias/         # Docs de apoyo
```

## 3. 🔴 HALLAZGOS CLAVE (sesión 5 — RE definitiva)

### 3.1 PS2 y HD guardan coords LOCALES al hueso
- **PS2**: `coords_local` (locales al bone index). Ej. Piccolo PS2 part0 vert0
  → bone 18, coords `(0.7237, 0.0745, 0.7678)`.
- **HD**: también `coords_local`. Ej. Piccolo HD slot0 → bone 8,
  `(-0.3634, 0.4190, 0.0066)`.
- **La conversión PS2→HD NO cambia las coords locales** — solo re-layout de
  bytes (LE→BE) + re-mapeo de bones si el esqueleto difiere.

### 3.2 Layout del vértice HD (stride 44, big-endian)
```
+00 pos.x +04 pos.y +08 pos.z
+12 peso (float, ej. 0.8)
+16 BONE (u32)          ← AQUÍ (no en +20)
+20 nrm.x +24 nrm.y +28 nrm.z
+32 0xFFFFFFFF
+36 uv.x +40 uv.y
```
Verificado en bins nativos PIC y TSH. **B1 y B3 HD usan el MISMO layout.**

### 3.3 Campos del header AWG (B1 y B3 HD iguales)
```
+0x28 vb off  → zona de VÉRTICES (sec34)
+0x2C vb size → tamaño del sec34
+0x30 ib off  → index buffer
+0x34 ib size → tamaño del IB
+0x38 bones off / restart
```

### 3.4 El port funcional del Piccolo (clave)
El mod `test_piccolo_on_tenshinhan` que SÍ funcionó reconstruye el bin con
**1 AWG por AMG del PS2** (19 AWGs: XPIC_BODY + dedos + caras), NO inyecta en
el template. La estructura del personaje origen es la correcta.

### 3.5 El port del Gero B3→B1 (referencia, scripts_gero/)
El Gero B3 HD ya era un #AWO con su estructura (16 AWGs). El port funcionó
re-mapeando los bones:
1. **Vértices** (bone en +18 del stride 44) → `rerig_b3_to_b1.py`
2. **ARMS de los mesh-ref blocks** (bone_n que conecta mesh part → hueso)
   → `rerig_arms.py` ★ — sin esto el modelo se ve mal/crashea

## 4. USO RÁPIDO

```bash
# Analizar un bin HD
python analizadores/analyze_b1_hd.py <bin.awo>

# Port B3 HD → B1 HD (re-mapeo de bones por labels) — vía del Gero
python conversores/install_b3_to_b1.py <awo_b3.bin> <azt_b3.bin> --mod <nombre>   # PORT B3-B1 AUTOMATICO (validado Gero)

# ✅ MODEL SWAP B1→B1 (automatizado, 100% funcional)
python swaps/swap_b1.py --list                                  # catalogar personajes
python swaps/swap_b1.py --origen X19G --dest 2450 --tex 2451   # Android 19 → Tenshinhan

# Exportar geometría a OBJ (validar en Blender)
python exportadores/export_sec34_obj.py <out.awo> <out.obj>

# Extraer texturas
python exportadores/azt_to_dds.py <personaje.azt> <carpeta>

# Instalar: comprimir con /N:2048, pad al slot, copiar a
#   mods/<mod>/us/data_sp.afs/2450/geom.bin
```

## 5. ESTADO DEL PORT (Goku→Tenshinhan)

| Versión | Enfoque | Resultado |
|---|---|---|
| v13-v15 | Inyección en template Gero (6 AWGs) | deforme |
| v16-v18 | Retarget inv_rigid + layout + offsets | deforme (pero avances) |
| v19 | Reconstrucción sobre plantilla Piccolo | amalgama de triángulos |
| **Gero B3** | Re-mapeo de bones (vértices + arms) | ✅ FUNCIONA |

**Lección**: el formato es compartido entre juegos. Para portar B3→B1 solo
hay que re-mapear bones por labels (vértices + arms). El retargeting de
geometría (inv_rigid) es para cuando el esqueleto difiere mucho.

## 6. HERRAMIENTAS DE LA COMUNIDAD ADAPTADAS (src_comunidad/)

Copiadas del `mod center` del B3 para estudiar y adaptar al HD:

| Script | Fuente | Función |
|---|---|---|
| `OBJ_to_AMG_v0.92_source.zip` | OBJ to AMG v0.92 | OBJ→AMG PS2 (retopología) |
| `obj_to_amg_basic_functions.py` | OBJ to AMG v0.92 | Funciones base (hex/offset) |
| `AMO_Compiler.py` / `AMO_Decompiler.py` | Model Compiling Tools | Parseo/build AMO |
| `amb_model.py` | B3_IW Model Converter | Empaquetar AMB |
| `Bone Addition Tool.py` | Bone Addition Tool v1.02 | Añadir huesos al AMO |
| `axis_data.py` | BoneAxis Display | Datos de ejes |
| `Model Merger Tool.py` | Model Merger | Merge de modelos (LGBT) |
| `Model-Rig Extractor.py` | Model Rig Toolset | Skin→malla (ch_loc/sb_loc) |
| `Model-Rig Remover.py` | Model Rig Toolset | Quitar rig |
| `Animation Editor.py` | Animation Editor | Editar animaciones |
| `B3-to-SB2.py` | Shin Budokai 2 Tools | B3→SB2 (layout mesh parts) |
| `bcm_b3_transform.py` / `bsk_b3_transform.py` | Transformation Input | Transformar esqueleto |

## 7. HOJA DE RUTA (resumen)

Ver `docs/planes/HOJA_DE_RUTA_SWAPS.md`:
1. **Swaps funcionales**: B1→B1 ✅ (Piccolo), B3→B3 (nuevo), B3→B1 (crash, dejar para el final).
2. **Mejorar herramientas**: adaptar las de la comunidad al HD.
3. **Port PS2→HD a gran escala**: con la estructura del Piccolo (1 AWG por AMG).

## 8. RETARGETING DE ESQUELETOS (retarget_hd.py)

**Problema**: los esqueletos de juegos distintos tienen rotaciones diferidas
(STMC/CHEST 90°, LARM 180°). Copiar coords locales directas deforma.

**Solución** (`conversores/retarget_hd.py`, basado en align_joint de
anim_utils/DFKI):
```python
from retarget_hd import retarget_local
local_dest = retarget_local(bind_src, bind_dst, local_src, bone_src, bone_dst)
# = inv(bind_dest) * R_align * bind_src * local_src
```
- `align_joint`: alinea el eje twist (y) + swing (x) del hueso origen al
  destino.
- Medición real (GOK B2 → TSH B1): WAIST 90°, STMC 180°, CHEST 90°, HEAD 90°.

**Referencias externas** en `src_comunidad/`:
- `referencia_retarget_analytical.py`, `referencia_retarget_utils.py`
- `referencia_run_retargeting.py` (pipeline de anim_utils)
- `referencia_libx_ESK.h` (esqueleto Xenoverse con matrices de skinning)
- `B3_Mod_Tool_full.py` (modding tool completo de SamuelDBZMAAM)
