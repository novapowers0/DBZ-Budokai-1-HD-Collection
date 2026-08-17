# Estructura del proyecto — referencia rápida
> Copyright (c) NovaPowers. Released under the MIT License. Firmado por NovaPowers.
>

> Guía para no perderse con las carpetas y los dos `dbz1.exe`.

---

## 1. ¿Qué es este proyecto?

Es un trabajo de **recompilación** con la [ReXGlue SDK](https://github.com/rexglue/rexglue-sdk).
El juego original corre en la Xbox 360 (GPU **Xenos**). La SDK convierte el ejecutable
original en un programa de PC que emula ese GPU usando **Direct3D 12**.

Por eso existen DOS `dbz1.exe` distintos.

---

## 2. Los dos `dbz1.exe`

| | Raíz `...\DBZ Budokai HD Collection\dbz1.exe` | `...\build\Release\dbz1.exe` |
|---|---|---|
| **Qué es** | Ejecutable **original** de Xbox 360 | Ejecutable **recompilado** para PC |
| **Tamaño / fecha** | 20,15 MB — 22/02/2026 | 16,9 MB — 10/08 21:24 |
| **Función** | Pieza de partida / referencia | Producto final que se ejecuta |
| **Se modifica** | **Nunca** | Se regenera con cada compilación |

> **Regla práctica:** el que sirve para jugar es siempre `build\Release\dbz1.exe`.
> El de la raíz no se toca jamás.

---

## 3. Rol de cada carpeta

```
DBZ Budokai HD Collection/
├── dbz1.exe              # Ejecutable ORIGINAL (no tocar)
├── dbz1_config.toml      # Config del runtime
├── dbz1_manifest.toml    # Manifiesto
├── dbz1_shader_dump.txt  # Dump de shaders
├── assets/               # Datos del juego — se extraen aquí
│   ├── default.xex       #   XEX del juego (se carga como game:\default.xex) — NO MOVER
│   ├── xex_eur/          #   Copia del XEX para la región EUR (idéntico al US)
│   ├── us/               #   Assets USA (data_us.afs, adx_us.afs, ...)
│   ├── eu/               #   Assets EUR/PAL (data_en/fr/sp/ge/it.afs, adx_jp.afs, ...)
│   └── 4E4D0856/         #   Save data
├── generated/            # Código generado por re2_codegen
├── src/                  # Código del juego recompilado
├── rexglue-sdk/          # Fuentes de la SDK (lo que modificamos)
│   └── out/win-amd64/Release/   # Otra salida de compilación (libs/dlls)
├── build/                # CARPETA DE SALIDA de CMake
│   ├── Release/          #   → AQUÍ está el dbz1.exe recompilado que se ejecuta
│   └── ...obj/.pch/      #   → Decenas de miles de archivos intermedios (NO mirar)
└── docs/                 # Documentación
    ├── ESTRUCTURA.md                 # Este archivo
    ├── AGENTS.md                     # ⚠️ FUENTE PRINCIPAL (RE definitiva, formato HD, mods, lecciones)
    ├── planes/                       # HOJA_DE_RUTA, PLAN_PORTS_FUNCIONALES, PLAN_PORT_REAL_DISENO,
    │                                 #   PLAN_RELAYOUT_B3_B1, PLAN_AFS_OUT_RE_COMPARATIVA, PLAN_SWAPS_INTERNOS,
    │                                 #   HOJA_DE_RUTA_SWAPS
    ├── re/                           # INVESTIGACION_FORMATO_B1_HD, SESION7_MESH_GROUP_COMPLETO,
    │                                 #   SESION6_PORT_B2_B1_HD, SESION7B_IMAGENES_B3IW, ESTUDIO_TRANSVERSAL_GOKU,
    │                                 #   ESTRUCTURA_AWG_B1, ESTUDIO_PORT_MODELOS, HALLAZGOS_DISCORD_SESION_B1,
    │                                 #   INVESTIGACION_BLACKOUT_DUELO
    ├── tutoriales/                   # FORMATO_MODS, TUTORIALES_MODDING, INVESTIGACION_MODDING_BUDOKAI,
    │                                 #   CONVERSOR_B3IW_A_B1_COMUNIDAD
    ├── estado/                       # ESTADO_PORT_GOKU_SS2 (histórico)
    ├── referencias/                  # PERSONAJES_BINS, GUIA_ECOSISTEMA_FASE1
    └── logs/                         # Logs conservados como evidencia
```

---

## 4. Cómo se compila

```powershell
cmake --build build --config Release
```

La salida real del linker se escribe en `rexglue-sdk\out\win-amd64\Release` y se
distribuye a `build\Release`. Tras compilar, **verificar que `build\Release\dbz1.exe`
y `build\Release\rexgpu-xenos.dll` tienen fecha actualizada**.

Advertencias de `fopen`/parámetros sin usar son inocuas.

---

## 5. Qué NO mirar

- `build\` completo (solo `build\Release` contiene el binario útil).
- Los `.obj` / `.pch` / `.lib` intermedios.
- `shaderdump/`, `user_data/`, `logs/` dentro de `build\Release` (salidas del runtime).
