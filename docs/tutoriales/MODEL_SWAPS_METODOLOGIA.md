# MODEL SWAPS EN B1 HD — METODOLOGÍA 100% FUNCIONAL (validada 16/08/2026)

> Copyright (c) NovaPowers. Released under the MIT License. Firmado por NovaPowers.
>
> Método definitivo para cambiar el modelo de un personaje en Budokai 1 HD.
> Validado en runtime con el swap **Android 19 (X19G) → slot Tenshinhan (2450)**:
> renderiza perfecto en combate. Reemplaza las conclusiones erróneas sobre
> "mesh group jerárquico" y "conteos fijos" de SESION8/RECONSTRUCCION.

---

## 1. HALLAZGO CLAVE (por qué antes crasheaba y ahora no)

El modelo del personaje en B1 HD vive en **dos bins del AFS**:
- **geom (2450)** = `#AWO` (malla + esqueleto + material)
- **tex (2451)** = `#AZT` (texturas DXT3 referenciadas por el AWO)

El crash `0xC0000005` en `dbz1.exe+0x8a9b85` era un **MISMATCH DE TEXTURA**:
se cambiaba el geom a un personaje distinto pero el tex seguía siendo de otro.

| Prueba | geom (2450) | tex (2451) | Resultado |
|---|---|---|---|
| A | `52_u.bin` (X20G nativo) | AZT Gero B3 | CRASH 0x8a9b85 |
| B | `49_u.bin` (X19G nativo) | AZT Gero B3 | CRASH 0x8a9b85 |
| **C** | **`49_u.bin` (X19G)** | **`48_u.bin` (AZT X19G)** | **FUNCIONA 100%** |

Solo cambia la textura entre B y C → la causa era el tex, NO la geometría,
ni el mesh group, ni los conteos de bones/AWGs.

---

## 2. METODOLOGÍA PASO A PASO (model swap completo)

### Paso 1 — Identificar el personaje origen y sus bins
El `#AWO` tiene el label del hueso raíz (`XXX_BODY`). Localizar el bin del
personaje en su AFS (ver `docs/referencias/PERSONAJES_BINS.md`).

