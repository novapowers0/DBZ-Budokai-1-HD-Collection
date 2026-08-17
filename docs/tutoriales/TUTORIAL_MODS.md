# TUTORIAL DE MODS — DBZ BUDOKAI 1 HD COLLECTION (ReXGlue)

> Guía paso a paso para crear mods funcionales en el recompile del B1 HD.
> Copyright (c) NovaPowers. Released under the MIT License. Firmado por NovaPowers.
>
> Actualizado: 17/08/2026. Cubre los TRES flujos validados (swap B1→B1,
> port B3→B1, port PS2→HD) + conceptos clave.

---

## ÍNDICE

1. [Conceptos clave](#1-conceptos-clave)
2. [Estructura de un mod](#2-estructura-de-un-mod)
3. [Activar/desactivar mods](#3-activardesactivar-mods)
4. [Flujo 1: Swap B1→B1 (el más fácil)](#4-flujo-1-swap-b1b1)
5. [Flujo 2: Port B3 HD→B1 HD](#5-flujo-2-port-b3-hdb1-hd)
6. [Flujo 3: Port PS2→HD (experimental)](#6-flujo-3-port-ps2hd)
7. [Compresión y padding](#7-compresión-y-padding)
8. [Verificación y debugging](#8-verificación-y-debugging)
9. [Referencias rápidas](#9-referencias-rápidas)

---

## 1. CONCEPTOS CLAVE

- **Recompile**: el juego original (Xbox 360) recompilado a Windows nativo.
  Se lanza con `out\build\win-amd64-release\dbz1.exe`.
- **AFS**: contenedor de archivos del juego. Los personajes viven en
  `data_sp.afs` (geom/tex) y `data_cmn.afs` (esqueleto/moveset).
- **Slots de personaje**: cada personaje ocupa varias entradas del AFS.
  Tenshinhan (TSH) = 2450 (geom) + 2451 (textura) + 2445 (#ACM esqueleto)
  + 2448 (#CSK moveset).
- **#AWO**: modelo (geom) HD big-endian. **#AZT**: texturas HD.
- **#AMO0**: modelo PS2 little-endian. **#AMT**: texturas PS2.
- **Tex mismatch = crash**: si la textura (2451) no corresponde al MISMO
  personaje que la geometría (2450), el juego crashea con `0xC0000005`.
  **Siempre verificar el par geom+tex del mismo personaje.**

---

## 2. ESTRUCTURA DE UN MOD

```
mods/<nombre_mod>/
├── .disabled                    # opcional: si existe, el mod está DESACTIVADO
└── us/
    └── data_sp.afs/
        ├── 2450/
        │   └── geom.bin         # modelo comprimido LZX + padding
        └── 2451/
            └── tex.bin          # textura comprimida LZX + padding
```

- **Overlay**: los archivos del mod REEMPLAZAN las entradas del AFS sin
  tocar el AFS original. El runtime los sirve por nombre AFS + índice.
- La región (`us` o `eu`) se ignora para el match — ambos funcionan.

---

## 3. ACTIVAR/DESACTIVAR MODS

- **Desactivar**: crea un archivo `.disabled` DENTRO de la carpeta del mod:
  ```
  mods/foo/.disabled
  ```
  (NO renombrar la carpeta a `foo.disabled`).
- **Activar**: borra el `.disabled`.
- El launcher (pestaña Mods) lo hace visualmente.

## 3b. EDITAR DESCRIPCIÓN / AUTOR / VERSIÓN DE UN MOD

Cada mod puede tener un `manifest.txt` opcional con metadatos que el launcher
muestra (descripción, autor, versión, tipo, origen, destino):

```
mods/foo/manifest.txt
  name=Mi mod
  description=Cambia Goku por Android 19
  author=Nombre
  version=1.0
  type=swap_b1
  source=Android 19 (B1)
  target=Tenshinhan (B1)
```

**Editar desde el launcher**: en la pestaña Mods, cada mod tiene un botón
`Editar` que abre un formulario en línea para descripción, autor y versión.
Al pulsar `Guardar` se escribe/actualiza `manifest.txt` en la carpeta del mod.
Campos vacíos se eliminan del manifest.

---

## 4. FLUJO 1: SWAP B1→B1

Cambiar un personaje por OTRO que ya existe en el juego. **100% funcional.**

### Requisitos
- El personaje origen existe en el AFS del B1 HD.
- Usar el par geom+tex del MISMO personaje.

### Pasos

**4a. Ver el catálogo** (listo los personajes y sus pares geom/tex):
```bash
python "mod center hd\swaps\swap_b1.py" --list
```

**4b. Ver los pares de un personaje** (ej. Chaozu):
```bash
python "mod center hd\swaps\swap_b1.py" --info CHZ
```
Salida: `XCHZ_BODY (bloque 1432-1435)` con pares `geom/tex` (1432/1433
= 1 AWG solo cuerpo; 1435/1436 = 3 AWGs cuerpo+manos).

**4c. Instalar el swap** (Chaozu → slot Tenshinhan 2450/2451):
```bash
python "mod center hd\swaps\swap_b1.py" --origen CHZ --dest 2450 --tex 2451 --mod mi_swap_chz
```
O por número de bin: `--origen 1435 --tex 1436`.

**4d. Con archivos ya extraídos** (geom.bin + tex.bin en una carpeta):
```bash
python "mod center hd\swaps\swap_b1.py" --dir <carpeta> --dest 2450 --tex 2451 --mod mi_swap
```

**4e. Probar en combate** — entrar en combate con el personaje del slot.

> ⚠️ **Verifica el par geom+tex ANTES de testear**. El crash 0xC0000005 es
> casi siempre tex mismatch. No asumas por cercanía de números.

---

## 5. FLUJO 2: PORT B3 HD→B1 HD

Meter un personaje del Budokai 3 HD al B1. **100% funcional** (Dr. Gero).

### Requisitos
- Un `#AWO` + `#AZT` del B3 HD (proyecto hermano: `DBZ Budokai 3 HD
  Collection\`).
- Convertir el AWO B3 → formato B1 (flag, type2, materiales, alpha).

### Pasos

**5a. Port automático** (recomendado — validado):
```bash
python "mod center hd\conversores\install_b3_to_b1.py" <awo_b3> <azt_b3> --mod mi_gero
```
Hace TODO: port AWO + materiales B1 + alpha AZT + comprimir + instalar.

**5b. Port manual en 2 pasos**:
```bash
python "mod center hd\conversores\port_b3_to_b1_v4.py" <awo_b3> <azt_b3> <out.awo> <out_azt.bin>
# luego instalar con swap_b1.py --dir (ver 4d)
```

### Qué convierte el port
- AWG flag `0x4` (B3) → `0x2` (B1).
- Mesh part `type2` `0x29BD` (B3) → `0x1BD`/`0x11BD` (B1).
- Materiales B1: escala 4×128.0 + weights torso 0.85/0.80/0.70/1.0.
- AZT: alpha DXT3 → 0xFF (B1 espera texturas opacas).

### Fallos conocidos
- Mandíbula abre al recibir daño pero no al usar técnicas.
- Personajes calvos → bones de pelo del invitado no responden.

---

## 6. FLUJO 3: PORT PS2→HD

Reconstruir un modelo del PS2 (B1/B2/B3) en formato HD. **⚠️ EXPERIMENTAL —
entra en combate sin crash pero DEFORMA** (validado 17/08 con Chaozu).

### Cuándo usarlo
- Personajes que NO existen en HD (o con traje distinto, ej. Tenshinhan B2).

### Requisitos
- Modelo PS2 en `#AMB` con `#AMO0` (B1 PS2: `Budokai 1 Models Converted to
  AMB\XXX00.bin`; B2 PS2: `ps2_games\Budokai 2 (USA)\USR\data_cmn.afs`).
- Un bin HD del MISMO esqueleto como plantilla estructural.
- **El par geom+tex correcto del personaje HD** (NO usar tex de otro par).

### Pasos

**6a. Port**:
```bash
python "mod center hd\conversores\amo0_to_awo.py" <ps2.amb> <template.awo> <out.awo>
```

**6b. Instalar** con la textura del MISMO par del template:
```bash
# prepara carpeta con out.awo como geom.bin + tex del MISMO par como tex.bin
python "mod center hd\swaps\swap_b1.py" --dir <carpeta> --dest 2450 --tex 2451 --mod mi_port
```

### Limitaciones actuales
- Deformidad por decimación voxel agresiva + descriptores A/B uniformes.
- Para port fiel: decimación más conservadora + descriptores por-part reales.

---

## 7. COMPRESIÓN Y PADDING

Los bins del `data_sp.afs` van comprimidos LZX (magic `0F F5 12 EE`).

- **Compresión**: `xbcompress.exe /N:2048` — **NUNCA /N:32** (los bins de
  modelos usan /N:2048).
- **Padding**: rellenar con `0x00` hasta el tamaño del slot
  (2450 geom = 290816 B, 2451 tex = 33504 B).
- **Verificación**: descomprimir con `xbdecompress.exe` y comparar byte a
  byte con el original (round-trip).

Las herramientas `swap_b1.py` y `install_b3_to_b1.py` hacen esto
automáticamente.

---

## 8. VERIFICACIÓN Y DEBUGGING

### Verificar que el mod se cargó
El log del juego muestra el override:
```
[fs] AFS entry override: data_sp.afs entry=2450 ... -> mods/<mod>/...geom.bin
```
Logs: `out\build\win-amd64-release\logs\dbz1_NNN.log`.

### Diagnóstico de crash
| Síntoma | Causa probable |
|---|---|
| `0xC0000005` + `PM4_DRAW_INDX(0,63,0)` | **Tex mismatch** (geom/tex de distinto personaje) |
| Cuelga al arrancar | Bin comprimido NO cabe en el slot (truncado) |
| Cuelga al cargar | Descriptores de submesh copiados de otro template |
| Crash en combate con AWG0 agrandado | Cambió el tamaño del AWG0 (debe ser fijo) |
| Modelo deforme | Decimación voxel agresiva / inyección por vecino |

### Log de AFS
`[info] [core] AFS BIN READ: data_sp.afs entry=2450 entrySize=290640`

---

## 9. REFERENCIAS RÁPIDAS

- **Slots de personajes**: `docs/referencias/PERSONAJES_BINS.md`
  (TSH: 2445 #ACM → 2450 geom → 2451 tex; Goku: 368 → 380/381/536).
- **Catálogo maestro de personajes**: `mod center hd/characters_db.py`
  (nombres, variantes, jugable/no-jugable de B1 HD, B3 HD y B1 PS2).
- **Catálogo generado**: `mod center hd/cache/characters.cat`
  (109 modelos B1 + 183 B3, con nombre + variante + jugable).
- **Set de archivos del personaje**: `docs/re/ANIMACIONES_MOVESETS_HD.md`.
- **Viabilidad del proyecto**: `docs/estado/VIABILIDAD_PROYECTO.md`.
- **Formato de mods detallado**: `docs/tutoriales/FORMATO_MODS.md`.
- **Metodología de swaps**: `docs/tutoriales/MODEL_SWAPS_METODOLOGIA.md`.
- **Proyecto hermano (B3)**: `DBZ Budokai 3 HD Collection\mod center hd\GUIA_SWAPS_Y_PORTS.md`.

### Personajes en el catálogo del launcher

El launcher muestra cada modelo con **nombre + variante** (ej. `Goku (SSJ2)`,
`Freeza (Forma 4)`, `Uub`), y marca con `[NO JUGABLE]` los modelos de
historia/cinemática (Dr. Gero, Dende, Roshi, Bulma...). Un personaje con
varios trajes/transformaciones aparece como varias entradas seleccionables.

### Regenerar el catálogo (si se añaden personajes)

```bash
python "mod center hd\launcher_mod_pipeline.py" catalog
```

### Comandos útiles

```bash
# catálogo
python "mod center hd\swaps\swap_b1.py" --list
# info personaje
python "mod center hd\swaps\swap_b1.py" --info <LABEL>
# swap B1→B1
python "mod center hd\swaps\swap_b1.py" --origen <LABEL> --dest 2450 --tex 2451 --mod <nombre>
# port B3→B1
python "mod center hd\conversores\install_b3_to_b1.py" <awo_b3> <azt_b3> --mod <nombre>
# port PS2→HD
python "mod center hd\conversores\amo0_to_awo.py" <ps2.amb> <template.awo> <out.awo>
# sec34 → OBJ (inspección visual)
python "mod center hd\exportadores\export_sec34_obj.py" <bin.awo> <out.obj>
# texturas AZT → DDS
python "mod center hd\exportadores\azt_to_dds.py" <bin.azt> <out.dds>
```