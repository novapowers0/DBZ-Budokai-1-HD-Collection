# Investigación: Ecosistema de Modding de DBZ Budokai 1 / HD
> Copyright (c) NovaPowers. Released under the MIT License. Firmado por NovaPowers.
>

> Cómo moddea la comunidad Budokai 1 y cómo se integra en el recomp RexGlue.
> Fecha: 12/08/2026. Fuente: `E:\Programas\Game Graphic Studio 7.4.0`.

---

## 1. Empaquetado del juego

Archivos **AFS** (ADX File System). En el recomp: `data_us/fr/sp/ge/it.afs` (idiomas),
`adx_us.afs`/`adx_jp.afs` (audio), `data_yah.afs`. Cabecera AFS: nº archivos u32 + tabla
(offset, tamaño) + dir de nombres opcional, todo padded a 2048.

**Implicación para mods:** el juego lee el `.afs` como plano vía VFS (`game:\us\...`).
Un mod puede reemplazar el `.afs` completo (override) o interceptar la lectura por entrada.

## 2. Ecosistema de la comunidad (Game Graphic Studio 7.4.0)

| Herramienta | Qué hace |
|---|---|
| AMT Tools (amt_builder/exporter.py) | Construye/extrae `.amt` (texturas). Cabeceras en `Files/AMT_header.bin` |
| Animation Editor | Edita animaciones `.amo`/`.amt` |
| Bone Addition Tool v1.02 | Añade huesos a modelos |
| Budokai Modding Tool V1.5 | Herramienta principal (empaca modelos/animaciones/texturas al juego) |
| Modelos B1 (`Modelos B1\*.bin`) | Un `.bin` por personaje/variante (16G02, 18G00, ANS00, BAT00, BBBOK00...) |

### Formatos
- `.bin` = modelo 3D (nombres `NNGGyy.bin`: G=grupo, yy=variante/traje).
- `.amt` = texturas (BMP empaquetado, tipos `[T]`=textura 0x21, `[S]`=shader, `[B]`=B2).
- `.amo` = animaciones. `.amb` = contenedor AMO+AMT (B2/B3, NO nativo de B1).
- `.amg` = model part. `.amm` = animación de cola.

### Flujo típico del modder
Extraer `.afs` (AFS Explorer) → extraer modelo/texturas (Budokai Modding Tool) →
sustituir → reempaquetar `.afs` → reemplazar en ISO.

### Personaje completo = ~12 archivos en AFS
`CLJ00.AMO, CLJ01.AMO, CLJ00.AMT, CLJ01.AMT, CLJ.AMM, CLJ_PTS.AMM, CLJ.BSK, CLJ.BCM,
CLJ.BFC, CLJ.SPX, DBS_CLJ.BD/HD/SQ`.

### Abreviaturas de personajes (Modelos B1)
GOK=Goku(21 vars), VGT=Vegeta, GHN=Gohan, FRZ=Freezer, CEL=Cell, TRX=Trunks, PIC=Piccolo,
KLL=Krillin, BLM=Broly?, RAD=Raditz, NAP=Nappa, CLJ=Cell Junior, CHZ=Chaoz, GNY=Ginyu,
YMC=Yamcha, ANS=Android. Variantes = trajes/transformaciones (Goku 0x04=SSJ, 0x0B=SSJ4).

## 3. Integración en el recomp — opciones del mod loader

- **Opción A — Override de `.afs` completo:** archivo directo `mods/<mod>/us/adx_us.afs`.
  ✅ compatible con mods ya empaquetados; ❌ pesa tanto como el original, no combina bien.
- **Opción B — Override por entrada (LA META, IMPLEMENTADA ✅ 13/08):** parser AFS en el
  runtime + carpeta `mods/<mod>/us/<afs>/<índice>` (archivo o carpeta con un archivo).
  ✅ pequeño, combinable, enable/disable. **OJO**: el archivo por entrada debe tener el
  MISMO tamaño que el original (o el juego lee datos truncados); en archivos completos no
  hay restricción.
- **Opción C — Texture packs por hash XXH3:** `texture_packs/<hash>.dds` en la texture
  cache. ✅ ideal para HD skins sin tocar .afs; ❌ requiere conocer los hashes.
- **Opción D — API scripting Lua/C#:** la más compleja, pendiente.

**Decisión:** Fase 3a = Opción B (✅ implementada y validada); 3b = Opción C (parcial);
3c = Opción D.

## 4. Audio japonés (adx_jp.afs) — INCOMPATIBLE por swap directo

`adx_us.afs` y `adx_jp.afs` tienen el mismo nº de entradas pero **estructura distinta**
(entry[0]=14KB vs 524KB; 0/200 primeras coinciden en tamaño). El juego indexa por posición
→ un swap simple desalinea música/diálogos. ✅ SOLUCIÓN: usar packs de fans diseñados como
reemplazo directo del archivo base → funcionan como mod de archivo completo
(`mods/<mod>/us/adx_us.afs`). Sin colgar.

## 5. Archivos relevantes

- `PROGRAMAS BUDOKAI\AMT Tools\amt_builder.py` / `amt_exporter.py` — formato AMT.
- `PROGRAMAS BUDOKAI\Budokai Modding Tool V1.5` — empaquetado principal.
- `PROGRAMAS BUDOKAI\Modelos B1\*.bin` — modelos.
- `DB Budokai 1 Characters\*` — personajes extraídos (AMO/AMT + previsualizaciones PNG).