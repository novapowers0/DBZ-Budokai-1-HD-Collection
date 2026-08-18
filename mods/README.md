# mods/

Carpeta de **mods de usuario**. Se distribuye **vacía** (los mods reemplazan
archivos con copyright del juego, así que no se incluyen aquí).

> 🚧 **Estado: WIP (en desarrollo).** El sistema de mods es experimental y puede
> cambiar. Úsalo con copias de seguridad.

## Estructura de un mod

Cada mod vive en una subcarpeta `mods/<nombre>/` y reemplaza entradas del AFS
por overlay (sin tocar los AFS originales):

```
mods/<mod>/
└── us/
    └── data_sp.afs/
        ├── 2450/geom.bin    # modelo del slot 2450
        └── 2451/tex.bin     # textura del slot 2451
```

- El override se instala en **todos** los `data_*.afs` de personaje, de modo
  que funciona independientemente del AFS concreto que elija el juego según
  región/idioma.
- Un archivo `.disabled` dentro de la carpeta del mod lo desactiva
  (`mods/foo/.disabled`).

## Consumo de espacio

⚠️ **Los mods de modelos ocupan bastante espacio.** Cada mod es una **copia
completa** del bin del personaje (geometría + texturas) comprimida y paddeada,
replicada en **todos** los `data_*.afs` de personaje de la región:

- Un modelo + su textura: **~5–30 MB por mod** (comprimido).
- Al copiarse en varios AFS, el total se multiplica.
- Con varios mods activos, **es fácil acumular cientos de MB** en `mods/`.

Recomendación: activa solo los mods que uses y elimina los que ya no necesites
(el launcher permite gestionarlos).

## Crear / instalar un mod

Usa el **launcher** (pestaña Mods) o las herramientas de `mod center hd/`:

- `launcher_mod_pipeline.py catalog|swap|port` — pipeline de modelos.
- `swaps/swap_b1.py` — swaps B1→B1.
- `conversores/install_b3_to_b1.py` — port B3→B1.

Guía completa: `docs/tutoriales/TUTORIAL_MODS.md` y
`docs/tutoriales/FORMATO_MODS.md`.
