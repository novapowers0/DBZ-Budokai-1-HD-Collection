# FORMATO DE MODS — DBZ BUDOKAI HD COLLECTION (Xbox 360)

> Copyright (c) NovaPowers. Released under the MIT License. Firmado por NovaPowers.
>
> Cómo funcionan los mods en el recomp y cómo crear uno. Actualizado: 13/08/2026.

---

## 1. Dos tipos de override

### 1.1 Override de archivo completo
Reemplaza un `.afs` entero (p. ej. `adx_us.afs`, `data_us.afs`).

```
mods/<mod>/<archivo>              # mods/og_music/adx_us.afs
mods/<mod>/us/<archivo>           # variante región US
mods/<mod>/eu/<archivo>           # variante región EU
```

Usado por `og_music`. El hook vive en `HostPathEntry::Open`
(`AfsFindModFileOverride`).

### 1.2 Override por entrada (bin/pista)
Reemplaza UNA entrada dentro de un `.afs` sin reempaquetar. Dos formatos
equivalentes:

```
mods/<mod>/us/<afs>/<índice>            # archivo directo
mods/<mod>/us/<afs>/<índice>/<archivo>  # carpeta con un archivo dentro
```

Ejemplo real validado:
```
mods/example_music_swap/us/adx_us.afs/111/music.adx     # opening
mods/example_music_swap/us/adx_us.afs/1255/music.adx    # menú principal
```

El hook vive en `HostPathFile::ReadSync` (`ResolveEntryOverride` +
`AfsFindModOverride`). Cada read que cae en el rango `[entry_start,
entry_start+entry_size)` de una entrada con override se sirve desde el
archivo del mod (offset relativo a la entrada).

---

## 2. Reglas y límites

- **Tamaño**: el guest lee cada entrada con el tamaño que tiene la tabla AFS
  original. Si el archivo del mod es MÁS CORTO, se lee lo que haya y el resto
  devuelve EOF (silencio / fin). Si es MÁS LARGO, el exceso se ignora. Para
  bins de datos (modelos) conviene mantener el mismo tamaño; para ADX se puede
  usar una pista más corta.
- **Rendimiento**: negative cache por contenedor (`AfsContainerHasNoEntryOverrides`):
  si ningún mod tiene la carpeta `mods/*/us/<afs>/`, los reads del contenedor
  van directos sin indexar (crítico para el streaming de audio).
- **Prioridad**: los mods se ordenan alfabéticamente; el primer match gana.
- **Enable/disable**: carpeta `mods/<mod>/` sin `.disabled` = activo. El launcher
  (tabla Mods) lo gestiona.

---

## 3. Formato AFS (confirmado)

```
offset 0:  "AFS" (3 bytes) + 1 byte padding
offset 4:  entry count (uint32 LE)
offset 8:  tabla: (address uint32, size uint32) -- 8 bytes/entrada
```
- Entradas alineadas a 0x800; datos en [address, address+size).
- En la HD 360 los bins de `data_XX.afs` van **comprimidos LZX** (magic
  `0F F5 12 EE`, `/N:32`). En `adx_XX.afs` son ADX directos (sin comprimir).
- El índice AFS = número de bin. El AFL (`data_cmn.afl`, registros fijos de
  32 bytes) mapea nombre → bin.

---

## 4. Músicas del menú (adx_us.afs, 1541 pistas) — verificado 13/08

| Entrada | Tamaño | Uso |
|---|---|---|
| 111 | 2,918,214 | Opening |
| 1255 | 7,896,046 | Menú principal |
| 1256/1257 | 8,173,568 c/u | Otras pistas (menú de duelo / selección) |
| 82, 1116 | ~9-10MB | Música de combate |

> La identificación se hizo por instrumentación: se loguearon los offsets de
> los reads del `adx_us.afs` y se mapearon a entradas con el parser AFS.

---

## 5. Recursos de la comunidad (compartidos con Budokai 3)

En el proyecto hermano `DBZ Budokai 3 HD Collection\` (raíz configurable con
la variable `DBZ3_ROOT`):

- `AWO_FORMAT.md` — formato completo AFS/AFL/LZX/#AMB/#AWO (BE 360 vs LE PS2).
- `mod center\` — herramientas: AFS Toolset, CRI ADX Tools, Budokai AMB
  Packer-Unpacker, Model tools, xbcompress/xbdecompress (XDK).
- `modding resources\` + `modding resources update\` — listas de bins
  (`DBZ_B3_Character_Bin_List.txt`, etc.), modelos convertidos, packs.
- `awo_tools\` — scripts de la raíz del proyecto B3.

Nota: los bins de personajes de B1 viven en sus propios AFS con numeración
propia; el B3 comparte numeración con la GH PS2 (Krillin 327-329), pero B1
requiere su propia verificación por instrumentación.
