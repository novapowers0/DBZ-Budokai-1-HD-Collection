# SESIÓN 6: PORT B2→B1 HD — CONOCIMIENTO VALIDADO (2026-08-15)
> Copyright (c) NovaPowers. Released under the MIT License. Firmado por NovaPowers.
>

> Resumen del port PS2→B1 HD. CORRECTO con v10-v12 (sec34 stride 44,
> offsets REL al AWG0, modelo base = B1 PS2). Ver AGENTS.md.

---

## 1. RESUMEN EJECUTIVO

| Resultado | Estado |
|---|---|
| Pipeline mismo personaje (v8/v12) | ✅ FUNCIONA (no crash, jugable) |
| Port personaje distinto (GOH/SS2) | ❌ bloqueado (mesh group nativo) |
| Formato mesh group HD | 🔬 Mapeado completo |
| Retopología IB / mesh group manual | ❌ caos / crash |

**v12 (estado actual)**: Tenshinhan **B1 PS2** `TSH00.bin` → slot 2450,
instalado en `mods/test_tsh_b2_stride16`. 4059/4272 slots reemplazados
(95%), mesh group 100% intacto, solo posiciones cambiadas (media 0.59).
**Deformidades residuales**: pies, muñequeras, cabeza, piernas (pocos
vértices → vecino aproxima mal); cintura/abdomen bien.

---

## 2. PIPELINE QUE FUNCIONA (v8/v12) — obj_to_awg_hd.py / build_awg_hd_full.py

```
python build_awg_hd_full.py <bin_hd_base_mismo_personaje.awo> <modelo_ps2.amb> <out.bin>
```

### Estrategia (ATAJO validado)
1. Base = bin HD nativo del MISMO personaje (mesh group coherente).
2. sec34 nativo COMPLETO preservado (orden + mesh group + UVs + normales + bones).
3. SOLO se sustituyen las coords de cada slot por el **vecino world PS2 más
   cercano** (pool GLOBAL puro), transformado a local del hueso (inv_rigid).
4. Mesh group/IB nativo intacto → dibuja la topología nativa.

### Mejoras clave
1. **UMBRAL 1.5**: slot se reemplaza solo si el vecino PS2 está <1.5; si no,
   quedan coords nativas.
2. **Decimación voxel del pool PS2** (2944→953): evita slots mapeando al mismo
   vecino (triángulos degenerados).
3. **Pool GLOBAL puro** (v12): el bone_map por labels del B1 PS2 está MAL
   (mapea 2→1, 4→2...); restringir por bone empeora (47% vs 95%).

### Limitación
Como el modelo es casi idéntico al nativo (mismo personaje, misma pose), el
resultado casi no difiere visualmente del nativo. El caso VALIDA el pipeline
pero NO demuestra un port de personaje distinto.

---

## 3. 🔴 EL BLOQUEADOR (confirmado)

**"El runtime dibuja con el mesh group/IB del bin ANFITRIÓN, nunca con la
geometría inyectada."**

| Enfoque | Resultado | Por qué |
|---|---|---|
| v4 re-layout coords | deforme | orden arbitrario |
| v6/v8/v12 sec34 nativo + coords vecinas | ✅ funcional | geometría ≈ nativa |
| r1 retopología (sec34+IB del PS2) | ❌ caos | runtime usa SU IB |
| retargeting GOH→TSH (label+align) | ❌ TSH deforme | mesh group TSH + geometría GOH |
| build_awg_hd_full (mesh group completo) | ❌ crash 0xC0000005 | formato jerárquico incompleto |

**Lección**: el mesh group/IB del bin está ligado a la geometría del
personaje. Solo funciona inyectar coords cuando la geometría es casi idéntica.
Para personaje distinto hay que reconstruir el bin COMPLETO coherente
(mesh group + IB + geometría) con herramientas de comunidad (OBJ→AMG→HD,
AMBStudio, .aerithdevs). NO reinventar el mesh group a mano.

---

