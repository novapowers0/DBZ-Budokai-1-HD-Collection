# ESTUDIO TRANSVERSAL: GOKU EN TODOS LOS JUEGOS (2026-08-14)
> Copyright (c) NovaPowers. Released under the MIT License. Firmado por NovaPowers.
>

> Objetivo: entender el formato de modelos de TODA la franquicia para construir
> el "traductor universal" IW/B3/B2/B1 → B1 HD. Método: comparar Goku de cada
> juego (mismo personaje aísla las diferencias de FORMATO).

---

## 1. RESUMEN DE FORMATOS (verificado en bins reales)

| Juego | Contenedor | Modelo interno | Notas |
|---|---|---|---|
| B1 PS2 | `#AMO` directo | `#AMG` (52-61 bones) | Goku en entradas 380/381/536 |
| B2 PS2 | `#AMB`→`#AMO` @+64 | `#AMG` (42 bones) | **IDÉNTICO al B1** (mismo #AMO/#AMG) |
| B3 PS2 | `#AMB`→`#MDD` | `#AMO` fragmentados | Complejo, Goku distribuido |
| B1 HD | `#AWO` directo / `#ACM` | `#AWG` (42-51 bones) | El que usamos |
| B3 HD | `#AMB`→`#AWO` @+0x40 | `#AWG` (42-51 bones) | Casi compatible con B1 HD |

## 2. HALLAZGOS CLAVE

### 2.1 B1 y B2 PS2 comparten el formato #AMO/#AMG EXACTO
B2_171 (Goku): 12 AMGs, labels XGOK_BODY + GOK_L0x_LHAND/RHAND; AMG0 3573 verts,
42 bones. **B2 → B1 HD usa el MISMO pipeline que B1 → B1 HD** (el traductor cubre
ambos). ⚠️ PERO: el traje puede diferir (TSH B2 ≠ TSH B1) — verificar SIEMPRE con
labels (AGENTS.md).

### 2.2 B3 PS2 usa #MDD (formato distinto y fragmentado)
`#AMB`→tabla de bloques(5×12B@+0x20)→`#MDD`(contiene #AMT + múltiples #AMO). El
Goku B3 está distribuido en varios #AMO → paso extra: desfragmentar el #MDD o usar
`b3iw_to_b1_ps2.py` (comunidad).

### 2.3 B1 HD y B3 HD comparten el formato #AWG
- B1 HD: `#AWO` directo (personaje) o `#ACM` (armatura/esqueleto, NO malla).
- B3 HD: `#AMB`→`#AWO` @+0x40 → `#AWG` internos.
- Ambos usan sec34 en +0x28 (offsets RELATIVOS al AWG). Diferencias de formato:
  flag AWG +0x0C: B1=0x2, B3=0x4; type2 mesh part +0x3C: B1=0x1BD/0x11BD, B3=0x29BD.

### 2.4 PS2 tiene MALLA + SKIN; HD usa el SKIN
- PS2: vértices de malla (absolutos) + skin (ch_loc = coords LOCALES al hueso).
- HD: guarda coords LOCALES al hueso (igual que el skin PS2).
- **La conversión es re-layout + re-mapeo de bones** (no transformación compleja),
  salvo que el esqueleto difiera en rotación (entonces inv_rigid/align_joint).

## 3. HERRAMIENTAS EXTERNAS PARA EL ESTUDIO

- **DarioSamo/LibXenoverse** (C++): `ESK` (esqueleto) con `transform_matrix[16]`
  + `skinning_matrix[12]` = bind pose para inv_rigid; EMDExportFBX exporta
  malla+esqueleto a FBX.
- **eherr/anim_utils** (Python): `run_retargeting.py` mapea huesos por nombre;
  **`align_joint`** alinea eje twist(y)+swing(x) origen→destino (el retargeting
  de rotación que esqueletos diferidos necesitan); `create_correction_map`,
  `auto_scale_factor` (escala por altura cadera→pie).
- **Nyxifer-prog/XV2AutoPorter** (Python): `.emd/.esk/.ean` Xenoverse 2 → FBX+XML.
- **SamuelDBZMAAM/DBZ-Budokai-3-Modding-Tool**: B3 Mod Tool.py (669 líneas) —
  conversión B3→B1, AMT editing, AMB combiner, aura editing. README: "B4 01 lines
  can be converted to be shadable" (conecta con type2 0x1BD vs 0x29BD).

## 4. RETARGETING INV_RIGID (referencia teórica)

1. Mapear huesos por nombre (generate_joint_map).
2. Alinear rotaciones (align_joint: twist y + swing x) para esqueletos 90-180°.
3. Escalar por proporción (auto_scale_factor).
4. Transformar vértices: `local_dest = inv(bind_dest[bone]) * bind_src[bone] * local_src`
   (= inv_rigid en build_awo_from_json.py).
5. El ESK de Xenoverse guarda las matrices de skinning (bind pose) directamente.

### 4.1 MEDICIÓN: GOK B2 PS2 → TSH B1 HD (esqueletos diferidos)
Rotaciones GOK→TSH medidas con align_joint (retarget_hd.py):
WAIST 90°, STMC 180°, CHEST 90°, L00_RHAND 114°, NRA 180°, NECK 120°, HEAD 90°.
Corrección: `local_dest = inv(bind_dest) * R_align * bind_src * local_src` con
`R_align = align_joint(ejes_src, ejes_dest)`. (GOK vs TSH difieren en
WAIST/CHEST 90° y STMC/NRA 180° — el align_joint solo hace falta si el esqueleto
difiere en rotación.)

## 5. DATOS DE GOKU (por juego)

| Fuente | Archivo | Verts AMG0 | Bones | Labels |
|---|---|---|---|---|
| B1 PS2 | ent_380 (#AMO) | 9212 | 61 | XGOK_BODY |
| B1 PS2 | ent_381 (#AMO) | 10109 | 59 | XGOK_BODY |
| B1 PS2 | ent_536 (#AMO) | 9235 | 52 | XGOK_BODY |
| B2 PS2 | B2_171_amo (#AMO) | 3573 | 42 | XGOK_BODY |
| B1 HD | slot 368 (#ACM) | — | — | XGOK_BODY (armatura, NO malla) |
| B3 HD | ent 264 (#AMB→#AWO) | — | — | XGOK_BODY |

## 6. ARQUITECTURA DEL TRADUCTOR UNIVERSAL

```
IW/B3 PS2 → [b3iw_to_b1_ps2.py] → B1 PS2 #AMO ─┐
B2 PS2 → (directo, mismo formato) ──────────────┤
B1 PS2 → (directo) ─────────────────────────────┤
                                                ▼
                         B1 PS2 #AMO/#AMG → [B1 PS2→B1 HD] → B1 HD #AWO
```

Pasos: (1) b3iw_to_b1_ps2.py (existe, decompilado del exe); (2) B1 PS2→B1 HD = el
pipeline v8/v12 (estructura Piccolo: 1 AWG por AMG); (3) port_b3_to_b1.py
(flag+type2+bones); (4) B2 directo.

## 7. 🔴 LECCIÓN DEFINITIVA (sesión 5, noche)

**El bin Piccolo que "funcionó" NO fue un port — fue un SWAP INTERNO B1→B1**
(un bin Piccolo NATIVO del B1 HD, de `afs_out`, instalado en el slot).

**El mesh group del HD es generado por el desarrollador al convertir PS2→HD.**
NO se puede tomar prestado de otro personaje (crash) ni reconstruir a mano
(desastre Janemba B3). La vía correcta (comunidad) = pipeline de retopología que
GENERA el bin completo coherente:
```
OBJ → OBJ to AMG (construye mesh group) → re-layout PS2→HD
```
El re-layout de bytes + mapeo de bones es necesario pero NO suficiente: el mesh
group debe generarse coherente con la geometría (OBJ to AMG / AMBStudio adaptados
al HD). → Estado actual en AGENTS.md (v12 mismo-personaje; retopología pendiente).