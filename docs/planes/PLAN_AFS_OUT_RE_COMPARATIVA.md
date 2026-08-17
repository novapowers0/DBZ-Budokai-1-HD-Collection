# PLAN: afs_out + RE COMPARATIVA DE MODELOS (2026-08-14)
> Copyright (c) NovaPowers. Released under the MIT License. Firmado por NovaPowers.
>

> Propuesto tras v16 (deforme). Extraer/descomprimir TODOS los bins de
> personajes a `afs_out` para RE comparativa y validar overlays por carpeta.

---

## 1. Hallazgos confirmados

### 1.1 El recompile YA soporta overlays por carpeta
`mods/<mod>/us/data_sp.afs/2450/geom.bin` + `.../2451/tex.bin` = carpeta (no
AFS). Hook `AfsFindModOverride` + `ResolveEntryOverride` sirve cada read en el
rango de una entrada desde el archivo del mod. No requiere reempaquetar.

### 1.2 Múltiples mods coexisten (prioridad alfabética)
Cada mod toca SOLO sus entradas; el primer match gana. Enable/disable: carpeta
`mods/<mod>/` sin `.disabled` = activo.

### 1.3 Los bins del data_XX.afs van COMPRIMIDOS LZX
Magic `0F F5 12 EE`, comprimidos `/N:32`. `xbdecompress.exe` los descomprime
→ #AWO/#AMB plano. ⚠️ Los mods se recomprimen con `/N:2048` (ver AGENTS.md).

## 2. Infraestructura `afs_out` creada

- **B1** (`DBZ Budokai HD Collection\afs_out\`): 101 bins de personajes
  descomprimidos del `assets\us\data_sp.afs`, nombrados `<entrada>_<codigo>.bin`
  (código = label `X??_BODY`): GOK, VGT, FRZ, PIC, KLL, TSH, THL, NAP, GNY,
  GRD, 16G-19G, GHN, RCM, STN, TRX, YMC, ZBN, TJR, SBM, RAD, DDR.
- **B3** (`DBZ Budokai 3 HD Collection\afs_out\`): 230 modelos B1→AMB (mismos
  que el B3 usa como base PS2).

## 3. Validación pendiente del launcher

¿Acepta `assets_out\<region>\<afs>\<entrada>\<archivo>` como overlay sin pasar
por `mods/<mod>/`? Si `AfsFindModOverride` busca cualquier carpeta `*.afs/`
con subcarpetas → `afs_out` global editable al instante. Si no, el patrón
`mods/<mod>/...` ya permite mods inmediatos.

## 4. RE comparativa profunda (la meta)

1. Goku HD nativo vs Tenshinhan HD nativo: estructura AWG, mesh groups, arms,
   IB — qué difiere entre personajes del mismo juego.
2. Goku HD vs Goku PS2: el "Rosetta Stone" — cómo el estudio re-trabajó el
   modelo PS2.
3. Gero B3 (que sí funcionó): por qué la inyección en slots mostró silueta en
   B3 (poses HD/PS2 51/51) pero falla en B1 (poses GOK vs 20G distintas).
4. Aislar el problema Goku→TSH: (a) retargeting inv_rigid incorrecto,
   (b) mesh group/IB del template, o (c) otra cosa.

## 5. Herramientas para la RE

`xbdecompress.exe`, `afs_out/`, `analyze_b1_hd.py`, `extract_hd_mats.py`,
`export_sec34_obj.py`, `mezclar_ps2_hd_v4.py` (B3), `Model-Rig_Extractor.py`,
`AMBStudio / AMB_Tool`.

## 6. Cómo hacer un mod inmediato (workflow validado)

```
# 1. Generar bin editado (build_awg_hd_full.py)  2. Comprimir /N:2048
# 3. Padding al tamaño del slot (290816)         4. mods/<mod>/us/data_sp.afs/<entrada>/geom.bin
# 5. Limpiar logs, lanzar dbz1.exe
```

## 7. 🔴 HALLAZGO CRÍTICO (14/08): POR QUÉ PICCOLO FUNCIONÓ Y GOKU NO

### Estructura del bin HD de Piccolo (funciona)
```
#AWO: 44 bones, 19 AWGs
AWG0  @0xB80   sec34=3573 slots  XPIC_BODY       <- cuerpo
AWG1-4        sec34=322-334      PIC_L0x_LHAND   <- dedos IZQ
AWG15-18      sec34=443-514      XPIC_L0x_FACE   <- caras
```

### La clave: 1:1 AMG PS2 → AWG HD
El Piccolo PS2 (IW→AMB) tiene 20 AMGs con los MISMO labels
(`XPIC_BODY` + `PIC_L0x_LHAND/RHAND` + `XPIC_L0x_FACE`). El bin HD funcional
replica esa estructura **1:1** (19-20 AWGs).

### El error (Goku v16, histórico)
El Goku PS2 tiene 21 AMGs (XGOK_BODY + 13 dedos + 7 caras), pero el script
mantuvo la estructura del template Tenshinhan (6 AWGs, 51 bones) y solo
reescribió el sec34 del AWG0 → el runtime usa los AWGs del template
(dedos/caras) con la geometría del Goku apretada en el AWG0 → deforme.

### La vía correcta (aprendida del Piccolo)
**Reconstruir el bin HD con la estructura del PS2** (1 AWG por AMG del origen):
1. Un AWG por AMG del personaje PS2, con el MISMO label.
2. Cada AWG con su sec34, vb2, IB y ejes propios.
3. El mesh group con los huesos correctos del origen.
→ Es lo que hace la comunidad (OBJ to AMG / AMBStudio). La plantilla NO es el
template — es la ESTRUCTURA DEL PS2 re-layout a 360.
⚠️ Estado 2026-08-15: esta vía sigue pendiente (el mesh group debe generarse
coherente — PLAN_PORTS_FUNCIONALES); el atajo v12 (sec34 nativo + pool world)
es lo validado en juego.