# SESIÓN 8 — CRASH RUNTIME DEL PORT GERO B3→B1 (16/08/2026)
> Copyright (c) NovaPowers. Released under the MIT License. Firmado por NovaPowers.
>

> Hechos básicos del runtime + resultado de probar `test_gero_b3_to_b1`
> (port Gero B3→B1 reconstruido). **El port carga (override OK) pero CRASHEA
> el runtime al renderizar el modelo en combate.**
>
> ⚠️ **RESOLUCIÓN (16/08, tarde)**: la causa del crash era el **mismatch de
> textura** (tex.bin 2451 = AZT del Gero B3 mientras la geometría esperaba su
> propio AZT). Con el par nativo completo del mismo personaje (`49_u.bin`
> AWO + `48_u.bin` AZT) el swap **funciona 100%** en combate. Detalle y
> metodología: `docs/tutoriales/MODEL_SWAPS_METODOLOGIA.md`.

---

## 1. CÓMO LANZAR Y DÓNDE ESTÁN LAS COSAS (no volver a preguntar)

| Qué | Ruta |
|---|---|
| **Ejecutable (build release)** | `out\build\win-amd64-release\dbz1.exe` (16 MB, 15/08) |
| Exe viejo de la raíz (NO usar) | `dbz1.exe` (21 MB, 22/02, build anterior) |
| Logs | `out\build\win-amd64-release\logs\dbz1_NNN.log` (el `_NNN` sube cada lanzamiento; hoy `dbz1_009.log`) |
| Assets (AFS) | `assets\<region>\*.afs` — el runtime mapea `D:\us\...` a esta carpeta |
| Mods | `mods\<mod>\us\data_sp.afs\<entry>\<archivo>` |
| Crash codes | Visor de eventos Windows → Logs de aplicación → "Application Error" → dbz1.exe |

**Datos duros de `dbz1_009.log`:**
- La región de assets para `data_sp.afs` se resuelve a `assets\eu\data_sp.afs`
  (y `adx_us.afs` → `assets\us\`). El override de mods NO depende de la región:
  se hace match por **nombre de AFS + índice de entrada**, con path en `mods\<mod>\us\`.
- El runtime registra cada override: línea
  `AFS entry override: data_sp.afs entry=2450 offset=... -> mods\test_gero_b3_to_b1\us\data_sp.afs\2450\geo`.
- El log corta sin error (crash silencioso); el crash real está en el Visor de eventos.

## 2. RESULTADO DE LA PRUEBA (16/08 03:36-03:37)

1. **Mod `test_gero_b3_to_b1` ACTIVO** (`mods/test_gero_b3_to_b1`, sin `.disabled`).
   Solo 2450/2451 overridden. Todos los demás mods desactivados.
2. **Override VERIFICADO en el log**: entrada 2450 (`geom.bin`) y 2451 (`tex.bin`)
   se cargaron desde el mod. El sistema de mods funciona.
3. **CRASH al entrar en combate** (cuando aparece el modelo):
   `Application Error: dbz1.exe, 0xc0000005, offset 0x8a9b85, 16/08 03:37:20`.

### Interpretación
**RESUELTO (16/08 tarde)**: el crash NO era por el mesh group ni por la
conversión B3→B1. Se demostró haciendo A/B con bins B1 nativos del Gero:
`52_u.bin` (X20G) y `49_u.bin` (X19G) instalados en slot 2450 con el
tex.bin 2451 = AZT del Gero B3 → **ambos crashean igual**. El runtime B1
espera que la textura (2451) corresponda al modelo (2450). El mismatch
geom/tex es lo que produce el 0xC0000005 al leer las texturas en combate.

**Confirmación final**: instalado el par nativo completo del Android 19
(`49_u.bin` X19G en 2450 + `48_u.bin` AZT en 2451) el modelo **renderiza
perfecto en combate** → los model swaps B1→B1 son 100% funcionales.

**Corrección de identidad**: `X19G` = **Android 19**, no Dr. Gero. El
Dr. Gero es `X20G`/`20G` = bins 52/53, no jugable (historia).

La teoría previa del mesh group jerárquico B3 vs plano B1 quedó descartada:
el crash ocurría también con bins B1 nativos sin convertir.

## 3. PRÓXIMO PASO (estado actual)

1. ✅ **Swap B1→B1 validado**: par nativo completo (geom+tex del mismo
   personaje) → renderiza perfecto. Metodología:
   `docs/tutoriales/MODEL_SWAPS_METODOLOGIA.md`.
2. El objetivo original (Dr. Gero) usa el par **52+53** (`X20G`, no jugable).
   El mod actual tiene el Android 19 (`49+48`, `X19G`).
3. El port B3→B1 (personaje de otro juego) sigue siendo un caso aparte; la
   causa de su crash se confirmó como tex mismatch, no mesh group.

## 4. LECCIONES

1. Verificar un port NO es solo chequear bytes: hay que probarlo en runtime.
2. El crash silencioso se busca en el Visor de eventos, no en el log del juego.
3. El override de mods funciona por nombre de AFS + entry, sin importar región.
4. **El geom y el tex deben ser del MISMO personaje** — un bin #AWO espera su
   #AZT correspondiente; mezclarlos → 0xC0000005 en combate.
5. `X19G` ≠ Dr. Gero: identificar SIEMPRE por el label `XXX_BODY`.