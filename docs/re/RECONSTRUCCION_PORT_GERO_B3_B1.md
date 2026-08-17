# RECONSTRUCCIÓN DEL PORT GERO B3 HD → B1 HD (16/08/2026)
> Copyright (c) NovaPowers. Released under the MIT License. Firmado por NovaPowers.
>

> ⚠️ **SUPERSEDIDA por `SESION10_PORT_B3_B1_FUNCIONAL.md` (16/08 noche)**:
> el port B3→B1 quedó **100% FUNCIONAL en runtime** con el pipeline automático
> `install_b3_to_b1.py` (flag→0x2, type2→0x1BD/0x11BD, **materiales B1**,
> **AZT con alpha DXT3 0xFF**). Esta doc documenta el análisis binario previo.
>
> Pipeline recreado desde cero con `port_b3_to_b1.py` y validado contra el
> bin Gero B1 nativo (`scan_gero\52_u.bin`). Es la forma CORRECTA de portar
> B3→B1. El mod `test_gero_on_tenshinhan` estaba CORRUPTO (contenía un TSH
> nativo con vértices alterados, NO el Gero) → descartado como referencia.

---

## 1. CONCLUSIÓN

**El port B3→B1 es un RE-MAPEO, no un re-layout ni un re-rigging de poses.**

Solo hay 3 diferencias entre un AWO B3 y uno B1 del MISMO personaje:

| # | Diferencia | B3 | B1 |
|---|---|---|---|
| 1 | Flag `+0x0C` de cada AWG | `0x4` | `0x2` |
| 2 | Type2 de mesh part headers (`+0x3C` de cada header 0x50) | `0x29BD` | `0x1BD` / `0x11BD` |
| 3 | **Orden de bones** (por labels) | orden B3 | orden B1 |

Nada más. El vértice, el mesh group, el IB, los ejes y los arms son
**idénticos en formato**. El skinning funciona porque el runtime lee el
bone index del vértice (`+16`) y del arm, y ambos apuntan al eje local.

---

## 2. PIPELINE VALIDADO (ejecutado y verificado)

```
python port_b3_to_b1.py <awo_b3.bin> <azt_b3.bin> <awo_b1_ref.bin> <out.awo>
```

Para el Gero:
```
awo_b3    = Gero B3 #AWO extraído del #AMB bin 91 (data_cmn)
azt_b3    = Gero B3 #AZT (440128 B)
awo_b1_ref = Gero B1 nativo (scan_gero\52_u.bin)   ← CLAVE: mismo personaje
out        = gero_b1_port.awo (293728 B)
```

**Salida verificada**: `flag=16 AWGs→0x2, type2=36→0x1BD, verts=1731,
arms=37`. En el bin resultante: flag AWG0=0x2, sec34 2501 verts, **todos los
bone indices mapean a labels válidas del B1(52)** (0 bones inválidos).

### Mapa de bones B3→B1 (Gero, 43/46 directos + 3 fallbacks)

```
B3[ 2] 20G_RLEGROT  → 52[44]      B3[40] 20G_LLEGROT → 52[38]
B3[ 3] 20G_RLEG1    → 52[45]      B3[41] 20G_LLEG1   → 52[39]
B3[ 4] 20G_RLEG2    → 52[46]      B3[42] 20G_LLEG2   → 52[40]
B3[ 8] 20G_STMC     → 52[ 2]      B3[43] 20G_LFOOT1  → 52[41]
B3[ 9] 20G_CHEST    → 52[ 3]      B3[45] 20G_LFOOT2  → 52[42]
... (resto directos por label)
X20G_M_JAW   (B3) → 20G_HEAD (52[19])   [fallback]
X20G_SHD3    (B3) → 20G_NECK (52[18])   [fallback]
X20G_L00_FACE(B3) → 20G_HEAD (52[19])   [fallback]
```

**⚠️ El ref B1 NO puede ser el TSH**: sus labels son `XTSH_*`/`TSH_*`, que
mapean 0/46 contra el Gero (`X20G_*`). El ref correcto es SIEMPRE el B1
**del mismo personaje** (Gero→52_u.bin, TSH→2450, etc.).

---

## 3. TEXTURAS (AZT) — 3 requisitos para que el modelo se renderice

El `#AZT` B3 reconstruido (`azt_10_gero_b1.bin`, 264072 B) cumplía:

1. **10 DDS contiguos**: `data_off = anterior + size`. Verificado: los 4
   primeros son 256×256 DXT3 (pitch 65536 c/u, contiguos 0x228→0x102A8→
   0x20328→0x303A8→0x40428) + 6 de 4×4 DXT3 (pitch 16, contiguos hasta
   0x40788). El AWO espera 10 slots, no 4.
2. **Alpha DXT3 a 0xFF**: en cada bloque DXT3 los 8 bytes de alpha se
   forzaron a `0xFF`. Sin esto → "cuerpo negro".
3. **Hash `+0x1C`**: los slots del AWO esperan el hash correcto por textura.