**IMPORTANTE — identidad por labels, no por suposición:**
| Label | Personaje | Jugable | Bins B1 |
|---|---|---|---|
| `X19G` | **Android 19** | Sí | 45, 47, 49 (#AWO) |
| `X20G` / `20G` | **Dr. Gero** | No (historia) | 52 (#AWO), 53 (#AZT) |
| `XTSH` / `TSH` | Tenshinhan | Sí | 2450 (#AWO), 2451 (#AZT) |

### Paso 2 — Extraer el par completo (geom + tex del MISMO personaje)
Del AFS (entries comprimidas LZX) o del bin descomprimido ya extraído:
```
geom  = #AWO  (ej. 49_u.bin, 561024 B)   → el #AWO directo
tex   = #AZT  (ej. 48_u.bin, 262912 B)   → el #AZT que acompaña al AWO
```
⚠️ El tex DEBE ser el del mismo personaje que el geom. Mezclar geometrías de
un personaje con texturas de otro → crash en runtime.

### Paso 3 — Comprimir ambos con LZX `/N:2048`
```
xbcompress.exe /N:2048  geom.bin  geom.lzx     # NUNCA /N:32
xbcompress.exe /N:2048  tex.bin   tex.lzx
```

### Paso 4 — Paddear a tamaño del slot destino (0x00)
El guest lee cada entry con el tamaño de la tabla AFS original; si el archivo
del mod es más corto, el resto da EOF. Paddear a:
```
slot 2450 (geom)  → 290816 B
slot 2451 (tex)   →  33504 B
```

### Paso 5 — Instalar en el mod
```
mods/<mod>/us/data_sp.afs/2450/geom.bin   (padded)
mods/<mod>/us/data_sp.afs/2451/tex.bin    (padded)
```
Activo = carpeta del mod SIN `.disabled`. Todos los demás mods desactivados.

### Paso 6 — Verificar override y probar
- Lanzar `out\build\win-amd64-release\dbz1.exe` (NUNCA el de la raíz).
- Log debe contener `AFS entry override: ... entry=2450 ... geom.bin` y
  `entry=2451 ... tex.bin`.
- Entrar a combate con el personaje del slot → debe renderizar el nuevo modelo.

---

## 3. REGLAS QUE SÍ IMPORTAN

1. **Par geom+tex coherente** (mismo personaje) — regla #1, sin excepciones.
2. **Compresión LZX `/N:2048`** (magic `0F F5 12 EE`). `/N:32` rompe bins.
3. **Padding exacto al tamaño del slot** (más corto = EOF, más largo = se ignora).
4. El bin DEBE caber en el slot tras comprimir (`49_u.bin`→171468 B < 290816 ✓).
5. El override se activa por **nombre AFS + índice de entry**, sin depender de
   la región (`assets\eu` vs `assets\us`).

---

## 4. LO QUE ANTES SE CREYÓ Y ES FALSO (corregido)

| Creencias anteriores | Realidad (validada) |
|---|---|
| El runtime dibuja con el mesh group nativo → "bloqueador" | El runtime dibuja el bin instalado; el swap completo funciona |
| El mesh group B3 es jerárquico y el B1 plano → crash al portar | El crash real era el tex mismatch; un bin B1 nativo en slot TSH funciona |
| El runtime exige conteos fijos (42 bones / 23 AWGs del TSH) | El X19G (46 bones / 15 AWGs / 4601 verts) funciona en slot 2450 |
| Port B3→B1 requiere aplanar `$grp` | No probado como causa; el camino validado es swap de par nativo B1 |

> El port B3→B1 (geometría de otro juego) quedó **RESUELTO 16/08 noche**: el
> runtime dibuja el bin completo tal cual, así que solo hay que convertir
> sellos + materiales + alpha. Pipeline automático: `install_b3_to_b1.py`.
> Detalle: `docs/re/SESION10_PORT_B3_B1_FUNCIONAL.md`.

---

## 4b. PORT B3 HD → B1 HD (100% FUNCIONAL, validado 16/08)

El swap nativo (sección 1) reveló que el runtime dibuja el bin #AWO completo
tal cual → el port B3→B1 es solo **conversión de sellos + materiales + alpha**:

```
python conversores/install_b3_to_b1.py <awo_b3> <azt_b3> --mod <nombre>
```

Convierte (automatizado):
1. **flag** AWG `0x4→0x2`
2. **type2** mesh part `0x29BD/0x1B5→0x1BD`, sombra `0x1B4→0x190`
3. **u34** `→0xFFFFFFFF`
4. **Materiales B1** (crítico para specular): escala `128.0×4` + weights
   `0.85/0.80/0.70/1.0` + type2→`0x11BD` en no-sombra
5. **AZT**: alpha DXT3 forzado a `0xFF` (crítico — sin esto cuerpo negro)

Sin los pasos 4 y 5 → cuerpo negro (materiales B3 planos + alpha DXT3 variable).
Validado con el Gero B3→slot TSH: renderiza perfecto en combate.

---

## 5. HERRAMIENTAS NECESARIAS

| Herramienta | Uso |
|---|---|
| `xbcompress.exe` / `xbdecompress.exe` | Compresión LZX (`%TEMP%\opencode\xbcomp\`) |
| `analizadores/extract_amb_awo.py` | Extraer #AWO/#AZT desde #AMB HD |
| `analizadores/analyze_b1_hd.py` | Estructura de un bin HD |
| `conversores/port_b3_to_b1_v2.py` | Port B3→B1 (sellos + materiales + alpha) |
| `conversores/install_b3_to_b1.py` | Pipeline completo B3→B1 (port + instalar mod) |
| `swaps/swap_b1.py` | Swap B1→B1 (par nativo) |
| Parser AFS (Python) | Extraer/insertar entries del `data_XX.afs` |
| `mods.cpp` / `afs.cpp` (rexglue-sdk) | Sistema de overrides de mods |

---

## 6. ESTADO VALIDADO (16/08/2026)

- Mod `test_gero_b3_to_b1_v2` ACTIVO = **port Gero B3→B1** (100% funcional):
  `2450/geom.bin` = AWO B3 convertido (flag 0x2, type2 0x11BD, materiales B1)
  `2451/tex.bin`  = AZT B3 con alpha DXT3 0xFF (10 tex) padded 33504
- Mod `test_a19_on_tsh` (swap Android 19) funcional pero desactivado.
- Renderiza perfecto en combate → **model swaps B1→B1 y port B3→B1 100%**.