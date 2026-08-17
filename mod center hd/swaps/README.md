# swap_b1.py — Model swaps B1→B1 automatizados (100% funcionales)

> Herramienta CLI que automatiza la metodología validada de model swaps
> (`docs/tutoriales/MODEL_SWAPS_METODOLOGIA.md`): extraer el par completo
> (geom #AWO + tex #AZT) de un personaje del AFS, comprimirlo, paddearlo e
> instalarlo en el slot destino con el mod activo.
>
> Validado en runtime (16/08): Android 19 (X19G) → slot Tenshinhan.

---

## 1. QUÉ HACE

1. **Escanea el AFS** (`data_sp.afs`) y cataloga personajes por su label raíz
   (`XTSH_BODY`, `X19G_BODY`, `XPIC_BODY`...), agrupando pares geom/tex
   contiguos del mismo bloque.
2. **Extrae el par completo** del personaje origen (geom #AWO + tex #AZT del
   MISMO personaje — requisito nº1 del swap).
3. **Comprime** ambos con `xbcompress /N:2048` (nunca /N:32).
4. **Padea** al tamaño del slot (2450=290816 B, 2451=33504 B).
5. **Verifica round-trip** (descomprime y compara bytes) antes de instalar.
6. **Instala** en `mods/<mod>/us/data_sp.afs/<slot>/geom.bin` y `tex.bin`,
   desactivando el resto de mods automáticamente.

---

## 2. USO

```bash
# 1. Catalogar todos los personajes del AFS
python swap_b1.py --list

# 2. Ver los pares de un personaje (label o bin)
python swap_b1.py --info X19G
python swap_b1.py --info 2450

# 3a. Swap automático por label (extrae del AFS)
python swap_b1.py --origen X19G --dest 2450 --tex 2451

# 3b. Swap por bin numerico
python swap_b1.py --origen 49 --dest 2450 --tex 2451

# 3c. Swap desde archivos ya extraidos (geom.bin + tex.bin en una carpeta)
python swap_b1.py --dir <carpeta> --dest 2450 --tex 2451

# 4. Solo plan, sin instalar
python swap_b1.py --origen X19G --dest 2450 --tex 2451 --dry

# 5. Nombre de mod personalizado
python swap_b1.py --origen X19G --dest 2450 --tex 2451 --mod mi_swap
```

### Argumentos

| Argumento | Descripción |
|---|---|
| `--afs <ruta>` | AFS a usar (default: `assets/eu/data_sp.afs` o `assets/us/`) |
| `--list` | Catalogar personajes |
| `--info <label\|bin>` | Pares geom/tex de un personaje |
| `--origen <label\|bin>` | Personaje a instalar (label raíz o bin del AFS) |
| `--dest <slot>` | Slot geom destino (2450 = Tenshinhan) |
| `--tex <slot>` | Slot tex destino (2451 = Tenshinhan; auto si es conocido) |
| `--dir <carpeta>` | Usar `geom.bin`/`tex.bin` ya extraídos en vez del AFS |
| `--mod <nombre>` | Nombre del mod (default: `swap_<origen>_on_<dest>`) |
| `--dry` | Mostrar el plan sin instalar |
| `--max-bins <n>` | Limitar el escaneo (debug) |

---

## 3. SLOTS DESTINO CONOCIDOS

| Personaje | Slot geom | Slot tex |
|---|---|---|
| Tenshinhan | 2450 | 2451 |
| Goku | 380 / 381 / 536 | 381 |

Para otros destinos usa `--info` con el label del personaje para conocer sus
pares, o `--list` para ver la tabla completa.

---

## 4. REGLAS (lo que garantiza el funcionamiento)

1. **Par geom+tex del MISMO personaje** — el runtime B1 exige que la textura
   (2451) corresponda al modelo (2450); mezclarlos da crash 0xC0000005.
2. **Compresión LZX `/N:2048`** (magic `0F F5 12 EE`). `/N:32` rompe bins.
3. **Padding exacto al tamaño del slot** (más corto = EOF, más largo = ignorado).
4. **El bin debe caber en el slot** tras comprimir (el script lo verifica).
5. **Un solo mod activo a la vez** — el script desactiva el resto.

---

## 5. DEPENDENCIAS

- Python 3 (solo stdlib).
- `xbcompress.exe` / `xbdecompress.exe` (XDK) — se buscan en
  `%TEMP%\opencode\xbcomp` y en el `mod center` del B3.
- El AFS `data_sp.afs` de `assets\eu\` o `assets\us\`.

---

## 6. NOTAS

- El catálogo agrupa pares por contigüidad dentro del bloque del personaje.
  Ej. X19G (bloque 45-49): `45+46`, `47+48`, `49+50` — todos son el mismo
  personaje y cualquiera funciona como origen.
- El script desactiva el resto de mods al instalar (archivo `.disabled` dentro
  de cada carpeta). Para re-habilitar uno: borrar su `.disabled`.
- Los mods se instalan en `mods/<mod>/us/data_sp.afs/<slot>/` — el override no
  depende de la región de assets (match por nombre AFS + entrada).