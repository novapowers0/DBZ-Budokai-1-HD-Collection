# ESTADO DEL PORT GOKU SS2 → TENSHINHAN (B1 HD) — HISTÓRICO (SUPERSEDED)
> Copyright (c) NovaPowers. Released under the MIT License. Firmado por NovaPowers.
>

> 2026-08-14. Consolidado de la sesión. ⚠️ **SUPERSEDED por la vía v10-v12 de
> AGENTS.md**: el layout definitivo es sec34 stride 44B con BONE@+16, offsets
> REL al AWG, y el modelo base correcto es el B1 PS2 `TSH00.bin` (no Gero). Este
> doc se conserva solo por las LECCIONES que siguen siendo válidas.

---

## Lecciones que siguen siendo válidas

1. **El runtime dibuja con la topología del bin anfitrión (mesh group + IB),
   nunca con la geometría inyectada.** Rellenar el sec34 del template con
   vértices de otro personaje → el IB del anfitrión conecta posiciones no
   adyacentes → cuerpo deforme. (Confirmado por logs: 2138 draws con
   index_count=6/12/120/420 = tiras del template.)
2. **El runtime exige conteos fijos** (sec34/vb2/IB). Cambiarlos rompe el
   parseo. El IB reconstruido (11055 < 12556 del Gero) puede impedir que el
   runtime dibuje bien.
3. **El mapeo skin→malla PS2 está incompleto (31%)**: el rig tiene
   `ch_loc`/`sb_loc` → bloques con el OFFSET del vértice (Model-Rig Extractor
   v0.9) que completaría el cuerpo.
4. **Los esqueletos difieren en ROTACIÓN (90-180° entre juegos)** — la
   comunidad los resuelve con retopología 3D manual, no conversión binaria.
   El retargeting world→local requiere la inversa de la matriz del hueso
   destino (`inv_rigid`, en build_awo_from_json.py).
5. **El bin Piccolo que funcionó era un SWAP INTERNO B1→B1** (un #AWO directo
   con 19 AWGs: cuerpo + dedos + caras), no un port PS2. El formato #AWO
   directo bien formado es portable entre personajes del mismo juego.

## AWG header (válido, de .aerithdevs)

Header AWG de 12 campos, big-endian, offsets REL al AWG:
`Offset subs, size subs, flag, Offset name, offset materials, size materials,
offset vertices, size vertices, offset faces, size faces, offset bones,
size bones`. Layout del vértice: **ver AGENTS.md (44B, BONE@+16)** — NO el
+20 de este doc histórico.

## Estado final (14/08)

v13: 4301 slots con bones reales; se veían torso amarillo/piernas/pies blancos
(colores del Goku SS2, confirmados por qwen3-vl:4b) pero deforme → la vía
correcta es la de AGENTS.md (pool world PS2 + sec34 nativo) o retopología
completa (OBJ to AMG). Herramientas en `mod center hd\`.