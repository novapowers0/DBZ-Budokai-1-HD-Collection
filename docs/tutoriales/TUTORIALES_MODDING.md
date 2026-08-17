# TUTORIALES DE MODDING — APRENDIZAJES CLAVE
> Copyright (c) NovaPowers. Released under the MIT License. Firmado por NovaPowers.
>

> Consolidación del conocimiento de `modding resources update 2\` (tutoriales
> de la comunidad). Relevante para el port de modelos HD (B3→B1) y mods.
> Actualizado: 14/08/2026.

---

## 1. PIPELINE DE EDICIÓN DE MODELOS (OBJ Editing Tutorial 2)

**Herramientas**: "AMG to OBJ V2.exe" (Nelson's Tool) = mesh parts HD ↔ OBJ;
"AMO_S.exe" (Nexus-Sama); **Blender** (2.8+).

**Pipeline**: 1) extraer mesh parts del #AWO/#AMB (AMG to OBJ V2) → 2) exportar
OBJ → 3) editar en Blender (malla, UVs) → 4) OBJ→AMG (Nelson's Tool) →
5) reinsertar sobre el original → 6) **editar el "model part texture value"**
(si cambian UVs, cambia la textura usada).
**UV Editing**: los UVs PS2 vienen **boca abajo** — aplicar "Mirror Y" al
exportar de vuelta.

## 2. EDICIÓN DE TEXTURAS (DBZ B3HD Lesson 2 - Texture Edition)

1. Descomprimir el bin (X360 = #AZT, PS3 = #A3T).
2. Localizar la sección AZT (template **B3_AMB para 010 Editor**, del discord).
3. Extraer DDS (herramienta A3T/AZT) → editar en Paint.NET/Photoshop (plugin
   **NVIDIA DDS**) → guardar como **BC2 (DXT3)**.
4. Reconstruir el AZT → reemplazar la sección en el bin original.
5. **Actualizar el tamaño de la sección AZT en el header** (ej. 96850 hex).
6. Recomprimir (Lesson 1, X360 o PS3).

**Value_list AMT** (tamaño de textura → valor): 8→04, 64→06, 128→07, 256→08,
450→09, 512→09, 600→0A. Bpp: x8 = W×H, x4 = (W×H)/2.

## 3. IDENTIFICACIÓN DE PERSONAJES

- **Character IDs (B3/IW) — SLXS**: ver `docs/referencias/PERSONAJES_BINS.md`
  §6 (lista completa: 05 Great Saiyaman, 08 Future Trunks, 16-1A Ginyu force,
  1F And19, 40 Gotenks, 44 Gogeta, 48 Vegito, 4C Kibito Kai, 5B-5D Goku/Vegeta
  SSJ4, 63-65 Cell, 68 Broly, 69 Demon King Piccolo...).
- **Códigos de labels → personajes**: ver PERSONAJES_BINS.md §1.
- **Bin List del B3** (`Nassif9000s Modding Tutorial\b3bins.txt`): bins→
  personajes B3 (70 C-16, 91 gero, 96 babidy, 146-148 cell, 264-281 goku
  forms, 339 nappa, 352 raditz, 369 mr satan, 390 tenshinhan, 406-419 vegeta).

## 4. SISTEMA DE COMBOS (BCM Notes)
- Combos = árboles (trunk = botón de inicio, branches).
- **Attack codes**: patrón `NN 02 NN 03 NN 03` (`00 02 00 03 00 03` = puñetazo
  normal; `4A 02 4A 03 4A 03` = Kamehameha).
- **Button codes**: `00 00 01 00`=P, `01 00 01 00`=fP, `02 00 01 00`=bP,
  `00 00 02 00`=K, `00 00 03 00`=PK, `00 00 04 00`=G, `00 00 06 00`=KG.
- Ki Attacks suelen ser los últimos combo trees.

## 5. ANIMACIONES (goku_all_animations_b3_and_iw.txt)
Los bins de movimientos indexan animaciones: `00 idle | 01 block | 02/05 jump
forward | 03/04 dash | 06-08 transform | 09/0a charge | 0b SSJ3 | 0c SSJ4 |
0d taunt | 0e-16 punches | 17-1f kicks...`.

## 6. MVS/ANIMATION SWAP ENTRE JUEGOS (IW to B3)
1. Guardar el bin de movimientos (AMC) fuente y destino → 2. copiar el **BCM**
(combo data) → 3. ajustar valores en el AMB → 4. reemplazar bins (BSK/AMM +
AMC). ⚠️ Necesita más experimentos, no garantizado 100%.

## 7. AUDIO ADX
**PES Sound File Converter** (MP3→WAV), **Audacity** (loop points), **AdxEncoder**
(WAV→ADX). 48000 samples = 1 segundo. Si el loop falla, ajustar ±2000 samples.

## 8-9. PATCHING AR CODES / SLXS (desbloquear fusions)
HTML de Action Replay codes (Ghidra/patching). Character IDs SLXS: 07=Vegeta,
06=Goten, 4A=Vegito. "Slots de transformación": contar transformaciones
(kaiohken=1, SSJ=2...). IDs 5D/68/5B solo para personajes "fusee".

## 10. HERRAMIENTAS
AMG to OBJ V2 (Nelson) · AMO_S.exe (Nexus-Sama) · B3_AMB template (010 Editor)
· A3T/AZT tool · ZERO Tool (JSON/FBX/AMT, otro juego "com.neon.sgu") · PES +
AdxEncoder · AMO Decompiler / AMB_AMT Manipulator.