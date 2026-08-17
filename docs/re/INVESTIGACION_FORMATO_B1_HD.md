# FORMATO DE MODELOS — DBZ BUDOKAI HD COLLECTION (B1, Xbox 360)
> Copyright (c) NovaPowers. Released under the MIT License. Firmado por NovaPowers.
>

> RE del formato de modelos/texturas del recomp B1. Consolidado 14/08/2026.
> Correcciones posteriores (v10-v12) en AGENTS.md (sec34 stride 44, offsets REL).

---

## 1. DIFERENCIA CLAVE CON B3 HD

- **B3 HD**: cada personaje = **#AMB** contenedor (#AWO + #AZT dentro), LZX.
- **B1 HD**: bins separados por tipo, cada uno LZX:
  `#ACM` rig/esqueleto, `#AWO` geometría, `#AZT` texturas DDS (DXT1/3/5),
  `#ZDD` texturas alt, `#CCM/#CSK/#SPX/#CFC/#ACA` datos char.

## 2. BINS DE UN PERSONAJE DE COMBATE (Tenshinhan, verificado)

El juego lee el bloque completo al entrar al combate (log "AFS BIN READ"):

| Bin | Magic | Tamaño | Función |
|---|---|---|---|
| 2445 | #ACM | 1,575,008 | Rig + 42 labels TSH_* |
| 2446-2449 | #CCM/#CFC/#CSK/#SPX | — | Datos |
| **2450** | **#AWO** | 855,584 | **Geometría traje 1** |
| **2451** | **#AZT** | 197,184 | **Texturas (3× DXT3 256×256)** |
| 2452-2455 | #AWO/#AZT | — | Trajes 2-3 |

Patrón: cada traje = #AWO + #AZT; #ACM compartido. Selección usa 1297(#ACM)/1302(#AWO).

## 3. FORMATO #ACM (rig)

`0x00 "#ACM" + 0x0C count + 0x10 id (0xA3 combate/0x93 selección) + 0x18 nº huesos
(42 combate/52 selección) + 0x1C offset labels`. Labels al final (0x18031C en 2445):
`TSH_BODY, TSH_WAIST, TSH_STMC...` (convención `XXX_*`).

## 4. FORMATO #AWO (big-endian)

```
0x00 "#AWO" + 0x10 bones(42) + 0x18 amg count(23) + 0x1C amg table(0x570)
+ 0x20 array count(39) + 0x24 labels(0x5CC)
```
Sin contenedor #AMB. Offsets del header RELATIVOS al #AWO.

## 5. FORMATO #AZT (texturas)

`#AZT` + header + DDS embebidos **DXT3** 256×256 (header 128B + bloques 4×4 de
16B: 8B alpha + 2×2B color RGB565 + 4B índices). Bin 2451: 3 DDS @0x0C0/0x10140/0x201C0.

## 6. PIPELINE DE MODS (validado)

1. Extraer bin del AFS + descomprimir `xbdecompress bin.lzx out.bin`.
2. Modificar contenido.
3. Recomprimir `xbcompress /N:2048` (NUNCA /N:32).
4. **Padding al tamaño del SLOT** con 0x00 (`slot = offset(sig) - offset(bin)`).
5. Colocar en `mods/<mod>/us/<afs>/<entry>/<archivo>`.
6. Solo UN mod habilitado por bin (orden alfabético, primero gana).

Ejemplo validado: `mods/test_tenshinhan_red/.../2451/tex.bin` = DDS[0] rojo →
muñequeras y pantalón rojos.

## 7. LAYOUT DEL #AWG0 (comparado con B3)

| Campo | B3 (Krillin) | B1 (Tenshinhan) |
|---|---|---|
| +0x0C version | 4 | **2** |
| +0x10 bones | 51 | 42 |
| +0x2C vb sec | 0x17868 | 0x2DE40 |
| +0x30 ib | 0x19F68 | 0x30310 |
| +0x34 sec34 | 0x2826 | 0x5D3A |
| +0x38 restart | 0x1C790 | 0x3604C |

> ⚠️ **CORRECCIÓN (16/08, auditoría)**: `+0x34` NO es sec34 — es **post_size**
> (el sec34 va en `+0x28 sec_off`, REL al AWG0). Verificado en TSH nativo
> (AWG0+0x28=0x24D0 → 0x2FF0, 4272 verts). `port_b3_to_b1.py`, `build_awg_hd_full.py`
> y `obj_to_awg_hd.py` ya usan el layout correcto; `scripts_gero/rerig_*.py`
> usan el viejo (bone +18, sec_off +0x34) → NO usar.

Buffers Tenshinhan 2450: sec34 ≈ 4272 verts (stride 44), vb2 214 verts,
ib 11934 índices u16.

## 8. FORMATO DE VÉRTICE (RE 14/08, confirmado por instrumentación del runtime)

**Modelo de combate (stride 44 = 11 dwords, float32 BE)** — idéntico al B3:
```
+00 pos.xyz (12B)  +12 w (peso)  +16 bone index (u32)
+20 normal.xyz     +32 0xFFFFFFFF  +36 uv.xy
```
⚠️ CORRECCIÓN v10: el layout ES `pos + weight@+12 + BONE@+16 + nrm + FFFF + uv`
(AGENTS.md). Antes se reportó bone en +18/+20/+28 en distintas versiones; la
definitiva es **+16**. buffer principal 187968B = 4272 verts.