## 4. FORMATO DEL MESH GROUP HD (mapeado, sesiones 6-7)

Verificado en bins nativos Piccolo (funciona) y TSH. Detalle en
SESION7_MESH_GROUP_COMPLETO.md y AGENTS.md.

### Header AWG
```
+0x1C nombre (XTSH_BODY)  +0x20/+0x24 materiales
+0x28 sec34 off (REL AWG0)  +0x2C sec34 size  → n_sec = size//44
+0x30 post/IB off (REL AWG0)  +0x34 size
+0x38 siguiente zona (REL)  +0x3C bones  +0x40 nombre 32B
```

### Mesh part header (80B)
`4×128.0 + weights[0.8,0.75,0.7,1.0] + [0,5,0,5] + grp_idx(0/1/2,FFFF=sombra)
+ 0xFFFFFFFF + type2 (0x1BD/0x11BD)×2 + stride 0x44×2 + 0,0`

### Eje / mesh-ref block (80B)
`quat[xyz,w] + pos[xyz] + 4×1.0 + sello(+0x30) + arm_ptr(+0x34, REL AWG0)
+ child(+0x38) + sibling(+0x3C) + parent(+0x40)` (→ labels)

### Arm block (20B) — CLAVE
`[bone_idx, fin_IB, 0, ini_IB, 0]` — ini/fin = byte offsets DENTRO del IB.
Rangos se solapan (triángulos comparten vértices). TSH: 8 bones con mesh
(0,9,16,20,24,27,31,37).

### Vértice sec34 (44B)
`pos3 | peso@+12 | BONE u32@+16 | nrm3@+20 | 0xFFFFFFFF@+32 | uv@+36/+40`

---

## 5. LAS MANOS PERFECTAS = AWGs NO TOCADOS

TSH B1 HD nativo = **23 AWGs**: AWG0 cuerpo (XTSH_BODY, el único reescrito),
AWG1-16 dedos, AWG17-22 caras → intactos → perfectos. El port solo toca AWG0.

---

## 6. HERRAMIENTAS

| Herramienta | Función | Estado |
|---|---|---|
| `conversores/build_awg_hd_full.py` | v12 (pool global, sec34 nativo) | ✅ validado estructuralmente |
| `conversores/obj_to_awg_hd.py` | v8 (mismo personaje) | ✅ validado en juego |
| `conversores/port_personaje_a_tsh.py` | retargeting label+align | 🔬 bloqueado |
| `conversores/build_awg_retopo.py` | retopología sec34+IB | ❌ caos |
| `conversores/retarget_hd.py` | align_joint/retarget_local | ✅ matemáticas |
| `parsers/lib_ps2/extract_hd_mats.py` | world mats HD | ✅ validado |
| `src_comunidad/` | OBJ to AMG, AMBStudio, Model-Rig Extractor | pipeline retopología |

---

## 7. PRÓXIMOS PASOS (la vía definitiva)

Para portar personaje DISTINTO (Goku SS2):
1. Adaptar **OBJ to AMG v0.92** para generar mesh group PS2 desde OBJ.
2. Re-layout PS2→HD (type2 0x29BD→0x1BD, ejes, arms, sec34 44B, IB u16).
3. Generar el AWG0 completo con mesh group GENERADO (no prestado).
4. Afinar v12: decimar pool antes del matching, penalizar bone, suavizado.

Recursos: OBJ to AMG v0.92, AMO Compiler/Decompiler, AMG to OBJ V2,
B3-IW Converter (en `src_comunidad/` y `modding resources`).

---

## 8. ESTADO ACTUAL INSTALADO

- **v12** (B1 PS2 TSH00 → slot 2450): instalado y activo en
  `mods/test_tsh_b2_stride16`. Deformidades en extremidades pendientes.
- Modelos PS2: `Budokai 1 Models Converted to AMB\TSH00.bin` (B1, correcto),
  `ent_282_amo.bin` (TSH B2, traje distinto — NO usar), Goku SS2 (objetivo).
- Bins generados en `%TEMP%\opencode\`.