# DBZ Budokai 1 HD Collection — Release ejecutable

Copyright (c) 2026 **NovaPowers**. Released under the MIT License.

Este paquete contiene el ejecutable recompilado de *Dragon Ball Z: Budokai HD
Collection* (Xbox 360) con el launcher, el sistema de mods y el pipeline de
modelos. **NO incluye los archivos del juego** (copyright): debes aportar los
de tu copia legal.

## Contenido

- `dbz1.exe` — recompilador + launcher + sistema de mods
- `rexruntime.dll` — runtime ReXGlue (D3D12 + Vulkan + FidelityFX)
- `rexgpu-xenos.dll` — plugin GPU (Xenos)
- `amd_fidelityfx_dx12.dll` — runtime FidelityFX (CAS/FSR/FSR2/FSR3, obligatorio)
- `TracyClient.dll` — profiling (requerido por el runtime)
- `RELEASE_README.md` — este archivo

## Novedades (v0.5.0)

- **Backend Vulkan opcional**: en la pestaña **Video** del launcher puedes
  elegir *Graphics backend* entre **Auto (D3D12)**, **D3D12** y **Vulkan**.
- **Upscalers FidelityFX**: *Upscaler* (Bilinear / CAS / FSR 1 / FSR 2 / FSR 3)
  con calidad ajustable (*FSR quality*). FSR 2/3 (temporal) requieren el
  backend **D3D12** en esta build; en Vulkan se usan CAS/FSR espaciales.

## Cómo instalar y jugar

1. **Aporta los archivos del juego** (no se incluyen, son de tu copia legal):
   - Crea una carpeta `assets/` junto a `dbz1.exe`.
   - Copia el `.xex` del juego como `assets/default.xex`.
   - Copia los datos de tu región:
     - **USA**: `assets/us/` → `data_us.afs`, `data_sp.afs`, `data_fr.afs`,
       `adx_us.afs`, `data_yah.afs`.
     - **EU (PAL)**: `assets/eu/` → `data_en.afs`, `data_fr.afs`,
       `data_ge.afs`, `data_it.afs`, `data_sp.afs`, `adx_jp.afs`,
       `data_yah.afs`.
2. **Ejecuta** `dbz1.exe`.
3. En el launcher elige **Región** (USA / EU PAL) y **Idioma**, y pulsa
   **Play**.

> Para extraer los archivos de tu **ISO legal** usa una herramienta tipo
> `extract-xiso` (lee el FATX de Xbox 360). Ver `baserom.md` del repositorio
> para los tamaños y checksums SHA-256 de cada archivo.

## Mods (WIP)

> 🚧 **Estado: en desarrollo (WIP).** El sistema de mods es experimental y puede
> cambiar. Úsalo con copias de seguridad.

Los mods se gestionan desde la pestaña **Mods** del launcher. **No modifican**
los archivos del juego: aplican un overlay sobre entradas concretas del AFS.
Cada mod ocupa una **copia completa** del modelo (geometría + texturas)
replicada en todos los `data_*.afs` de personaje, así que **puede consumir
bastante espacio en disco** (~5–30 MB por mod, y con varios mods es fácil
acumular cientos de MB). Activa solo los que uses y elimina los que ya no
necesites. Detalle: `docs/tutoriales/TUTORIAL_MODS.md`.

## Bugs conocidos (blackouts)

Pantalla en negro (blackout) en determinadas secuencias renderizadas
(entrada a combate ~4.5s, modo historia, combates con presentación inicial, y
ataques definitivos). No bloquean la jugabilidad — solo son una pausa en negro
y el juego continúa correctamente después. Detalle:
`docs/re/INVESTIGACION_BLACKOUT_DUELO.md`.

## Legal

Proyecto no oficial, sin ánimo de lucro, de investigación y preservación. No
afiliado ni avalado por Bandai Namco, Shueisha, Toei Animation ni ningún
titular de los derechos de Dragon Ball. No se distribuye ningún `.xex`, AFS ni
dato del juego. Los archivos del juego son de tu copia legal.

Repositorio: https://github.com/novapowers0/DBZ-Budokai-1-HD-Collection
