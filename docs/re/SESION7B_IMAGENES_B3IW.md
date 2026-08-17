# Interpretación de imágenes y recursos B3/IW (modding resources update 3)
> Copyright (c) NovaPowers. Released under the MIT License. Firmado por NovaPowers.
>

> 2026-08-15. El usuario pasó 8 imágenes con apuntes/código de la comunidad B3/IW
> y una carpeta de recursos. Como el modelo principal (deepseek-v4-flash) NO soporta
> entrada de imágenes, se transcribieron las 8 con OCR de Windows (rápido, local)
> y se correlacionaron con los mensajes. Carpeta revisada a fondo.

## Correlación imagen ↔ mensaje

| Img | Mensaje | Contenido |
|---|---|---|
| 1 | B3GH SLUS Stage Location and Data | Tabla de stages en **303D20** del ELF SLUS. Header de 18 bytes (nombre + bin location en data_cmn.afs: offset **10**=mapa, **14**=load data). **Restar FFF80** a los offsets de bins. Extra Stage IDs: 00 World Tournament, 01 Hyperbolic Time Chamber, 02 Archipelago, 03 Destroyed Archipelago, 04 Urban City, 05 Destroyed Urban, 06 Mountains, 08 Plain, 11 Inside Buu, 12 Destroyed plains, 0A Grandpa Gohan's, 0C Namek, 0D Destroyed Namek, 0E Cell Games, 0F Kars world |
| 2 | ELF sfx partial breakdown (IW SLES) | Dump hex en **0034E000–0034E3xx**: categorías Soundtracks / Ringout-Special grab / Other audios, con los bytes índice de cada canal |
| 3 | BFCs navigation | Broly's skills (unnamed_11). Los BFC están **al final de ciertos AMTs**. Código de color: **Rojo** = nº de skills, **Negro** = línea de chars con transformación, **Azul** = Capsule ID. "Los últimos 4 bytes por línea parecen vacíos, podrían extender el nº de botones para un combo" |
| 4 | SLxS B3→IW (línea faltante) | Comparativa hueso a hueso (LOBIL, WAIST, LLEGI...): **"6th line is missing"** — las animaciones IW pierden la 6ª línea de bytes frente a las B3 |
| 5 | Select menu pose (bin 3882) | **BUDOKAI 3 CHARACTER IDs** en unnamed_3882.bin (offsets 000022D0+): 00 GOKU, 01 KID GOKU, 02 KID GOHAN, 03 TEEN GOHAN, 04 GOHAN, 05 GREAT SAIYAMAN, 06 GOTEN, 07 VEGETA, 08 FUTURE TRUNKS, 09 KID TRUNKS, 0A KRILLIN, 0B PICCOLO, 0C TIEN SHINHAN, 0D YAMCHA, 0E HERCULE, 0F VIDEL, 10 KAIOSHIN, 12 RADITZ... |
| 6 y 7 | FACE AMGS ON AXIS LINES | Dump del AMO de Goku (XKOK LOI, XKOK M RMOUTH2, RPCTARA, XKOK M LMOUTH1, XKOK L00 FACE, LPCTARA). Misma imagen duplicada. Zonas: 0x26xx (axis), 0x70370 (AMG body), 0x74000, 0x54830 (faces). Confirma: las caras van en orden numérico de AMG pero **colocadas desordenadas en las líneas de eje** |
| 8 | Port BT3→B3 (shaders) | **GOK09.AMO (SSJ1)**: valores de iluminación se buscan con `BD010000BD010000` y `BD11000080110000`. Default `00 00 00 43`; valores válidos `00 00 00 3F`–`00 00 00 44` y `00 00 00 BF`–`00 00 00 C4`. Hair: `00 00 10 C3`, Skin: `00 00 A0 43`. Confirma conversión de shader (RGB lines) al portar |

## Carpeta `modding resources update 3` — hallazgos

