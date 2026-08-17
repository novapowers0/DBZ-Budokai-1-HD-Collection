# SESIÓN 9 — MODEL SWAPS B1→B1 100% FUNCIONALES (16/08/2026, tarde)
> Copyright (c) NovaPowers. Released under the MIT License. Firmado por NovaPowers.
>

> Resolución del crash 0xC0000005 del port Gero B3→B1: la causa era un
> **mismatch de textura**, no el mesh group. Con el par nativo completo
> (geom #AWO + tex #AZT del MISMO personaje) el swap renderiza perfecto.
> `X19G` = Android 19 (no Dr. Gero).

---

## 1. SECUENCIA DE LA INVESTIGACIÓN

### 1.1 Extracción del TSH nativo y comparación de MP headers
- Extraído el #AWO nativo de la entry 2450 del `assets\eu\data_sp.afs`
  (comprimida LZX, descomprimida con `xbdecompress.exe` → `tsh_2450_native.awo`,
  855584 B, 42 bones, 23 AWGs, AWG0 10 hdr/4272 verts).
- Comparados los mesh part headers (0x50B) entre TSH nativo (B1), Gero B3 y
  Gero B1 nativo:

| Campo | B3 | B1 |
|---|---|---|
| `grp` (+0x30) | índice de bone (0,2,3,4,6,8,9) | índice de grupo secuencial (0-3, 0xFFFFFFFF=sombra) |
| `t38` (+0x38) | 0x1B5 / 0x1B4 | 0x1BD / 0x11BD / 0x190 / 0x199 |
| `unk34` (+0x34) | 1 / 5 / 7 / 0xFFFFFFFF | siempre 0xFFFFFFFF |
| escala | 1.0 | 128.0 |
| weights | 1.0 | [0.85, 0.8, 0.7, 1.0] |

### 1.2 Fix del port (aplanado) → SIGUE CRASHEANDO
- Modificado `port_b3_to_b1.py`: convierte `t38` (0x1B5→0x1BD, 0x1B4→0x190)
  y `t3C`, aplana `grp` (bone→grupo secuencial 0-5, sombras→0xFFFFFFFF),
  `u34`→0xFFFFFFFF.
- Rebuild `recreate_port_b3b1_flatten.awo` (293728 B), comprimido /N:2048
  (81110 B), padded 290816, instalado en slot 2450.
- **Resultado: CRASHEA igual** en `dbz1.exe+0x8a9b85` → el aplanado no era
  la causa.

### 1.3 Desensamblado del crash (capstone)
- Instrucción del crash: `mov ecx, dword ptr [rdx + rcx]` en VA `0x1408a9b85`:
  lectura BE u32 en `rsi + (campo + 0x1a4)`, con guard
  `cmp eax,0xe0000000; setae dl; shl edx,0xc`.
- Función `0x1408a9900` sin callers directos; 1 puntero en `.data` 0x140F9C0B8.
- Es el parser del modelo leyendo el bin.

### 1.4 Pruebas A/B con bins nativos → descarte del mesh group
| geom (2450) | tex (2451) | Resultado |
|---|---|---|
| Gero B3 port (flatten) | AZT Gero B3 | CRASH 0x8a9b85 |
| `52_u.bin` (X20G nativo B1) | AZT Gero B3 | CRASH 0x8a9b85 |
| `49_u.bin` (X19G nativo B1) | AZT Gero B3 | CRASH 0x8a9b85 |
| **`49_u.bin` (X19G nativo)** | **`48_u.bin` (AZT X19G)** | **✅ FUNCIONA** |

Conclusión: bins B1 nativos del Gero también crasheaban con el AZT del B3 →
el problema NO era la conversión B3→B1 ni el mesh group. El runtime exige
que geom (2450) y tex (2451) sean del **mismo personaje**.

### 1.5 Escaneo de bins del Gero B1 (`scan_gero`)
| Bin | Contenido | Label raíz |
|---|---|---|
| 48_u.bin | #AZT (4 tex) | — (texturas X19G) |
| 49_u.bin | #AWO (46 bones, 15 AWGs, 4601 verts, 561024 B) | `X19G_BODY` |
| 50_u.bin | #AZT (4 tex) | — |
| 51_u.bin | #ACM (esqueleto) | — |
| 52_u.bin | #AWO (51 bones, 6 AWGs, 4872 verts, 371072 B) | `X20G_BODY` |
| 53_u.bin | #AZT (4 tex) | — |

**Identidad corregida**: `X19G` = **Android 19** (jugable). El Dr. Gero es
`X20G`/`20G` = bins 52/53 (no jugable, personaje de historia).

---

## 2. METODOLOGÍA VALIDADA

Ver `docs/tutoriales/MODEL_SWAPS_METODOLOGIA.md` — el swap completo:
1. Identificar personaje por label `XXX_BODY`.
2. Extraer par: #AWO (geom) + #AZT (tex) del MISMO personaje.
3. Comprimir `/N:2048`, pad a tamaño del slot (2450=290816, 2451=33504).
4. Instalar en `mods/<mod>/us/data_sp.afs/<slot>/`.
5. Verificar override en log y probar en combate.

---

## 3. ESTADO FINAL (16/08)

- Mod `test_a19_on_tsh` ACTIVO = swap Android 19 (X19G) en slots TSH
  2450/2451 (geom `49_u.bin` + tex `48_u.bin`), **100% funcional**.
  (Antes: `test_gero_b3_to_b1`, nombre engañoso — era el mismo swap.)
- Antes de esta sesión el mod crasheaba (tex = AZT del Gero B3).
- Pendiente: si se quiere el objetivo original (Dr. Gero), usar el par
  `52+53` (`X20G`, no jugable).

## 4. LECCIONES

1. **El par geom+tex debe ser del MISMO personaje** — regla #1 del swap.
2. Identificar SIEMPRE por el label `XXX_BODY`, nunca por suposición.
   `X19G` = Android 19; `X20G`/`20G` = Dr. Gero.
3. Las teorías previas (mesh group jerárquico B3, conteos fijos del slot)
   quedaron descartadas por A/B con bins nativos.
4. El override de mods por nombre AFS + entry funciona sin depender de región.