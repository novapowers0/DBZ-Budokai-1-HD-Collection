# ESTUDIO: PORT DE MODELOS SPIKE CHUNSOFT → HD B1 (estrategia)
> Copyright (c) NovaPowers. Released under the MIT License. Firmado por NovaPowers.
>

> 2026-08-14. Casuística: búsquedas online + Discord + código de la comunidad.
> Objetivo: por qué no se importaba el modelo y la vía correcta.
> ⚠️ Layout de vértice mencionado aquí = pre-v10; usar AGENTS.md (44B, BONE@+16).

---

## 1. Búsquedas online

Bing/DuckDuckGo/Noesis: sin resultados útiles. GitHub:
- `SamuelDBZMAAM/Budokai-Modding-Tool` (Python): la más completa de la serie.
  Módulos en `mod center hd\src_comunidad\`: `amg_a.py, amo_a.py, amg_c.py,
  axis_e.py, b1_i_e.py, amb_c.py`.
- `ViveTheModder/tenkaichi-mdl-assist` (C++): Tenkaichi, no aplica a B1.

## 2. Discord (hallazgos clave)

- **.aerithdevs — vértice Budokai**: "ID of bone, 2: Weight/Intensity, 3:
  Vertice, 4: UV, 5: normal, 6: color". B1 comparte el formato AMO/AMG PS2.
- **.aerithdevs — header AWG X360**: "first 16 bytes is AWG header: Offset
  subs, size subs, flag, Offset name, offset materials, size materials,
  offset vertices, size vertices, offset faces, size faces, offset bones,
  size bones".
- **samueldoesstuff — AMG**: "AMG is made with the amount of bones added,
  model parts on the BODY bone, the respective Rig Data then finally the bone
  name list". Herramientas de conversión HD existen (IDs de mensaje 360/PS3).

## 3. Código de la comunidad

### `b1_i_e.py` — conversión B3↔B1 (mapeo de mesh part headers)
**Export (B3→B1)**: busca `BD 01`/`BD 11`, reescribe `+0: B5 01 +4: BD 29
+12: shader +32..63: matriz identidad`.
**Import (B1→B3)**: busca `B5 01`, reescribe `+0: 35 62 +4: 35 62 +12: FF FF
FF FF +32: 0.8 +36: 0.8 +40: 0.9 +44: 1.0 +48..63: 128.0`.
**Conclusión**: B1 usa headers `BD 01`/`BD 11`; B3 usa `B5 01`/`BD 29`
(= `b3iw_to_b1_ps2.py` inverso). ⚠️ Ver HALLAZGOS_DISCORD sesión 9: en HD los
mesh parts del B3 NO usan type1 0x1BD (los candidatos BD 29 resultaron index
data) → el re-layout de headers es para PS2; el port B3→B1 HD requiere más RE.

## 4. Diagnóstico consolidado (por qué no se importaba)

1. El runtime dibuja con la topología del template (mesh group + arms + IB) →
   vértices del personaje conectados con topología del anfitrión = deforme.
2. El runtime exige conteos fijos (sec34/vb2/IB).
3. El mapeo skin→malla incompleto (31%): el rig PS2 tiene `ch_loc`/`sb_loc`
   → offsets de vértices (Model-Rig Extractor v0.9).

## 5. Estrategia (orden de prioridad, ahora HISTÓRICA)

Pasos que se intentaron (conteos fijos, skin→malla, retopología 3D, mesh
group/IB) → ver AGENTS.md para el estado real: **v8/v12 validado = sec34
nativo + pool world PS2 del modelo B1 correcto**; personaje distinto bloqueado
por el mesh group (requiere OBJ to AMG / retopología). La vía definitiva =
`OBJ → OBJ to AMG (mesh group PS2) → re-layout PS2→HD` (PLAN_PORTS_FUNCIONALES).

## 6. Herramientas adaptadas

`mod center hd\src_comunidad\`: parsers de edición de la comunidad
(amg_a/amo_a/amg_c/axis_e/b1_i_e/amb_c) — documentan la estructura PS2.
Propias: `analyze_b1_hd.py`, `export_sec34_obj.py`, `b3iw_to_b1_ps2.py`,
`azt_to_dds.py`, `build_awg_hd_full.py` (v12).