Estructura:
```
3DMax/budokai_111616.ms          <- importer AMO completo (SleepyZay)
Axis/axis_data.py                <- display bones/axis (SamuelDoesStuff)
DATA_CMN/data_cmn.afl + INFO     <- nombre de archivos del AFS B3 (Vras)
DATA_EN/DATA_EN.afl/.jfl + INFO  <- nombre de archivos DATA_XX B3 (Alice Liddell)
DATA_ENG .aerithdevs/...          <- AFL GH/CE (MetalFrieza3000) + SkillList.dson
Dragon Ball Z_ Budokai 3 - The Cutting Room Floor.pdf  <- portada wiki (1 pág)
```

### `Axis/axis_data.py` — header AMO PS2 CONFIRMADO por la comunidad
```
+16 = axis_amount            (cantidad de huesos/ejes)
+20 = amo_bone_location      (ubicación de la tabla de huesos)
+32 = axis_line_amount       (cantidad de axis lines por hueso)
+48 = first_amg_location     (primer AMG)
Nombres de huesos: first_amg_location + first_amg_length + (i*32), 16B por nombre
Línea de eje:     amo_bone_location + (i*32) + 4  -> offset;  y +8 dentro de la línea
```
Es EXACTAMENTE el layout que usamos en `mod center hd/parsers/lib_ps2/`. Valida nuestra RE del PS2.

### `3DMax/budokai_111616.ms` — importer AMO (mina de oro)
- Header AMO: `AMO` + HeaderLength + (skip 0x8) + AmoData_Count + AmoData_Start + AmgCount + AmgOffsetTable + Bonecount + BoneNameTableOffset.
- **Jerarquía de huesos**: cada bone = quat (c11,c12,c13,c14*-1) + pos (c21,c22,c23 * fscale 5), skip 0x20, y **`tfm = tfm * parent`** (compone con el padre — igual que pose_matrix.py).
- **Bloques AMG**: `skip 0x30` (bone matrix) + DataType (short) + DataType2 (short) + DataOffset + unk + unk + `skip 0x10`.
- **Formatos de vértice PS2 por MeshType[1]**:
  - `0xBD/0xFD/0x3D`: pos(3)+null + nrm(3)+null + uv(2)+w+null = 48B
  - `0xB5/0xB6/0xF5`: 48B con 4 bytes extra (shader)
  - `0x199`: pos+nrm sin UV; `0x90`: solo pos; `0xB4/0xA4/0x99/0x92/0x19`: pos+uv
- **Weight/skin data** (bloque tipo 20): tabla `tableCount` → `weightCount`+`weightOffset`; cada entry = 3 floats (weightData) + offset + 3 floats + null.
- Submesh: `FaceType` (0=strips, 1=normal), `VertCount`.

**CONFIRMA**: PS2 usa vértices de 48B con mesh types; el HD usa sec34 stride 16
(pos+weight) + IB. La conversión PS2→HD requiere re-layout + transformación,
tal como concluimos en sesión 7.

### AFL / SkillList
- `DATA_EN.afl` + `data_cmn.afl` + `DATA_ENG .aerithdevs/DATA_ENG.afl`: listas de nombres de archivos del AFS B3 (skills, personajes, maps, efectos SPX). Útiles como diccionario de entradas/slots B3.
- `DATA_ENG .aerithdevs/SkillList.dson`: lista OCR de skills B3 (SK-SKL_000+ con name/owner/txt1-3). Referencia para el skill tray.

## Relevancia para el port B1 HD
- La imagen 6/7 (FACE AMGS ON AXIS LINES) + el script 3DMax confirman que **en el
  AMO PS2 las caras/manos son AMGs separados con líneas de eje dedicadas e IDs
  secuenciales** → refuerza la vía del Piccolo (reconstruir con 1 AWG por AMG,
  estructura del PS2) como correcta.
- Layout AMO PS2 ahora validado por 2 fuentes independientes (community scripts).
- El script 3DMax documenta los formatos de vértice PS2 (48B) — la conversión a
  HD stride 16 necesita re-layout exacto.