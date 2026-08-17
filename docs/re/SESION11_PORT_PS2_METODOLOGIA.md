# SESIÓN 11 — PORT PS2→HD: METODOLOGÍA (17/08/2026)
> Copyright (c) NovaPowers. Released under the MIT License. Firmado por NovaPowers.
>

> Descubrimientos de la sesión: swap nativo CHZ HD validado, submesh data
> descifrado, mapeo de esqueleto B2 PS2→HD 1:1, y hoja de ruta para portar
> modelos PS2 (B1/B2/B3) al B1 HD.

---

## 1. RESULTADO CLAVE: SWAP NATIVO CHZ HD = 100% FUNCIONAL

**El Chaozu HD completo (geom bin 352 + tex bin 353) en el slot TSH renderiza
perfectamente en combate.** Es la validación definitiva del swap nativo B1→B1:

| Bin | AWGs | Contenido | Resultado en slot TSH |
|---|---|---|---|
| 350 | 1 | Solo cuerpo (XCHZ_BODY) | Renderiza sin manos (aparecen al atacar) |
| **352** | **3** | **Cuerpo + LHAND + RHAND** | **✅ PERFECTO (validado)** |
| 354 | 1 | Variante (43 bones) | — |

**Lección**: para personajes que YA existen en B1 HD, el swap nativo con bins
HD completos es la vía definitiva. NO hace falta portar PS2.

## 2. POR QUÉ LA INYECCIÓN DE POSICIONES DEFORMA (RE del B3)

La RE del proyecto hermano (`awo_tools/RE_PROGRESO.md` §15-19, §28) demostró:

- La geometría HD **NO es una conversión 1:1 del PS2** — es **re-topologizada**
  (vértices re-ordenados/re-computados, con IB propio de triangle strip).
- Al inyectar posiciones PS2 sobre el IB HD nativo, los triángulos conectan
  vértices que no corresponden → deformación (brazos/manos/cabeza/piernas).
- Por eso `build_awg_hd_full` (v12) al 98.3% de slots reemplazados sigue
  deformando: el 1.7% restante + la topología distinta rompen la malla.

**La vía correcta para port PS2→HD es reconstruir el bin COMPLETO**:
sec34 (44B) + IB + arms + **zona de submesh data** regenerados desde el PS2.

## 3. SUBMESH DATA DESCIFRADO (la pieza que faltaba)

Entre la zona de arms y el sec34 de un AWG HD hay una **zona de descriptores
de submesh** (23 en CHZ, uno por mesh part). Estructura de cada descriptor:

```
+00..+5F  floats de transformación/material (quats, pos, escala)
+60  c08 = inicio rango A (contiguo entre descriptores)
+64  c0C = tamaño rango A
+68  c10 = inicio rango B
+6C  c14 = tamaño rango B
+70  label 16B (XCHZ_BODY, CHZ_L01_LHAND...)
+80  string debug "max N m" (del desarrollador)
```

- Los rangos A son **contiguos** (fin de uno = inicio del siguiente).
- Los descriptores cubren los buffers de geometría (sec34 + IB).
- `amo0_to_awo.py` copiaba esta zona del bin plantilla (TSH) sobre la
  geometría nueva → **hang (no crash)** al cargar, porque los offsets del
  descriptor no coincidían con los buffers regenerados.
- Para portar PS2 correctamente hay que **generar los descriptores desde los
  mesh parts PS2** (mismo nº de descriptores que parts).

## 4. MAPEO B2 PS2 → HD 1:1 (Tenshinhan)

Extraído del `ps2_games\Budokai 2 (USA)\USR\data_cmn.afs`:

- **Entry 282**: `#AMB` → `#AMO` 772KB + `#AMT` 273KB (modelo Tenshinhan).
- **Entry 286**: `#AMM` (otro modelo, 1.4MB).
- Parseado con `parse_ps2_amg` (de `amo0_to_awo.py`): **14 mesh parts,
  4427 verts, 2944 skin**.

