# PLAN: PORTS FUNCIONALES VÍA OBJ TO AMG → HD (2026-08-15)
> Copyright (c) NovaPowers. Released under the MIT License. Firmado por NovaPowers.
>

> Pipeline de retopología de la comunidad y su adaptación al HD.
> Lección: el mesh group HD se GENERA, no se presta ni se reconstruye a mano.

---

## 1. LA LECCIÓN (qué rompe los ports)

| Enfoque | Resultado | Por qué |
|---|---|---|
| Swap interno B1→B1 (bin nativo) | ✅ | mesh group nativo coherente |
| Inyectar geometría en bin de otro personaje | ❌ crash | mesh group host + geometría ajena |
| Reconstruir mesh group a mano | ❌ | desastre Janemba (B3) |

El mesh group (mesh-ref blocks + arms) lo genera el desarrollador al
convertir PS2→HD. **No se presta ni se reconstruye a mano.** La única vía
validada para mismo personaje es el atajo v8/v12 (sec34 nativo + coords
vecinas, ver AGENTS.md). Para personaje distinto: pipeline OBJ→AMG→HD.

---

## 2. PIPELINE DE LA COMUNIDAD (OBJ to AMG v0.92)

### Qué hace
1. Lee OBJ (v/vt/vn/f).
2. Por cada objeto `o` → un mesh part: `model_part_header.bin` (160B) +
   triángulos expandidos (3 verts 48B c/u `[pos3, 4B, nrm3, 4B, uv2]`) +
   `triangle.bin` (176B). `mesh_size = tris×16 + 0x60`.
3. Ensambla AMG: `amg_header.bin` (160B) + tabla mesh parts + parts +
   `amg_end.bin` (64B).

### Templates binarios (formato exacto)
- **model_part_header.bin** (160B): `B5 01` (type1) + `BD 29` (type2
  **0x29BD**, sello B3) + identidad + `0x8C: 60 00 00 00`.
- **triangle.bin** (176B): header `08 00 00 14` + 3 verts 48B.
- **amg_header.bin** (160B): `#AMG` + +0x14:0x20 + +0x18:03 mesh groups.

### Conexión con el HD
El type2 **0x29BD** del PS2 es EXACTAMENTE el del B3 HD. El B1 HD usa
**0x1BD/0x11BD**. → mesh part header PS2 y HD comparten estructura; el
re-layout PS2→HD solo cambia type2 + endianness.

---

## 3. EL PLAN

### Fase A — `obj_to_awg_hd.py` (vía correcta)
1. Lee OBJ (v/vt/vn/f).
2. Mesh part header con type2 **0x1BD** (B1 HD).
3. Triángulos expandidos a vértices 44B stride HD.
4. Ensambla #AWO: header AWO (flag 0x2) + labels (esqueleto destino) +
   ejes 80B (quat+pos destino) + mesh group GENERADO + sec34 44B + IB.
5. Empaqueta #AWO + #AZT.

### Fase B — Flujo traductor universal
```
IW/B3 PS2 → [b3iw_to_b1_ps2.py] → B1 PS2 #AMO
B1/B2 PS2 → directo
   → [AMO Decompiler] → OBJ (malla+skin+esqueleto)
   → [Blender re-riggear a esqueleto B1 HD] (solo esqueletos distintos)
   → [OBJ to AWG HD] → #AWO HD (mesh group generado)
   → instalar en slot → ✅
```

### Fase C — Casos
1. Mismo personaje B1→B1 HD: esqueleto idéntico, solo re-layout.
2. Personaje distinto (Goku→TSH): re-riggear en Blender + OBJ→AWG HD.
3. B3 HD→B1 HD: usar #AWO del B3, cambiar flag+type2; si el mesh group es
   compatible (mismo personaje) funciona directo.

---

## 4. ESTRUCTURA MESH PART HEADER HD (mapeada, 80B)

```
+00 4×escala (128.0)   +10 4×weights [0.8,0.75,0.7,1.0]
+20:0 +24:5 +28:0 +2C:5
+30 índice incremental (agrupación 0-3)   +34 0xFFFFFFFF
+38/+3C type2 (0x1BD mesh / 0x11BD alt) duplicado
+40/+44 stride 0x44   +48/+4C 0
```
PS2 (160B): `B5 01` + `BD 29` + identidad + `0x8C: mesh_size`. Relación =
re-layout LE→BE + type2 0x29BD→0x1BD.

---

## 5. MAPA COMPLETO DEL AWG0 HD (Piccolo, funciona)

```
+0x040  labels (27×32B)          [XTSH_BODY, PIC_WAIST, ...]
+0x5C0  mesh part headers (10×80B)
+0x910  mesh-ref blocks / ejes (19×80B)  [quat, pos, sello, arm_ptr, child/sib/parent]
+0xF00  zona intermedia (mesh-ref + arms)
+0x23A0 sec34 (vértices 44B)
+0x2E608 IB (índices u16)
+0x34250 bones
```

Mesh-ref block / eje (80B): `quat[xyz,w] + pos[xyz] + sello(+0x30:
0x9000020C mesh/0x204 shadow) + arm_ptr(+0x34 REL AWG) + child/sib/parent`.
10 mesh part headers ↔ 19 ejes (algunos ejes solo huesos sin geometría).

**Pendiente**: mapear la relación exacta mesh part header → mesh-ref block →
arm para generarlo coherente con los triángulos.

---

## 6. RECURSOS

- `mod center hd/src_comunidad/OBJ_to_AMG_v0.92_source.zip` + templates
- `mod center hd/scripts_gero/` (port Gero que funcionó)
- `mod center hd/parsers/lib_ps2/` (extract_geometry, pose_matrix)
- `mod center hd/conversores/retarget_hd.py` (align_joint)
- B3: `awo_tools/build_janemba3.py` (referencia de qué NO hacer)
- Discord: ReXGlue Project + Budokai Modding Community