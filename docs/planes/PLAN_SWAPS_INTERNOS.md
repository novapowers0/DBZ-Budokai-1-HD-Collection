# PLAN DE SWAPS INTERNOS (2026-08-14) — ampliar conocimiento del formato
> Copyright (c) NovaPowers. Released under the MIT License. Firmado por NovaPowers.
>

> Propuesto por el usuario tras v19 (amalgama de triángulos + parpadeo).
> Idea: dominar los swaps internos (mismo juego) ANTES de portear entre
> juegos, para aislar qué entendemos del formato y qué no.

---

## 1. LOS 3 BINS DE REFERENCIA (descubiertos en sesión 5)

| Bin | Qué es | Tamaño | AWGs | Estado |
|---|---|---|---|---|
| `slot_2450_native.bin` | Tenshinhan nativo (XTSH) | 855584 | 23 | Funciona en juego (nativo) |
| `piccola_dec.bin` | Piccolo HD (mod que funcionó) | 635744 | 19 | **Funciona como mod** |
| `scan_gero/52_u.bin` | Gero template (20G) | 371072 | 6 | **NO era el TSH** — era el Gero |

**HALLAZGO CRÍTICO**: durante v1-v18 usamos el GERO (52_u.bin) como template,
no el Tenshinhan nativo. El Gero tiene 6 AWGs; el TSH nativo tiene 23.

> ⚠️ Corrección sesión 7: el **#ACM es la ARMATURA (esqueleto), no un
> contenedor de la malla**. La malla está en el #AWO que el runtime carga
> aparte. Los bins `XXX00.bin` de "Budokai 1 Models Converted to AMB" =
> #AMB PS2 (malla + texturas).

## 2. LOS PERSONAJES NATIVOS DEL JUEGO

- Los personajes del B1 HD viven en **contenedores #ACM/#AMB** (no #AWO
  directos). Slot 368 = GOK (#ACM 1.4MB).
- Solo el slot 2450 (Tenshinhan) es #AWO directo en el AFS.
- El bin Piccolo del mod es #AWO directo → el runtime acepta ambos.

## 3. PLAN DE TESTS (de menor a mayor dificultad)

### Test 1 — Pipeline de control (INSTALADO)
Instalar el bin nativo del TSH re-comprimido en slot 2450.
**Objetivo**: validar que la instalación (compresión/padding/overlay) es
correcta. Si el TSH se ve bien → el pipeline es correcto, el problema era
el template/conversión.

### Test 2 — Swap interno B1→B1
Instalar el bin Piccolo HD (funciona como mod) en slot 2450.
**Objetivo**: confirmar que un bin #AWO directo de otro personaje es
intercambiable en el slot. Si el Piccolo se ve bien desde el mod → el
formato #AWO directo es portable.

### Test 3 — Swap interno B1→B1 desafiante
Extraer el #AWO embebido del contenedor #ACM del Goku (slot 368) e instalarlo
en slot 2450.
**Objetivo**: entender el formato #ACM (contenedor nativo) y si su #AWO
interno es directamente utilizable.

### Test 4 — Swap interno B3→B3
Repetir en Budokai 3 HD: intercambiar dos personajes nativos del mismo juego
(además del Gero).
**Objetivo**: confirmar que el formato #AWO/#AWG es el mismo en B3 y B1
(como documenta la comunidad).

### Test 5 — Port PS2→HD (con estructura correcta)
Solo después de dominar los swaps internos, retomar el port PS2→HD:
reconstruir el bin con la estructura del PS2 (1 AWG por AMG), usando la
plantilla estructural que funcione.

## 4. APRENDIZAJE ESPERADO

Cada test aísla una variable:
- Test 1: pipeline de instalación (compresión, padding, overlay)
- Test 2: intercambiabilidad del bin #AWO directo
- Test 3: formato contenedor #ACM
- Test 4: paridad B1/B3 del formato
- Test 5: port PS2→HD real

Con esto sabremos si nuestro problema es el pipeline, el formato del bin,
o la conversión de esqueleto — y podremos construir las herramientas
correctas para portear cualquier modelo.
