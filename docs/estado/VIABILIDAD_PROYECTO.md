# VIABILIDAD DEL PROYECTO — DBZ Budokai 1 HD Collection (ReXGlue)

> Copyright (c) NovaPowers. Released under the MIT License. Firmado por NovaPowers.
>
> 2026-08-17. Estado consolidado de TODO lo que funciona y lo que no,
> para preparar la salida. Cada técnica está marcada como ✅ VIABLE
> (validada en runtime), ⚠️ PARCIAL (funciona con limitaciones) o
> ❌ NO VIABLE (descartada con causa).

---

## RESUMEN EJECUTIVO

El proyecto es un **recompile de DBZ Budokai 1 HD (Xbox 360)** con sistema de
mods por overlay de archivos. Hay **TRES vías de modelado validadas**:

1. **Swap nativo B1→B1** — cambiar un personaje por OTRO que ya existe en el
   juego. ✅ 100% funcional, mejor calidad.
2. **Port B3 HD→B1 HD** — meter un personaje del Budokai 3 HD (proyecto
   hermano) al B1. ✅ 100% funcional (validado con Dr. Gero).
3. **Port PS2→HD** — reconstruir un modelo del PS2 (B1/B2/B3) en formato HD.
   ⚠️ **VIABLE pero deforme** — entra en combate sin crash, pero la geometría
   necesita refinamiento.

Los **movesets** (animaciones de combate) son ❌ NO VIABLES sin RE completa.

---

## ✅ VIABLE — VALIDADO EN JUEGO

### 1. Swap nativo B1→B1 (cambiar personaje por otro del mismo juego)

**Estado: 100% FUNCIONAL** (validado 16/08-17/08).

- El runtime dibuja el bin `#AWO` completo tal cual (mesh group + IB + bones +
  UVs). NO valida el slot destino.
- **Requisito crítico**: geom (slot 2450) y tex (slot 2451) deben ser del
  **MISMO personaje**. Mezclarlos → crash `0xC0000005`.
- Ejemplos validados:
  - CHZ HD completo (geom bin 352 + tex 353) → slot TSH: **render perfecto**.
  - Android 19 (X19G, geom 49 + tex 48) → slot TSH: **100% funcional**.
- Herramienta: `mod center hd\swaps\swap_b1.py` (automatiza todo).

### 2. Port B3 HD → B1 HD (personaje del Budokai 3 HD)

**Estado: 100% FUNCIONAL** (validado 16/08 noche, Dr. Gero → slot TSH).

- Un `#AWO` del B3 convertido (flag 0x2, type2 0x1BD/0x11BD, materiales B1,
  AZT con alpha DXT3 0xFF) + su AZT del MISMO personaje funciona en runtime.
- Rig OK, materiales/specular OK, texturas OK, reacciones a daño OK.
- Fallos conocidos: mandíbula abre al recibir daño pero no al usar técnicas
  (rig boca B3); calvos (TSH) → bones de pelo del Gero no responden.
- Herramienta: `conversores/install_b3_to_b1.py` (port + materiales + alpha +
  comprimir + instalar mod, automático).

### 3. Texturas (AZT→DDS)

**Estado: FUNCIONAL** (exportadores/azt_to_dds.py).

---

## ⚠️ PARCIAL — FUNCIONA CON LIMITACIONES

### 4. Port PS2 → HD (reconstrucción completa)

**Estado: ENTRA EN COMBATE SIN CRASH pero DEFORMA** (validado 17/08).

- Pipeline completo validado: parseo de triángulos reales (FaceType) →
  decimación por (bone, voxel) → rellenar sec34/IB/descriptores en posición
  (tamaño fijo, delta=0) → arms intactos → **textura del MISMO par**.
- Resultado: CHZ PS2→slot TSH carga y entra en combate sin crash (log limpio).
- **Deformidad**: la decimación voxel (cell 0.148, 1406 de 4313 verts) +
  descriptores A/B uniformes no respetan la topología → modelo irreconocible.