Los AZT de prueba (`azt_4tex`, `azt_mixed`, `azt_piccolostyle`,
`azt_contig`, `azt_contig_opaque`) muestran el camino: el paso final fue
`azt_10_gero_b1.bin` con los 10 DDS contiguos + alpha 0xFF.

---

## 4. ARTEFACTOS DEL PIPELINE REAL (b3_bins/)

| Archivo | md5 | Qué es |
|---|---|---|
| `gero_0_#AWO.bin` | 85b7e407 | AWO B3 extraído (293728 B, flag 0x4) |
| `gero_awo_190.bin` | a31d3257 | +108B (primer intento type2) |
| `gero_awo_mat.bin` | b5ac4a15 | materiales (2611 diffs) |
| `gero_awo_type2.bin` | e1b2f786 | type2 0x29BD→0x1BD (1918 diffs) |
| `gero_awo_bones.bin` | 0ed82eee | remap bones vértices (1962 diffs) |
| `gero_awo_full.bin` | 12af349f | = rerig (remap arms, 28 diffs) |
| `gero_awo_rerig.bin` | 12af349f | idéntico a full |
| `gero_awo_arms.bin` | — | +67 diffs (remap arms final) |
| `azt_10_gero_b1.bin` | — | AZT final (10 DDS contiguos, alpha 0xFF) |

**Ojo**: los bins `gero_awo_*` quedaron con flag=0x4 (B3) — eran estados
intermedios de un pipeline que nunca completó el cambio de flag. El
`port_b3_to_b1.py` es el que hace las 3 transformaciones completas.

---

## 5. COMPRIMIR E INSTALAR (mod)

```
xbcompress.exe /N:2048  gero_b1_port.awo  geom.lzx   → 81136 B (slot 2450 = 290816)
xbcompress.exe /N:2048  azt_10_gero_b1.bin tex.lzx   → 31824 B (slot 2451 = 33504)
padding a tamaño de slot con 0x00, instalar en mods/<mod>/us/data_sp.afs/<slot>/
```

Ambos bins caben en los slots del TSH. Round-trip verificado con
`xbdecompress.exe`.

---

## 6. LECCIONES PARA PORTEAR OTROS PERSONAJES

1. **Mismo personaje B3→B1**: solo flag+type2+remap bones (este pipeline).
   Gero B3→Gero B1 funciona directamente.
2. **Personaje distinto B3→B1** (ej. Gero B3 → TSH B1): el ref B1 debe ser
   el DESTINO (2450), pero entonces los labels `X20G_*` mapean 0/46 → se
   necesita además el **retargeting de poses** (align_joint, inv_rigid) para
   que la geometría quepa en el esqueleto destino. Ese es el port de
   personaje distinto, aún pendiente (ver `docs/planes/PLAN_PORT_REAL_DISENO.md`).
3. Los scripts `scripts_gero/rerig_*.py` usan offsets ANTIGUOS (bone en +18,
   sec_off en +0x34) → **NO usar**: producen remaps en offsets equivocados.
   El offset correcto del bone es **+16** y sec_off **+0x28** (v10).

---

## 7. VERIFICACIÓN ADICIONAL (16/08 — RESULTADO EN RUNTIME: SOLUCIONADO)

- ❌ Probar `gero_b1_port.awo` instalado en slots TSH (2450/2451): el mod
  `test_gero_b3_to_b1` se carga bien (override OK en log) pero **CRASHEA**
  `0xC0000005` en `dbz1.exe+0x8a9b85` al renderizar el modelo en combate.
- ❌ A/B con bins B1 nativos del Gero (`52_u.bin` X20G, `49_u.bin` X19G) en
  slot 2450: **también crashean** mientras el tex.bin (2451) era el AZT del
  Gero B3 → el problema NO era la conversión B3→B1.
- ✅ **Causa real del crash = MISMATCH DE TEXTURA**: el mod dejaba el AZT del
  Gero B3 (10 texturas) en 2451 mientras se instalaban geometrías que esperan
  su propio AZT. Con el **par completo del mismo personaje** funciona.
- ✅ **Validado en runtime (100% funcional)**: instalar `49_u.bin` (AWO X19G)
  en 2450 + `48_u.bin` (AZT X19G, 4 tex) en 2451 → **renderiza perfecto en
  combate**. El swap X19G→slot TSH demuestra que los model swaps B1→B1 son
  totalmente funcionales.
- ⚠️ **Identidad**: `X19G` = Android 19, NO Dr. Gero. El Dr. Gero es
  `X20G`/20G = bins 52/53 (no jugable). Ver
  `docs/tutoriales/MODEL_SWAPS_METODOLOGIA.md`.
- La validación binaria (flag 0x2, type2 0x1BD, bones 0 inválidos) NO basta
  para portar entre juegos; para swaps B1→B1 el método validado es el par
  nativo completo (ver `docs/tutoriales/MODEL_SWAPS_METODOLOGIA.md`).
- **Teorías descartadas**: mesh group jerárquico B3 / plano B1 (el crash
  ocurría también con bins B1 nativos); conteos fijos 42/23 del TSH (el X19G
  con 46 bones / 15 AWG / 4601 verts funciona en slot 2450).