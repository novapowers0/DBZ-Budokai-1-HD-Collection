# SESIÓN 10 — PORT B3 HD → B1 HD 100% FUNCIONAL (Gero, validado en runtime)
> Copyright (c) NovaPowers. Released under the MIT License. Firmado por NovaPowers.
>

> 2026-08-16, noche. **Logro**: el Gero de Budokai 3 HD renderiza perfecto en
> el slot Tenshinhan de Budokai 1 HD. Rig intacto, materiales/specular OK,
> texturas OK, reacciones a daño OK.
>
> Clave: el swap nativo B1→B1 (sesión 9) demostró que el runtime dibuja el bin
> #AWO COMPLETO tal cual (mesh group, IB, bones, UVs incluidos), sin validar
> conteos del slot. Esto convirtió el port B3→B1 en un problema de CONVERSIÓN
> DE SELLOS + MATERIALES + ALPHA, no de retopología ni re-rigging.

---

## 1. LA REVELACIÓN (cadena de descubrimientos)

1. **Swap B1→B1 nativo** (sesión 9): instalar un bin #AWO completo de otro
   personaje B1 en un slot funciona 100% (X19G con 46 bones en slot TSH de 42).
   El runtime usa la tabla de bones del PROPIO bin.
2. **Consecuencia**: el port B3→B1 NO necesita aplanar jerarquía ni reindexar
   bones — si el bin conserva su estructura B3 y sus vértices apuntan a su
   propia tabla, el runtime lo dibuja igual.
3. **Los 2 requisitos que faltaban** (además de flag/type2): materiales B1
   (escala 128, no 1.0) y AZT con alpha DXT3 a 0xFF.

---

## 2. PIPELINE VALIDADO (automatizado)

```
python install_b3_to_b1.py <awo_b3.bin> <azt_b3.bin> --mod <nombre>
```

Pasos internos (`port_b3_to_b1_v2.py` + `install_b3_to_b1.py`):

### A. Conversión del AWO B3 → B1 (`port_b3_to_b1_v2.py`)
| # | Qué | B3 | B1 |
|---|---|---|---|
| 1 | Flag `+0x0C` AWG | `0x4` | `0x2` |
| 2 | Type2 mesh part `+0x38` | `0x1B5` | `0x1BD` |
| 3 | Type2 mesh part `+0x3C` | `0x29BD` | `0x1BD` |
| 4 | Sombra | `0x1B4` | `0x190` |
| 5 | u34 `+0x34` mesh part | `1/5/7` | `0xFFFFFFFF` |

### B. Materiales B1 (crítico — sin esto → cuerpo negro/sin specular)
| Campo | B3 | B1 |
|---|---|---|
| Escala `+00` | `1.0,1.0,1.0,0.0` | `128.0×4` (specular) |
| Weights `+10` torso | `1,1,1,0` | `0.85,0.80,0.70,1.0` |
| Weights `+10` extremidades | `1,1,1,0` | `0.85,0.85,0.80,1.0` |
| Type2 (no-sombra) | `0x1BD` | `0x11BD` (shader alt con specular) |

### C. AZT con alpha DXT3 a 0xFF (crítico — sin esto → cuerpo negro)
El runtime B1 espera DXT3 con alpha opaco (verificado en el X19G nativo:
`48_u.bin` tiene bloques alpha `0xFF`). El AZT B3 del Gero usa DXT3 con alpha
variable → cuerpo negro. `fix_azt_alpha()` fuerza los 8 bytes de alpha de cada
bloque DXT3 a `0xFF` (27392 bloques en el Gero).

### D. Instalación (reutiliza `swaps/swap_b1.py`)
1. Comprimir `/N:2048` (nunca /N:32)
2. Padding al tamaño de slot (2450=290816, 2451=33504)
3. Round-trip verificado con `xbdecompress`
4. Instalar en `mods/<mod>/us/data_sp.afs/<slot>/`
5. Gestión de mods (activar este, desactivar el resto)

---

## 3. VERIFICACIÓN EN RUNTIME (Gero B3 → slot TSH)