- **Cómo mejorarlo**: decimación más conservadora + descriptores por-part
  reales (los rangos A/B del template por part, no uniformes).
- Herramienta: `conversores/amo0_to_awo.py`.

### 5. Inyección de posiciones PS2 sobre bin HD anfitrión (v12)

**Estado: 95% de slots reemplazados, deforma en zonas poco densas.**

- Mantiene el IB nativo del anfitrión y sustituye posiciones con el vecino
  PS2 más cercano (pool world global).
- Deformidades en pies, muñequeras, cabeza y piernas (pocos vértices → el
  vecino aproxima mal). Cintura/abdomen bien.
- Útil SOLO si el personaje PS2 y el anfitrión HD son el MISMO (mismo traje).

### 6. Launcher con pestaña de mods + pipeline de modelos

**Estado: FUNCIONAL** (17/08).

- Catálogo de personajes B1 (26) + B3 (56) en `cache/characters.cat`.
- Pestaña Mods: gestión visual con manifest.txt + ejecución asíncrona.
- `launcher_mod_pipeline.py catalog|swap|port`.

---

## ❌ NO VIABLE — DESCARTADO CON CAUSA

### 7. Port de movesets (animaciones de combate)

**Estado: DESCARTADO** (lección 13, 17/08 concluido).

- Instalar el `#CSK` de otro personaje (entry 2448) cambia el moveset pero con
  poses rotas (el `#ACM` del slot no coincide).
- Instalar el `#ACM` de otro personaje (2445) **rompe el modelo** (T-Pose).
- El #ACM HD contiene esqueleto + expresiones faciales (163 bloques en TSH)
  + tabla de labels. Generarlo requiere reconstruir las 9002 poses internas
  (RE completa): cambiar solo labels+conteo → crash `0xC0000005`.
- **El #CSK es sustituible; el #ACM NO.**

### 8. GameCube (.iso GC del B1) como fuente de modelos

**Estado: DESCARTADO** (lección 20, 17/08).

- El GC usa formatos `#ACO/#ACB/#AMB` con `.act/.aco/.acm/.acb` — distinto al
  `#AMO0` PS2 y al `#AWO` HD.
- Los nombres de archivo NO corresponden a personajes (entry 967 "TSH" =
  Trunks). Solo el AFS del PS2 es fuente válida.

### 9. Moveset #CSK del B3 (port de animaciones B3→B1)

**Estado: DESCARTADO** — misma razón que el punto 7.

### 10. Port con cambio de tamaño del AWG0

**Estado: DESCARTADO** (lección 22, B3 §13.5.14).

- El AWG0 NO puede cambiar de tamaño: crecer → crash en combate; encogerse →
  no arranca. La vía correcta es **tamaño fijo (delta=0)**.
