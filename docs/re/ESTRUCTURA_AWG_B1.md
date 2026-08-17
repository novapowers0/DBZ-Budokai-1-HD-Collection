# ESTRUCTURA AWG X360 (B1 HD) — DESCIFRADA con guía de .aerithdevs
> Copyright (c) NovaPowers. Released under the MIT License. Firmado por NovaPowers.
>

> 2026-08-14. Fuente: mensajes de `.aerithdevs` en el Discord (Dragon Ball Z
> Budokai Modding Community) + verificación contra el bin del Gero B1 HD
> (`scan_gero\52_u.bin`, AWG0 @0xD20).

## 1. HALLAZGO CLAVE (de .aerithdevs, 14/08/2026)

> "first 16 bytes is AWG header: **Offset subs, size subs, flag, Offset name,
> offset materials, size materials, offset vertices, size vertices,
> offset faces, size faces, offset bones, size bones.**"
> "the awo contains more offsets and counters" / "maybe for X360"

Esto resuelve el layout del header del AWG X360 (el formato del B1 HD).

## 2. MAPA DEL AWG DEL GERO (verificado, 12 campos)

Header AWG (offsets RELATIVOS al AWG, big-endian):

| Campo | +off | Valor Gero | Significado |
|-------|------|-----------|-------------|
| offset subs | +0x10 | 0x33 | 51 sub-parts (bones) |
| size subs | +0x14 | 0xBA0 | tabla de huesos (matrices bind) |
| flag | +0x18 | 4 | flag |
| offset name | +0x1C | 0x40 | labels (X20G_BODY...) |
| offset materials | +0x20 | 0x6A0 | floats de material |
| size materials | +0x24 | 0x10 | |
| offset vertices | +0x28 | 0x2F10 | zona de vértices |
| size vertices | +0x2C | 0x34560 | vb2 (tamaño) |
| offset faces | +0x30 | 0x37470 | IB |
| size faces | +0x34 | 0x6218 | sec34 (tamaño) |
| offset bones | +0x38 | 0x3D688 | jerarquía padre (FFFF,1,2,3...) |
| size bones | +0x3C | 0x24 | |

**Buffers reales** (rel AWG):
- sec34 = 0x6218 (189256 B = 4301 verts × 44)
- vb2 = 0x34560 (12048 B = 273 verts × 44)
- IB = 0x37470 (12556 índices u16)

## 3. ESTRUCTURA DEL AWG (interpretación)

```
AWG0:
  +0x00: '#AWG' magic
  +0x10..+0x3C: header (12 campos, ver tabla)
  +0x40: offset name = labels de huesos (X20G_BODY, 16B cada uno)
  +0x6A0: offset materials = floats de material (67.0, 67.0, ...)
  +0x2F10: offset vertices = zona de vértices
  +0x6218: sec34 (4301 verts × 44B, layout 01BD)
  +0x34560: vb2 (273 verts × 44B, cabezas/caras)
  +0x37470: IB (12556 índices u16)
  +0x3D688: offset bones = jerarquía padre (0xFFFFFFFF, 1, 2, 3...)
  +0xBA0: tabla de huesos (matrices bind: quat + pos + escala)
```

## 4. LAYOUT DEL VÉRTICE DEL B1 (CORREGIDO a la RE v10)

⚠️ Este doc era PRE-v10 (decía BONE@+20). La RE DEFINITIVA (AGENTS.md,
verificada en TSH nativo slot_2450) es stride **44B con BONE en +16**:

```
+00 pos.x +04 pos.y +08 pos.z     (floats BE)
+12 weight (0.7/0.8/0.9/1.0)
+16 BONE (u32, VÁLIDO 1-34)       ← NO +20
+20 nrm.x +24 nrm.y +28 nrm.z
+32 0xFFFFFFFF
+36 blend/scale
+40 uv
```
`n_sec = sec_size//44`. TSH nativo = 4272 verts.

Los offsets del header AWG0 (+0x50) son **RELATIVOS al AWG0** (NO absolutos):
`+0x28 sec_off`, `+0x2C sec_size`, `+0x30 post_off`, `+0x34 post_size`,
`+0x38 siguiente zona`, `+0x3C bones count`, `+0x40 nombre (16B)`. El layout
de 12 campos del header (Offset subs/size/flag/name/materials/vertices/faces/
bones) viene de .aerithdevs y es válido como estructura general; los VALORES
numéricos de la tabla de la sección 2 eran de un bin desactualizado
(sec34@0x6218, vb2@0x34560, IB@0x37470 = Gero pre-v10).

## 5. LA LECCIÓN (por qué fallaron v2-v9)

El enfoque de "rellenar el sec34 del template con vértices del Goku" FALLA
porque el runtime dibuja el sec34 con el **IB del template** (topología del
Gero). Al poner vértices del Goku en slots 0-4301, el IB del Gero conecta
posiciones del Goku que no son adyacentes → el cuerpo se ve como el Gero
deforme.

**El enfoque correcto**: reconstruir los buffers del AWG del Goku:
1. **offset vertices/sec34** → geometría del Goku (layout 01BD)
2. **offset faces/IB** → triángulos REALES del Goku (submeshes FaceType)
3. Actualizar **size vertices/size faces** en el header
4. Mantener offset name, materials, bones (jerarquía) del template

## 6. PRÓXIMO PASO

Reconstruir el IB con los triángulos reales del Goku SS2 (extraídos de los
submeshes con FaceType=1 strips / FaceType=0 triplets) y reescribir
sec34 + IB en el bin, actualizando los sizes del header AWG. Este es el
mismo pipeline que la sesión B3 validó con Krillin PS2→HD.

**Herramientas**: `build_ib_from_ps2.py` (B3), `parse_ps2_mesh.py` (B3),
`convert_personaje.py` (B3) — adaptar el layout del vértice a 01BD del B1.