- Mod: `test_gero_b3_to_b1_v2` (ACTIVO, `mods/`)
- Overrides en log: `data_sp.afs entry=2450` y `2451` → mod
- **Resultado en combate**: Gero B3 renderiza perfecto.
  - Rig OK: brazos, piernas, cuerpo conservados; no se rompe al jugar.
  - Materiales/specular perfectos.
  - Reacciones a daño OK (el modelo cambia como se espera).
  - Texturas OK (las 10 del AZT B3 con alpha forzado).
- **Reproducibilidad**: `port_b3_to_b1_v2.py` genera bins byte-idénticos a los
  instalados (md5 `d36aea8e...` geom, `b4e859e6...` azt).

---

## 4. FALLOS CONOCIDOS (a documentar)

1. **Mandíbula al recibir daño pero no al usar técnicas**: el rig de la boca del
   B3 (X20G_M_JAW) abre la mandíbula en la reacción de daño pero no en la
   animación de técnicas. Es el rig de boca B3, que difiere del B1.
2. **Tenshinhan es calvo → bones de pelo no responden**: el TSH no tiene pelo.
   Los bones de pelo del Gero (X20G_HAIR1/2/3) deforman geometría del brazo
   (comen medio brazo) porque el runtime no los anima. Al portar a un personaje
   con pelo, este fallo desaparecería.

---

## 5. ARTEFACTOS

| Archivo | Qué |
|---|---|
| `%TEMP%\opencode\b3_bins\gero_0_#AWO.bin` | AWO B3 del Gero (293728 B) |
| `%TEMP%\opencode\b3_bins\gero_1_#AZT.bin` | AZT B3 del Gero (440128 B, 10 tex DXT3) |
| `%TEMP%\opencode\b3_bins\gero_b1_port_v3.awo` | port validado (293728 B) |
| `%TEMP%\opencode\b3_bins\gero_1_#AZT_opaque.bin` | AZT con alpha 0xFF (440128 B) |
| `mods\test_gero_b3_to_b1_v2\` | mod instalado (ACTIVO) |

---

## 6. CÓMO PORTAR OTROS PERSONAJES B3 → B1

1. Extraer el par AWO+AZT del personaje del `data_cmn.afs` del B3 HD.
2. `python install_b3_to_b1.py <awo> <azt> --mod <nombre>`.
3. Probar en runtime.
4. Si el personaje destino tiene pelo y el origen no (o viceversa), los bones
   extra del rig pueden deformar geometría — documentar como fallo conocido.

**Inverso (B1 HD → B3 HD)**: mismo pipeline simétrico — el runtime B3 dibujaría
un bin B1 completo si se convierten los sellos (flag 0x2→0x4, type2 0x1BD→
0x29BD, materiales a los del B3) y el AZT a formato B3. Pendiente de validar.

---

## 7. DESCUBRIMIENTOS POST-VALIDACIÓN (mismo día)

### Retargeting v3/v4 (bones huerfanos - pelo)
- v3 (cambiar bone index sin transformar coords) ESTIRA la geometria porque los
  vertices estan en coords LOCALES al bone origen (el pelo del Gero se fue al suelo).
- v4 (port_b3_to_b1_v4.py): transforma coords con local_dst = inv(M_dst) * M_src * local_src usando las matrices bind world de los ejes del AWO. Mejora el pelo pero aun solapa con el brazo en anfitriones calvos.
- Conclusión: el runtime B1 anima con el esqueleto del ANFITRIÓN; los bones sin correspondencia (HAIR1/2/3, DTEETH) quedan en pose bind.
- El v2 sigue siendo la versión más estable (pelo congelado = limitación conocida).

### Set de archivos del personaje HD (movesets)
- El personaje HD no es solo #AWO+#AZT: usa #ACM (esqueleto) + #CCM (comandos) + #CFC + #CSK (ANIMACIONES/moveset) + #SPX (efectos).
- Todos los #CSK tienen la MISMA estructura (2037 animaciones, mismos IDs) → intercambiables para portar movesets.
- Detalle: docs/re/ANIMACIONES_MOVESETS_HD.md.