- Re-mapear arms también crashea ("los offsets de los arms NO son rangos del
  IB a dibujar; el IB se dibuja completo").

---

## ARCHIVOS AFS — COMPATIBLES E INCOMPATIBLES

### Compatibles (fuentes de modelos PS2)

| AFS | Juego | Uso | Estado |
|---|---|---|---|
| `Budokai 1 Models Converted to AMB\XXX00.bin` | B1 PS2 | Modelos `#AMB` con `#AMO0`+`#AMT` | ✅ **Fuente PRIMARIA** para ports |
| `ps2_games\Budokai 2 (USA)\USR\data_cmn.afs` | B2 PS2 | `#AMB` con trajes alternativos (TSH=282/283/286) | ✅ **Fuente PRIMARIA** para trajes distintos |
| `DBZ Budokai 3 HD Collection\` (AWO B3) | B3 HD | `#AWO`+`#AZT` para port B3→B1 | ✅ **Port B3→B1 validado** |

### Compatibles (assets del recompile)

| Archivo | Uso | Estado |
|---|---|---|
| `assets\eu\data_sp.afs` | Personajes HD del B1 (geom/tex por slots) | ✅ Leído por el runtime |
| `assets\us\data_sp.afs` | Versión US | ✅ Leído por el runtime |
| `assets\eu\adx_us.afs` / `assets\us\adx_us.afs` | Audio | ✅ Intactos |

### Incompatibles (NO usar como fuente)

| Archivo | Por qué |
|---|---|
| `DragonBall Z - Budokai [NGC].iso` | Formatos `#ACO/#ACB` distintos, nombres sin mapear a personajes |
| `Budokai 2` GameCube | Ídem GC |
| `mods/*/us/data_sp.afs` de otros juegos | No son AFS del B1 HD |

---

## FORMATO HD (referencia rápida)

### Vértice sec34 (44B)
```
+00 pos.x +04 pos.y +08 pos.z      (floats BE)
+12 weight (float)                  +16 BONE index (u32, 1-34)
+20 nrm.x +24 nrm.y +28 nrm.z
+32 0xFFFFFFFF                      +36 blend +40 uv
```
`n_sec = sec_size//44`.

### Offsets del header AWG0 (+0x50) — RELATIVOS al AWG0
```
+0x28 sec_off → sec_abs = AWG0+val    +0x2C sec_size → n_sec = sec_size//44
+0x30 post_off → post_abs = AWG0+val   +0x34 post_size
+0x38 siguiente zona (REL AWG0)        +0x3C bones count   +0x40 nombre (16B)
```

### Descriptor de submesh (entre arms y sec34)
```
+00 hdr (0x500 cuerpo/0x400 extremidades)  +08 A_start<<8  +0C A_size<<8
+10 B_start<<8  +14 (B_size<<8)|1  +18 label 16B  +28 flag tipo
+2C 0xF000000  +30 "max N m"  +58 ptr mesh-ref<<8  +5C stride 44<<8
A = rangos de vértices en sec34 (contiguos)  B = rangos de índices en IB
```

### Parsers PS2 (submeshes)
```
mesh part PS2: header 0xA0 + mesh_data con submeshes en cadena
  header 0x20 por submesh: FaceType en +0x10 (1=strip zig-zag, 0=triplete)
                           VertCount en +0x14
```

---

## HERRAMIENTAS DISPONIBLES (`mod center hd\`)

| Herramienta | Uso |
|---|---|
| `swaps/swap_b1.py` | **Swap B1→B1** (catálogo + extraer par geom/tex + comprimir + instalar). `--list`, `--info`, `--origen`, `--dest`, `--tex`, `--dir`, `--mod` |
| `conversores/install_b3_to_b1.py` | **Port B3→B1 automático** (validado Gero). `install_b3_to_b1.py <awo_b3> <azt_b3> --mod <nombre>` |
| `conversores/port_b3_to_b1_v2.py` | Port B3→B1 (flag/type2/materiales/alpha). |
| `conversores/port_b3_to_b1_v4.py` | v2 + retargeting por matrices bind. |
| `conversores/amo0_to_awo.py` | **Port PS2→HD completo** (validado entra en combate). `amo0_to_awo.py <ps2.amb> <template.awo> <out>` |
| `launcher_mod_pipeline.py` | Orquestador del launcher: `catalog`, `swap`, `port`, `--dry`. |
| `analizadores/catalog_b2_ps2.py` | Catálogo de personajes B2 PS2. |
| `analizadores/analyze_submesh*.py` | RE de descriptores de submesh. |
| `analizadores/analyze_b1_hd.py` | Estructura de un bin HD. |
| `exportadores/export_sec34_obj.py` | sec34 → OBJ (inspección). |
| `exportadores/azt_to_dds.py` | Texturas AZT → DDS. |
| `parsers/lib_ps2/` | Parsers PS2 (parse_ps2_model, pose_matrix, extract_hd_mats). |

> Tutorial completo de mods: `docs/tutoriales/TUTORIAL_MODS.md`.