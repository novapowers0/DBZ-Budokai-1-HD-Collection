# HOJA DE RUTA — MODEL SWAPS + MEJORA DE HERRAMIENTAS (2026-08-14)
> Copyright (c) NovaPowers. Released under the MIT License. Firmado por NovaPowers.
>

> Propuesta del usuario tras el crash del Tenshinhan B3→B1. Reenfoque:
> dominar los swaps funcionales ANTES de portear modelos.

---

## 1. Estado actual (qué funciona y qué no)

| Swap | Estado | Detalle |
|---|---|---|
| **B1 HD → B1 HD** | ✅ **FUNCIONA 100%** | Android 19 (X19G) en slot Tenshinhan → perfecto. Par geom+tex del MISMO personaje |
| **B3 HD → B1 HD** | ✅ port binario, ⚠️ crash por tex mismatch | Flag +0x0C=0x4 (B3) vs 0x2 (B1) + type2 + bones. El crash 0x8a9b85 era el tex, no el mesh group |
| **B1 PS2 → B1 HD** | ❌ deforme (histórico) | Goku SS2 → template Gero/Tenshinhan. Ver AGENTS.md para el estado v12 |
| **B1 PS2 → B1 HD (Piccolo)** | ✅ FUNCIONA | El bin Piccolo del mod es un #AWO reconstruido |

**Estado real (2026-08-16, tarde)**: el swap B1→B1 está RESUELTO. El crash
del port B3→B1 era un **mismatch de textura** (geom de un personaje + tex de
otro). Con el par nativo completo (geom 2450 + tex 2451 del mismo personaje)
el modelo renderiza perfecto. Metodología:
`docs/tutoriales/MODEL_SWAPS_METODOLOGIA.md`.

**El caso Piccolo es LA REFERENCIA**: un bin #AWO directo con estructura
propia (19 AWGs: body + dedos + caras) que el runtime acepta y renderiza
perfecto. ⚠️ Era un SWAP interno B1→B1, no un port (sesión 5).

## 2. Hallazgos clave (sesión 5)

### 2.1 Flag +0x0C del AWG (crash B3→B1)
- B1 HD: `+0x0C = 0x2` en todos los AWGs; B3 HD: `0x4`. El port B3→B1
  requiere flag 0x2 (probado, aún crashea → hay más).

### 2.2 Layout del vértice HD (stride 44, BE) — ver AGENTS.md (BONE@+16)
⚠️ El `+36 FFFFFFFF +40 uv` de este doc era pre-v10. El layout definitivo:
`pos3 @+0, weight @+12, BONE @+16, nrm3 @+20, FFFFFFFF @+32, blend @+36, uv @+40`.

### 2.3 El bin funcional del Piccolo (estructura correcta)
1 AWG por AMG del PS2 (cuerpo + dedos + caras), cada uno con su sec34/vb2/IB/
ejes/mesh group. NO es el template del anfitrión.

## 3. Hoja de ruta

### Fase 1 — Dominar los swaps
- **1.1 Swap interno B1→B1 (VALIDADO, ampliar)**: probar con Goku/Vegeta/
  Frieza HD extrayendo su #AWO del contenedor del AFS.
- **1.2 Swap interno B3→B3 (NO probado)**: intercambiar nativos B3 para ver
  consistencia interna del formato.
- **1.3 Port B3→B1 (el reto)**: crash persiste con flag 0x2 → comparar mesh
  group/zona subs del B3 vs B1 byte a byte. Dejado para el final.
- **Estado real (2026-08-15)**: el port B3→B1 del Gero SÍ se logró vía
  `port_b3_to_b1.py` (flag 0x2 + type2 0x1BD + bones verts+arms) — ver AGENTS.md.

### Fase 2 — Mejorar las herramientas (mod center hd)

| Herramienta comunidad | Adaptar a HD |
|---|---|
| **OBJ to AMG v0.92** | ✅ Pipeline de retopología → genera AMG PS2. Adaptar a AWG HD |
| **AMO Decompiler/Compiler** | ✅ Parseo/creación de AMO. Referencia del formato |
| **Model Rig Toolset V0.6** | ✅ Mapeo skin→malla (ch_loc/sb_loc) |
| **EMD to AMG v0.90** | 🔬 Modelos externos → AMG |
| **B3-IW AMO Converter + Shadows** | ✅ B3/IW→B1 PS2 (ya decompilado: b3iw_to_b1_ps2.py) |
| **AMBStudio / AMB Tool / Packer** | ✅ Empaquetado AMB |

**Prioridad**: (1) OBJ to AMG → OBJ to AWG HD; (2) AMO Decompiler → parser HD;
(3) unificar conversores con la estructura del Piccolo (1 AWG por AMG).

### Fase 3 — Port PS2 → HD (a gran escala)
B1/B2/B3/IW/SB (PS2) → B1/3 HD con estructura 1 AWG por AMG. ⚠️ B2 tiene
traje distinto (descartado para TSH); usar siempre modelos del MISMO juego/labels.

## 4. Documentación a consultar

- `mod center hd/README.md`, `docs/re/INVESTIGACION_FORMATO_B1_HD.md`,
  `docs/re/ESTRUCTURA_AWG_B1.md`, `docs/planes/PLAN_AFS_OUT_RE_COMPARATIVA.md`
- Discord: ReXGlue Project + Dragon Ball Z Budokai Modding Community.