**Formats Xenos**: fmt 57=k_32_32_32_FLOAT, 36=k_32_FLOAT, 37=k_32_32_FLOAT,
38=k_32_32_32_32_FLOAT, 6=k_8_8_8_8.

## 9. MODEL SWAP ENTRE PERSONAJES (VALIDADO)

### Swap B1→B1 (MÉTODO MÁS FIABLE)
Copiar #AWO + #AZT de un personaje al slot de otro (ambos nativos B1):
- **Piccolo (1768+1769) → slot Tenshinhan (2450+2451)**: perfecto.
- **Gero nativo B1 (52+53) → Tenshinhan**: funciona con estilo artístico B1.
Requisito: el bin fuente cabe en el slot destino.

### Port B3→B1 (PARCIAL: modelo OK, texturas arregladas)
Gero B3 (data_cmn bin 91) → slot TSH: modelo se renderiza. Texturas exigían:
1. Reconstruir AZT con los 10 DDS **contiguos** (`data_off = anterior + size`).
2. **Forzar alpha a 0xFF** en bloques DXT3 (la causa del "cuerpo negro").
3. Mantener 10 slots de textura (el AWO espera 10, no 4).
4. Hash +0x1C correcto.

Materiales: meshpart B1 tiene floats material +0x18..+0x34 (specular alto,
sombreado B1); el B3 (0x1B5) plano → "cartoon". Copiar floats del B1 a meshparts
B3 mejora sombreado (NO convertir type2 a 0x190, rompe layout de vértice).

### Glitches del port B3→B1 (pelo/cara/brazos)
Causa raíz (RE 14/08): **orden de huesos difiere B1 vs B3** (mismos labels,
orden distinto: B3 empieza por RLEGROT). El runtime B1 anima por índice/orden de
la jerarquía, no por label. El re-mapeo de +18 de vértices es parcial (funciona
sin crash pero cuerpo deforme); la solución real = reordenar jerarquía completa
(labels + ejes + armatures + arms + mesh parts + vértices TODO junto) = proyecto
de RE sustancial. **BLOQUEADO** — ver `docs/planes/PLAN_RELAYOUT_B3_B1.md`.

### Skinning B1 vs B3 (RE 14/08)
- **B1**: RIG POR HUESO — armature de cada hueso con rig data (weight groups:
  coords locales + offsets a vértices). El runtime deforma por hueso con rig.
- **B3**: BONE INDEX POR VÉRTICE (+18), sin rig data en armature.
- Al cargar AWO B3 en B1, los bones sin rig data NO se animan → congelados en el
  mundo. Convertir B3→B1 requiere crear rig data por hueso B1.
- +30 del mesh part header = **índice de material/shader** (0-3), NO bone (remap
  causa crash). La tabla post-restart de huesos con sub-mesh también difiere.

### B3: jerarquía de huesos (canónica vs B3)
- B1: `BODY→WAIST→STMC→CHEST→LCHN→[LARM]→[RCHN→RARM]→[NECK→HEAD]→[LLEGROT]→[RLEGROT]`
- B3: `BODY→WAIST→RLEGROT→[pierna der]→STMC→CHEST→RCHN→[brazo der]→NECK→HEAD→LCHN→[brazo izq]→LLEGROT`

## 10. PROYECTO RAGING BLAST 2 (RB2) — DESCARTADO

- Recompile PC del RB2 2010 (Spike Chunsoft), mismo SDK base (ReXGlue) pero
  **xenia-premake estático** (código dentro del exe, NO instrumentable).
- Formato de malla distinto: **STPK/IORAM/VRAM/SPR3/TX2D** (ZPAKs), NO AWO.
- Compresión de bloques `0LCS` = LZ propietario de Spike (no LZX/deflate/LZSS).
- **Conclusión**: RB2 no aporta al skinning AWO B1/B3. Descartado.

## 11. PRIMER PORT FUNCIONAL: GOKU SS2 (B1 PS2) → TENSHINHAN (B1 HD)

> 14/08/2026: el cuerpo de Goku SS2 se ve en el slot Tenshinhan (sin pelo, sin
> texturas correctas). Primer personaje PS2 de B1 renderizando en el recomp.

Técnica validada (`build_b1_goku_final.py`):
```
SkinData (PS2) → mapeo GOK→TSH por labels → coords→world → layout 01BD (44B)
→ relleno en sitio del sec34 manteniendo IB/mesh group/offsets intactos
```
- Mapeo 21 bones por labels (GOK_BODY→XTSH_BODY, etc.), pose_matrix.py para
  world, decimación voxel (cell=0.08 → 443 slots únicos).
- Template Tenshinhan INTACTO; solo se rellenan los primeros N slots del sec34.
- Éxito vs intentos previos: layout 01BD + relleno en sitio (movía offsets vb2/IB
  → crash FIGHT). El runtime B1 lee el bin completo (Gero nativo→2450 funcionaba
  porque comparten layout 01BD).
- **Pendiente histórico**: mapeo skin→malla completo (443/3729 slots),
  pelo (GOK_HAIR*), vb2 (273 slots cabeza), IB correcto, texturas Goku en 2451.
  → SUPERSEDED por la vía v6/v12 (sec34 nativo + vecinos world PS2) en AGENTS.md.

## 12. ARCHIVOS CLAVE

- `%TEMP%\opencode\` — scripts y bins generados por sesión.
- `modding resources discord\` — templates/layouts de la comunidad.
- B3: `awo_tools/` (convert_personaje, rig_mapeo, relayout_awg...).