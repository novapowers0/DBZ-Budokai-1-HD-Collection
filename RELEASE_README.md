# DBZ Budokai 1 HD Collection - Release ejecutable

Copyright (c) 2026 **NovaPowers**. Released under the MIT License.

Este paquete contiene el ejecutable recompilado de *Dragon Ball Z: Budokai HD
Collection* (Xbox 360) con el launcher, el sistema de mods y el pipeline de
modelos. **NO incluye los assets del juego** (tienen copyright): debes extraer
los de tu copia legal.

## Contenido

- `dbz1.exe` - el recompilador + launcher + sistema de mods
- `rexruntime.dll` - runtime ReXGlue
- `rexgpu-xenos.dll` - plugin GPU (Xenos)
- `TracyClient.dll` - profiling (requerido por el runtime)

## Cómo jugar

1. Crea una carpeta `assets/` junto a estos archivos (o en un directorio padre
   del exe).
2. Dentro de `assets/`, extrae los AFS de tu copia legal del juego:
   - Región **USA**: `data_us.afs`, `data_sp.afs`, `data_fr.afs`,
     `adx_us.afs` (voces EN), `data_yah.afs` en `assets/us/`.
   - Región **EU (PAL)**: `data_en.afs`, `data_fr.afs`, `data_ge.afs`,
     `data_it.afs`, `data_sp.afs`, `adx_jp.afs` (voces JP), `data_yah.afs`
     en `assets/eu/`.
   - Copia también el `.xex` del juego como `assets/default.xex` (el ejecutable
     de ambas regiones es el mismo binario).
3. Ejecuta `dbz1.exe`. Se abre el launcher: elige región (USA/EU), idioma,
   y pulsa **Play**.

> El `.xex` y los AFS NO se redistribuyen (copyright). Solo se usan en local.

## El código recompilado

El recompilador está vinculado dentro de `dbz1.exe`. Para reconstruirlo desde
el código fuente (carpeta `github/`), se ejecuta el codegen de ReXGlue sobre
tu `.xex` legal, que regenera `generated/` antes de compilar.

## Bugs conocidos

Ver la sección "Bugs conocidos" de las notas del release.

Documentación completa: `docs/` (en el repositorio).