**Comparación de labels (42 base idénticos, MISMO orden):**

| HD (42) | B2 PS2 (66) |
|---|---|
| XTSH_BODY | TSH_BODY |
| TSH_WAIST | TSH_WAIST |
| TSH_STMC | TSH_STMC |
| TSH_CHEST | TSH_CHEST |
| TSH_LCHN | TSH_LCHN |
| ... (los 42 en el mismo orden) | ... + LHAND 01-38, RHAND 01-38, FACE 01-45 (24 extra) |

Los labels extra del PS2 son manos/caras que en HD viven en AWGs separados.
El esqueleto es **1:1 en los primeros 42 bones** → mapeo directo de bones
y coords locales sin transformar.

## 5. MAPEO DEL CATÁLOGO B2 PS2 (labels X??_BODY)

Escaneando el `data_cmn.afs` completo por `X??_BODY` en el AMO:

| Personaje | Entries | Nota |
|---|---|---|
| Androide 16 | 74, 78 | mini-modelo en 77 (X16G_HEAD) |
| Androide 17 | 80, 83 | |
| Androide 18 | 84 | |
| Androide 20 | 90, 94 | |
| Tenshinhan | 282, 283, 286 | 282=AMO+AMT, 286=AMM |
| Otros | escanear | mini-modelos X??_HEAD ~1.7KB en entries pares |

**NOTA**: los labels se buscan escaneando el AMO COMPLETO (el inicio del AMO
no los contiene — el parser del B1 los encontraba al inicio, el B2 los tiene
dispersos).

## 6. GAMECUBE: DESCARTADO PARA MODEL SWAPS

El `DragonBall Z - Budokai [NGC].iso` (GC del B1) usa formatos distintos:

- Magics: `#ACO`, `#ACB`, `#AMB` con `.act/.aco/.acm/.acb`.
- FST del GCM: offset en 0x424 (bytes), tabla de 12B/entrada
  `[type u8, nameoff u24, off u32, sz u32]`, strings tras las entradas.
- Los nombres de archivo NO corresponden a personajes (entry 967 "TSH" =
  `#ACM` de Trunks, labels XTRX_BODY).
- Solo el AFS del **PS2** es fuente válida para ports.

## 7. HOJA DE RUTA: PORT PS2→HD (Tenshinhan B2)

1. **Extraer** entry 282 (AMO+AMT) del B2 PS2 → `tsh_b2.amo` (hecho).
2. **Verificar labels** → esqueleto 1:1 con TSH HD (hecho, §4).
3. **Usar el bin TSH HD nativo (2450/2451) como plantilla ESTRUCTURAL**:
   mantiene ejes, arms, mesh part headers, submesh data, labels del TSH.
4. **Reconstruir geometría**: sec34 (44B) + IB desde los mesh parts PS2
   (14 parts → sec + IB) — el parser ya extrae verts+skin correctamente.
5. **Regenerar descriptores de submesh** (14 descriptores desde los 14 parts)
   con rangos de los nuevos buffers (la pieza que faltaba).
6. **Convertir textura** `#AMT` PS2 → `#AZT` HD (contenedor de DDS).
7. Instalar mod (geom 2450 + tex 2451) y validar en combate.

**Herramienta a crear**: `conversores/port_ps2_to_hd.py` — generaliza
`amo0_to_awo.py` + regeneración de submesh data.

## 8. ARCHIVOS DE TRABAJO

- `ps2_games\Budokai 2 (USA)\USR\data_cmn.afs` — modelos B2 PS2.
- `%TEMP%\tsh_b2.amo` / `tsh_b2.amt` — Tenshinhan B2 extraído (entry 282).
- `mods/test_chz_hd_completo_on_tsh/` — mod validado (CHZ HD 352+353).
- `conversores/amo0_to_awo.py` — parser PS2 + reempaquetado (base a extender).
- `docs/re/RE_PROGRESO.md` (proyecto B3) — RE del formato HD.