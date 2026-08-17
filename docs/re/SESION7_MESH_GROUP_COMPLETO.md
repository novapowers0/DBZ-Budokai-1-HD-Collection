# SESIÓN 7: MAPEO DEFINITIVO DEL MESH GROUP HD (2026-08-15)
> Copyright (c) NovaPowers. Released under the MIT License. Firmado por NovaPowers.
>

> RE del AWG0 del TSH nativo (slot_2450). CORREGIDO en v10 (2026-08-15):
> el sec34 es stride 44 y los offsets del header AWG0 son RELATIVOS al
> AWG0. Ver AGENTS.md sección "FORMATO HD".

---

## 1. ESTRUCTURA FÍSICA DEL AWG0 (verificada byte a byte)

TSH nativo slot_2450 (#AWO directo, AWG0 @0xB20, size 221408 B):

```
0xB20  header AWG0 (0x50)          +0x28 sec_off +0x2C sec_size
0xB60  label XTSH_BODY (16B)       +0x30 post_off +0x34 post_size
0xB70..0x10A0  labels interleaved (tabla de huesos)
0x10A0..0x1410  12 mesh part headers (0x50B c/u)
0x1460..0x2130  42 ejes (0x50B c/u) jerarquía child/sib/parent
0x2180..0x24C8  42 arms (0x14B c/u) [bone, fin, 0, ini, 0]
0x2FF0..0x30E30 sec34 = VÉRTICE stride 44 (4272 verts) ← AWG0+0x24D0
0x30E30..0x36B6A zona post = IB u16 + sub-mesh data
0x36B6A..0x36C00 zona bones (índices u16)
```

## 2. SEC34 = VÉRTICE STRIDE 44 (CORRECCIÓN v10; "stride 16" fue error)

- Layout 44B: `pos(3f) + weight@+12 + BONE@+16 (u32, válido 1-34) + nrm@+20 +
  0xFFFFFFFF@+32 + blend@+36 + uv@+40`. Ver AGENTS.md.
- `n_sec = sec_size//44 = 4272`. TSH nativo = 4272 verts.
- La lectura "stride 16" en 0x24D0 daba NaNs/padding; la de 44B en
  `AWG0+0x24D0=0x2FF0` da bones válidos → ES el vértice real.
- El sec_off/post_off del header son RELATIVOS al AWG0 (0x2FF0 / 0x30E30).

## 3. ZONA POST = IB u16 (los arms apuntan a rangos de bytes)

- body IB (post+6576..) = 8645 índices válidos (max 3896, 0 FFFF).
- prefix post[0..6576] = separadores 0xFFFF de sub-mesh.
- Arms `[bone, fin, 0, ini, 0]` apuntan a rangos del post:
  bone 0→[6576..7088], 9→[6640..7968], 16→[6704..8080], 20→[6768..8192],
  24→[6832..8496], 27→[6896..8704], 31→[6960..8816], 37→[7024..9120].
- Solo 8 bones con mesh; el resto ib[0..0].

## 4. LOS 12 MESH PART HEADERS (0x50B = 80B)

```
+00..+0C: 4× escala (128.0)     +10..+1C: 4× weights
+20:0  +24:5  +28:0  +2C:5
+30: grp_idx (0/1/2, FFFF=sombra)  +34: 0xFFFFFFFF
+38/+3C: type2 (0x1BD mesh, 0x11BD alt, 0x190 shadow, 0x199 special)
+40/+44: stride 0x44   +48/+4C: 0
```

| h | grp | type2 | weights | tipo |
|---|---|---|---|---|
| 0-2 | 0 | 0x1BD | 0.8/0.75/0.7/1.0 | mesh cuerpo |
| 3-7 | 1/2 | 0x1BD/0x11BD | varían | mesh/alt |
| 8 | FFFF | 0x190 | 1.0×4 | **shadow** |
| 9 | 1 | 0x11BD | 0.9×3/1.0 | mesh alt |
| 10 | FFFF | 0x199 | 0.59/0.31/0.31/1.0 | **special** |
| 11 | 2 | 0x1BD | 0.7×3/1.0 | mesh |

Headers 8 y 10 (grp=FFFF, 0x190/0x199) = sombra/special, no dibujan malla.

## 5. LOS 42 EJES (0x50B) — JERARQUÍA DE HUESOS

```
+00..+0C: quat local (x,y,z,w)   +10..+1C: pos local
+20..+2C: 4×1.0
+30: sello (0x6000020F raíz, 0x9000020C/0x8000020C mesh, 0x1000020C
     transición, 0x204/0x205 shadow, 0x9000020E/0x9800020E,
     0x90000208/0x80000208/0x10000208)
+34: arm_ptr (REL AWG0) → arm 20B
+38: child  +3C: sibling  +40: parent  (→ labels)
```

⚠️ Leer el bloque desfasado +0x10 da falsa impresión de sello en +0x20
(19 ejes "fantasma"); el layout real es +0x30/+0x34.

## 6. LOS 42 BLOQUES 0x1660-0x1994 (20B) — TRANSFORM + PTRS

Dentro de la zona de ejes. Bloque PAR = transform (quat + sello); bloque
IMPAR (PTRS) = `[axis_ptr, labelA, 0, labelB, 0]` con labelA/B → labels
de huesos (0xBC0=TSH_CHEST, 0xC60=TSH_LHANDROT, 0xD00=TSH_RARM1,
0xDA0=TSH_NECK, 0xE40=XTSH_M_RMOUTH2, 0x0A30=RLEGROT...).

## 7. TABLA DE LABELS (interleaved, +0x20 c/u, nombre en +0x0C)

40+ labels: XTSH_BODY, TSH_WAIST/STMC/CHEST, TSH_L/RCHN, TSH_L/RARMROT/
1/2, TSH_L/RHANDROT, TSH_L00_L/RHAND, XTSH_NLA/NRA/NW/NH/NLF/NRF,
TSH_NECK/HEAD, XTSH_L00_FACE, TSH_M_JAW, XTSH_M_L/RMOUTH1/2, XTSH_DTEETH,
XTSH_M_UTEETH, TSH_LLEGROT/1/2, TSH_LFOOT1/2, TSH_RLEGROT/1/2, TSH_RFOOT1/2.

## 8. CONEXIÓN EJE→LABEL→ARM→IB

```
EJE (quat+pos+child/sib/parent) → arm_ptr → BLOQUE (transform|PTRS→labels)
ARMS [bone, fin, 0, ini, 0] → rangos del IB en la zona post
IB (zona post) → slots del sec34 (vértices stride 44)
```

Para un AWG coherente hay que reconstruir TODO: labels + headers + ejes +
bloques + arms + sec34 + IB.

## 9. VERIFICACIÓN CRUZADA (JSON .aerithdevs)

- Vértice JSON: `<bone, weight, pos(3), uv(2), nrm(3), color(4)>` = 44B.
- Mesh part header: `F[8 floats] + I&[type1 type2 0 FFFF 0]`.
- Sub-mesh: `$sub00: < <&0000, &0000, $tri, false>, <vertices>...>`
- Jerarquía: `$data (hueso, $ref hijos, $mtx, $grp)`.
- Formato B1 (`_skel-1.json`, XGOK): plano `$data`→`$sub`→verts (header
  `0000101B`, NN=bones 1/2/3), 18 sub-meshes, 7337 verts con duplicados.

## 10. ERRORES DE build_awg_hd_full.py (CORREGIDOS en v10/v12)

El build anterior usaba stride 16 + offsets absolutos (error de sesión 7)
→ solo manos visibles. Corregido: stride 44 + offsets REL + pool global
(ver AGENTS.md, v12: 4059/4272 slots reemplazados, mesh group intacto).