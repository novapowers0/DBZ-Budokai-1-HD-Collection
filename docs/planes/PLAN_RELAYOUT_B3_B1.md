# PLAN: RE-LAYOUT B3→B1 (RE-RIGGING MASIVO)
> Copyright (c) NovaPowers. Released under the MIT License. Firmado por NovaPowers.
>

> Estado: **BLOQUEADO/SOBRESEÍDO**. Planificado 14/08/2026. La vía v10-v12
> (AGENTS.md) es la que funciona; el re-layout masivo B3→B1 se dejó de lado.
> ⚠️ Los layouts de vértice de este doc (stride 68 B1, bone +18 B3) eran
> PRE-v10 — la RE definitiva es sec34 stride 44B con BONE@+16 (ver AGENTS.md).

---

## Objetivo (histórico)

Portar el Gero B3 HD (bin 91) al slot TSH B1 HD con skinning funcional.

## El problema (resumen de la RE pre-v10)

- **B1**: 6 AWGs (AWG0=51 huesos + 5 sub-AWGs). Rig por hueso. IB=12556.
- **B3**: 16 AWGs (AWG0=46 + 15). Bone index por vértice. IB=5444.
- Diferencias: orden de huesos (B3 empieza por pierna derecha), nº AWGs/huesos,
  formato de vértice, rig data (B3 6 bones vs B1 16).
- **Síntoma**: partes congeladas en el mundo = huesos sin rig data en
  posiciones B1.

## Estructura del AWG0 (B3, verificada)

```
0xC00: header (0x40) → 0xC40 labels (46×32B) → 0x1200 mesh parts (10×0x50)
0x1520 ejes (46×80B) [+0x30 sello, +0x34 arm_ptr, +0x38 child, +0x3C sibling]
0x2380 armatures (46×20B) [bone_n +0, +6 rig_ptr, +8 sub_ptr]
0x2A86 sec34 → 0x1ADDC vb2 → 0x1D4FC ib (5444 u16 BE) → 0x1FF84 restart+tabla
```
B1: misma estructura con 51 huesos.

## Opciones de conversión (históricas)

- **A**: Crecer AWG0 B3 de 46→51 huesos (reordenar + añadir 5) → desplaza
  todas las secciones → re-mapear todos los offsets. Riesgo alto.
- **B**: Usar AWO B1 como plantilla (estructura B1 que ya funciona) +
  reemplazar geometría (sec34/vb2/ib) del B3 convertida a formato B1. Riesgo
  medio. → **La recomendada entonces**.
- **C (no viable)**: Solo remap de +18 — mejoría parcial, huesos sin rig data
  congelados.

## Lecciones de los experimentos (14/08)

- **NO re-mapear arms** (casi congela el juego).
- **NO reordenar solo los ejes** (labels en orden B3 + ejes en B1 → colisión).
  El sistema labels+ejes+armatures+punteros es interconectado.
- **+30 del mesh part ES bone index** (el crash previo fue mapa incompleto).
- Los mesh-ref blocks del B3 = los propios ejes (sello +0x30), arm_ptr → arm.

## Resolución final (2026-08-15)

El port B3→B1 SÍ se logró vía `port_b3_to_b1.py` (Gero en script_gero/):
flag 0x2 + type2 0x1BD + bones (verts + arms). La RE v10 confirmó que el
sec34 del B1 es stride 44B con BONE@+16 y offsets REL al AWG0 — el "stride 68
multi-tipo" era un artefacto del análisis B3. Para personajes B3 sin versión
B1 nativa sigue pendiente la retopología completa (PLAN_PORTS_FUNCIONALES).

## Herramientas (pipeline B3, adaptables)

`awo_tools/` : convert_personaje, rig_mapeo, decimar_tri, build_janemba2,
relayout_awg, relayout_sec34_remap, build_afs.