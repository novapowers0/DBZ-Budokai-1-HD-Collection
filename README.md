# DBZ Budokai 1 HD Collection — Recompile ReXGlue + Modding

Copyright (c) 2026 **NovaPowers**. Released under the MIT License (see `LICENSE`).

Static recompilation of **Dragon Ball Z: Budokai HD Collection** (Xbox 360) for
Windows, built on the [ReXGlue SDK](https://github.com/rexglue/rexglue-sdk),
with a launcher and a model-modding system validated in-game.

> ⚠️ **Origen**: este proyecto se **rehízo desde cero** sobre ReXGlue. El
> repositorio [`WistfulHopes/DBZ1`](https://github.com/WistfulHopes/DBZ1) se
> tomó **solo como referencia** (para entender la API del SDK), **NO como base
> ni copia de código**. El launcher, mods, regiones y herramientas son trabajo
> original de **NovaPowers**.

---

## ⚖️ Copyright / Legal

**El juego y sus datos NO se distribuyen.** Debes aportar los archivos de tu
**copia legal** del juego (el `.xex` y los `data_*.afs`). Este proyecto sigue la
convención "copyright-friendly" de la comunidad de recompilación estática
(como `mstan/DragonBallZBuusFuryRecomp`): el código y el launcher se
distribuyen, **el contenido del juego no**.

- Ver `baserom.md` para la identidad exacta de los archivos (tamaño y checksums)
  y cómo extraerlos de la ISO.
- El código recompilado (`generated/`) se genera **localmente** a partir de tu
  `.xex` y **no se sube** al repositorio.

Proyecto no oficial, sin fines comerciales, de investigación y preservación.
No está afiliado ni avalado por Bandai Namco, Shueisha, Toei Animation ni ningún
titular de los derechos de Dragon Ball.

---

## Estructura de carpetas

```
DBZ-Budokai-1-HD-Collection/
├── assets/                  # NO incluido. Tus archivos del juego (ver baserom.md)
│   ├── default.xex          #   el ejecutable (USA y EU son idénticos)
│   ├── us/                  #   datos región USA (data_us.afs, adx_us.afs...)
│   └── eu/                  #   datos región EU/PAL (data_en.afs, adx_jp.afs...)
├── src/                     # Código fuente del recompilador/launcher/mods
│   ├── main.cpp             #   entrada, ventana, crash handler
│   ├── region.cpp           #   montaje de assets us/eu
│   ├── mods.cpp             #   sistema de mods (overlay AFS)
│   ├── launcher/            #   UI del launcher + pipeline de modelos
│   └── ingame/              #   menú in-game (F10)
├── generated/               # NO incluido. Código generado del .xex (ver README ahí)
├── mod center hd/           # Herramientas Python de modding (propias)
│   ├── paths.py             #   rutas portables (sin rutas de usuario)
│   ├── characters_db.py     #   catálogo maestro de personajes
│   ├── swaps/               #   swaps B1→B1
│   ├── conversores/         #   ports (B3→B1, PS2→HD)
│   ├── analizadores/        #   RE de bins HD
│   └── exportadores/        #   exportar OBJ/DDS/FBX
├── mods/                    # Carpeta de mods de usuario (vacía)
├── tools/                   # xbcompress.exe / xbdecompress.exe (portables)
├── docs/                    # Documentación completa
├── CMakeLists.txt           # Build (REXSDK_DIR o rexglue/ junto al proyecto)
├── baserom.md               # Archivos del juego requeridos + cómo extraerlos
└── LICENSE                  # MIT (NovaPowers)
```

---

## Quick start (jugadores)

1. **Descarga** el ZIP de Windows desde la pestaña **Releases** y extráelo.
2. **Aporta los archivos del juego**: crea `assets/` junto a `dbz1.exe` y copia
   el `.xex` y los `data_*.afs` de tu copia legal (ver `baserom.md` y "Instalar
   el juego" abajo).
3. **Ejecuta** `dbz1.exe`.
4. En el launcher elige **Región** (USA / EU PAL), **Idioma**, **Vídeo** y
   **Audio**, y pulsa **Play**.

> El launcher recuerda la configuración. Si marcas "Skip launcher on boot",
> los siguientes arranques van directos al juego.

### Instalar el juego (aportar los archivos)

El paquete de release **no trae** los archivos del juego (copyright). Tienes
que extraerlos de tu **ISO legal** de *Dragon Ball Z: Budokai HD Collection*
(Xbox 360):

1. Extrae la ISO con una herramienta tipo `extract-xiso` (lee el sistema de
   archivos FATX de Xbox 360).
2. Copia a `assets/default.xex` el ejecutable del juego.
3. Copia la carpeta de datos de tu región:
   - **USA**: a `assets/us/` → `data_us.afs`, `data_sp.afs`, `data_fr.afs`,
     `adx_us.afs`, `data_yah.afs`.
   - **EU/PAL**: a `assets/eu/` → `data_en.afs`, `data_fr.afs`, `data_ge.afs`,
     `data_it.afs`, `data_sp.afs`, `adx_jp.afs`, `data_yah.afs`.
4. Verifica los archivos contra `baserom.md` (tamaños y checksums SHA-256).

Solo necesitas el ejecutable y los archivos de datos, **no toda la ISO**.

---

## Regiones EU/US

- Los `.xex` USA y EU son **byte-idénticos** (misma región lógica; la región
  está en los datos).
- El launcher (pestaña *Video* → *Region*: `USA` / `EU (PAL)`) o el cvar
  `dbz1_region` montan `assets/us` o `assets/eu` en `game:\us`.
- El guardado es compartido entre regiones.

---

## Bugs conocidos (blackouts)

Pantalla en negro (blackout) en determinadas secuencias renderizadas. Todos
comparten la misma causa raíz: la animación/escena no se resuelve al
render-target que se presenta (el personaje queda fuera del frustum de recorte
con `clip_disable=0` → no rasteriza → negro opaco). En Xenia el mismo juego
muestra estas escenas correctamente.

| Bug | Estado |
|---|---|
| Blackout al entrar en combate (duelo, ~4.5s) | ⚠️ Diagnosticado, no bloquea |
| Blackout en modo historia | ⚠️ Conocido |
| Blackout en combates con presentación inicial | ⚠️ Conocido |
| Blackout en ataques definitivos | ⚠️ Conocido |

Los blackouts no bloquean la jugabilidad (solo una pausa en negro); el juego
continúa correctamente después. Detalle técnico:
`docs/re/INVESTIGACION_BLACKOUT_DUELO.md`.

---

## Mods

> 🚧 **Estado: WIP (Work In Progress / en desarrollo).** El sistema de mods
> funciona, pero es experimental y puede cambiar. Úsalo con copias de seguridad.

### Cómo funcionan

Los mods **no modifican** los archivos originales del juego. En lugar de eso,
el launcher aplica un **overlay**: reemplaza entradas concretas del AFS en
memoria/arranque. Cada mod vive en una carpeta `mods/<nombre>/` (la carpeta
`mods/` del repo se distribuye **vacía** — el contenido de los mods depende de
datos con copyright del juego, así que no se incluyen):

```
mods/<mod>/us/data_sp.afs/2450/geom.bin   # modelo del slot 2450
mods/<mod>/us/data_sp.afs/2451/tex.bin    # textura del slot 2451
mods/<mod>/.disabled                      # si existe, el mod está OFF
```

- `2450` = geometría (modelo), `2451` = texturas. Esos "slots" corresponden a
  la numeración interna de bins del personaje.
- El override se instala en **todos** los `data_*.afs` de personaje, de modo
  que funciona independientemente del AFS concreto que elija el juego según
  región/idioma.
- Un mod se activa/desactiva desde el launcher (pestaña Mods) o creando/
  borrando el archivo `.disabled`.

### Consumo de espacio

⚠️ **Los mods de modelos ocupan bastante espacio en disco.** Cada mod es una
**copia completa** del bin del personaje (geometría + texturas) comprimida y
paddeada, y se replica en **todos** los `data_*.afs` de personaje de la región
para que funcione en cualquier idioma. En la práctica:

- Un modelo + su textura suelen ocupar **~5–30 MB por mod** (comprimido).
- Como el override se copia en varios AFS, el total puede multiplicarse.
- Con varios mods activos a la vez, **es fácil acumular cientos de MB** de
  overlays en `mods/`.

Por eso se recomienda: activar solo los mods que vayas a usar, y eliminar los
que ya no necesites (el launcher permite gestionarlos).

### Crear / instalar

Gestión visual en el launcher (pestaña Mods) o con las herramientas de
`mod center hd/` (swaps B1→B1, port B3→B1, port PS2→HD). Guía completa:
`docs/tutoriales/TUTORIAL_MODS.md` y `docs/tutoriales/FORMATO_MODS.md`.

---

## Estado (17/08/2026)

| Técnica | Estado |
|---|---|
| Swap nativo B1→B1 | ✅ **100% funcional** (CHZ, Android 19) |
| Port B3 HD→B1 HD | ✅ **100% funcional** (Dr. Gero) |
| Port PS2→HD | ⚠️ **VIABLE** — entra en combate, modelo deforme por decimación |
| Port de movesets | ❌ No viable sin RE completa (#ACM) |
| GameCube como fuente | ❌ Formato distinto (#ACO/#ACB) |

---

## Building from source (desarrolladores)

Requisitos: compilador C++23, CMake ≥ 3.25, y el [ReXGlue SDK](https://github.com/rexglue/rexglue-sdk)
(`REXSDK_DIR` o una carpeta `rexglue/` junto al proyecto).

```
git clone --recurse-submodules https://github.com/novapowers0/DBZ-Budokai-1-HD-Collection.git
cd DBZ-Budokai-1-HD-Collection
# 1) aporta tu .xex legal en assets/default.xex
# 2) regenera el código derivado del xex
cmake --build out/build/win-amd64-release --target dbz1_codegen
# 3) compila
cmake -S . -B out/build/win-amd64-release --preset win-amd64-release
cmake --build out/build/win-amd64-release
# 4) ejecuta
out\build\win-amd64-release\dbz1.exe
```

> El código recompilado (`generated/`) se deriva de tu `.xex` y **nunca se
> sube** (ver `generated/README.md` y `.gitignore`).

---

## Rutas portables

- Las herramientas detectan los AFS desde `assets/` o desde la ruta que les
  pases en el launcher (pestaña Mods → Archivos fuente).
- El proyecto B3 se localiza con la variable `DBZ3_ROOT` o como carpeta
  hermana `DBZ Budokai 3 HD Collection`.
- `xbcompress.exe`/`xbdecompress.exe` viven en `tools/` (o vía
  `DBZ1_XBCOMP_DIR`).

---

## Créditos

- [ReXGlue](https://github.com/rexglue/rexglue-sdk) — herramientas de
  recompilación.
- [WistfulHopes/DBZ1](https://github.com/WistfulHopes/DBZ1) — referencia de la
  API del SDK (no usado como base).
- Comunidad de modding de Budokai — herramientas y modelos de referencia.
- **NovaPowers** — autor del sistema de mods, launcher y herramientas.
