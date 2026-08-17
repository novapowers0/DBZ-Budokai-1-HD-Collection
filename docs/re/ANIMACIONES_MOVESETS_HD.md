# FORMATO DE ANIMACIONES Y MOVESETS HD (#CSK/#CCM/#SPX)
> Copyright (c) NovaPowers. Released under the MIT License. Firmado por NovaPowers.
>

> RE 16/08/2026. Descubierto al investigar cómo portar movesets entre juegos.
> El modelo del personaje en HD NO es solo #AWO+#AZT: el personaje completo
> usa un set de 7+ archivos, análogos a los de PS2 (AMO/AMT/AMM/BSK/SPX).

---

## 1. SET DE ARCHIVOS DEL PERSONAJE (HD, en data_sp.afs)

Cada personaje jugable tiene un bloque de entradas AFS consecutivas. Ejemplos:

**Tenshinhan (TSH):**
| Entry | Formato | Tamaño | Contenido |
|---|---|---|---|
| 2445 | `#ACM` | 836KB | esqueleto/armatura (labels de huesos) |
| 2446 | `#CCM` | 5KB | comandos/moveset (técnicas) |
| 2447 | `#CFC` | 160B | flags de cara/expresiones? |
| 2448 | `#CSK` | 140KB | **tabla de ANIMACIONES** (moveset) |
| 2449 | `#SPX` | 39KB | efectos especiales |
| 2450 | `#AWO` | 290KB | modelo (malla + esqueleto bind) |
| 2451 | `#AZT` | 33KB | texturas (DXT3) |
| 2456 | `#ACM` | 3.8KB | ACM secundario |

**Android 19 (X19G, bins 43-51):**
| Entry | Formato | Contenido |
|---|---|---|
| 43 | `#CSK` | animaciones (135KB) |
| 44 | `#SPX` | efectos (28KB) |
| 45/46 | `#AWO`+`#AZT` | variante traje 1 |
| 47/48 | `#AWO`+`#AZT` | variante traje 2 |
| 49/50 | `#AWO`+`#AZT` | variante traje 3 |
| 51 | `#ACM` | esqueleto |

> El TSH tiene #CCM y #CFC; el X19G no (o están en otras entradas). El set
> mínimo común es: `#ACM + #CSK + #SPX + #AWO + #AZT`.

---

## 2. #CSK = TABLA DE ANIMACIONES (MOVESET) — CLAVE

Header:
```
+0x00 '#CSK'
+0x0C = 0x00000002
+0x10 = n_animaciones  (2037 en TSH y X19G — SAME para todos los personajes)
+0x14 = 0x20
+0x18 = 0xD4
+0x1C = offset tabla de datos (TSH=0x1BBBC, X19G=0x1A60C)
```

Tabla de animaciones (entradas de 48B c/u):
```
+00 ID de animación (0x00000001, 0x00010001, 0x00020001...)
+04..+20 zeros
+24..+2C FFFFFFFF (máscara)
+30 0
+34 contador/tamaño (3,4,5...)
+38 offset de datos (apunta a keyframes)
```

Zona de datos (ej. @0x1BBBC en TSH): keyframes por hueso (bytes
`0x44 0x00 0xC8 ...` = transformaciones por hueso).

**CLAVE para portar movesets**: todos los #CSK tienen la MISMA estructura y
los MISMOS IDs de animación (2037). Solo difieren los DATOS (keyframes de
cada hueso). → **Sustituir el #CSK del personaje anfitrión por el del
personaje B3 portado transfiere las animaciones/moveset.**

---

## 3. #CCM = COMANDOS / MOVESET

`#CCM` (TSH 2446, 5KB): header `#CCM + 0x4A + 0x10 + ... 0x11 (17?)`.
Pequeño — probablemente tabla de comandos de entrada (qué botones ejecutan
qué animación). Sustituirlo junto al #CSK transferiría el moveset completo.

## 4. #SPX = EFECTOS ESPECIALES

`#SPX` (TSH 2449, 39KB; X19G 44, 28KB): efectos de técnicas (energía,
destellos). En PS2 el #SPX también existe (entry 479).

## 5. #CFC (solo TSH)

160B, campos de flags (0x6B, 0x6C, valores 0202/0A02...). Posiblemente
expresiones faciales o flags de animación de cara.

---

## 6. ANÁLOGOS EN PS2 (Budokai 1, data_us.afs)

Personaje = ~12 archivos (tabla de nombres con 48B/entrada: 16B header + 32B
nombre):
- `19G00.AMO / 01 / 02` = animaciones (3 variantes, 1.5MB c/u)
- `19G00.AMT / 01 / 02` = texturas (3 variantes)
- `19G.AMM` = esqueleto (labels de huesos, 2716B)
- `19G_PTS.AMM` = puntos/partes del esqueleto
- `19G.BCM` / `19G.BFC` / `19G.BSK` / `19G.SPX` = movimientos/cara/esqueleto/efectos
- `DBS_19G.BD/HD`, `DECK_19G.AMM`, `MON_19G1/2.AMT`, `SP_19G.AMB` = extras

Correspondencia aproximada HD↔PS2:
```
#CSK (animaciones)  ~ AMO (animaciones) + BSK (esqueleto)
#ACM (esqueleto)    ~ AMM (esqueleto)
#AWO (modelo)       ~ AMG (mesh) + AMO
#AZT (texturas)     ~ AMT (texturas)
#SPX (efectos)      ~ SPX (efectos)
#CCM (comandos)     ~ BCM? (moveset)
```

---

## 7. IMPLICACIONES PARA MODS

1. **Portar moveset B3→B1**: instalar el #CSK (y #CCM) del personaje B3 en
   las entradas del anfitrión (2448/2446 para TSH) junto al #AWO+#AZT ya
   portado. Verificar en runtime si las técnicas del B3 funcionan.
2. **Texturas editables**: los #AMT PS2 (BMP) se podrían usar para generar
   #AZT HD fácilmente (texturas del personaje en abierto).
3. **El set completo del personaje** (7+ archivos) es lo que hay que
   sustituir para un port completo (modelo + animaciones + efectos).

---

## 8. EXPERIMENTOS DE MOVESET (17/08, runtime — datos clave)

Mod `test_gero_moveset_19`: port Gero B3→B1 (2450/2451) + #CSK del Android 19
(2448). El **Gero B3 es jugable** (X20G en data_cmn del B3: AMB 91/92/94/95 +
ACM 3740), pero sus animaciones NO están en formato #CSK B1 (el B3 usa
#BPC/#SPX/#MTC, formato distinto). **Su equivalente de animación en B1 es el
Android 19 (X19G)** — comparte el rig de androide.

### Resultados en runtime (Gero portado en slot TSH)

| Config | Resultado |
|---|---|
| Solo modelo (v2) | ✅ renderiza perfecto (rig, materiales, daño) |
| + #CSK X19G (2448) | ✅ **el moveset CAMBIA** (hallazgo) pero poses imperfectas: P→P→P→P pega hacia abajo, K→K→K→K desde el suelo, agarrón roto. Técnicas bug. |
| + #ACM X19G (2445) | ❌ **T-Pose con medio cuerpo bajo el suelo**. Solo X (defensa) funciona: puños + cierra la boca. |

### Datos clave aprendidos

1. **El #CSK es sustituible por entrada AFS** → cambia el moveset del
   personaje. Es la vía para portar movesets (hallazgo validado en runtime).
2. **El #ACM NO es sustituible directamente**: instalar el #ACM de otro
   personaje (X19G, 4KB vs TSH 1.5MB) deja el modelo en T-Pose bajo el suelo.
   El #ACM define la pose de referencia (bind pose) del esqueleto y debe ser
   consistente con el #AWO; un #ACM mínimo de otro personaje no es compatible.
3. **El rig del AWO del Gero B3 es el genérico `G_*`** (G_CHEST, G_HEAD,
   G_LARM1...): **coincide con 27 labels del #ACM del X19G** y **0 con el
   #ACM del TSH**. Por eso el Gero en slot TSH nunca se anima perfecto (bones
   sin coincidencia quedan en bind/T-Pose).
4. **La defensa (X) funciona parcialmente** aunque el resto esté roto: los
   bones de puños (G_L00_LHAND/RHAND) y boca (G_M_JAW) coinciden entre el
   AWO del Gero y el #ACM del X19G → confirma que el runtime anima por
   **coincidencia de labels** entre AWO y esqueleto.
5. **El runtime B1 HD anima con el esqueleto del slot (#ACM)**; los bones del
   AWO sin label coincidente quedan en pose bind (congelados/T-Pose).

### Conclusión para el port de moveset

El moveset correcto de un personaje portado requiere que esqueleto (#ACM) y
animaciones (#CSK) sean del MISMO rig. Para el Gero (rig G_*):
- El #ACM del X19G (G_*) coincide en labels pero su bind pose no encaja con
  el AWO del Gero B3 (T-Pose).
- Falta investigar: ¿se puede ajustar el #ACM del X19G (bind pose) para que
  coincida con el AWO del Gero? ¿O generar un #ACM desde el propio AWO del
  Gero (su esqueleto bind, 46 bones)?

### ✅ CONCLUSIÓN FINAL (17/08): MOVESET NO VIABLE sin RE completa del #ACM

Tras probar todo lo siguiente, **el port de movesets queda descartado por
ahora** (se mantienen los ports de modelos, 100% funcionales):

| Config | Resultado |
|---|---|
| Solo modelo (v2) | ✅ **100% funcional** (port de modelos = la vía viable) |
| + #CSK X19G (2448) | ⚠️ moveset cambia (hallazgo) pero poses rotas |
| + #ACM X19G (2445) | ❌ T-Pose |
| Modelo Gero en slot A19 (45-50) | ❌ **crash 0xC0000005** (el slot X19G no acepta el AWO/AZT del Gero) |
| **#ACM híbrido** (estructura TSH 163 bloques + 46 labels X20G_* del Gero + conteo 46) | ❌ **crash 0xC0000005** |

### Por qué el #ACM híbrido crasheó (RE del #ACM HD)

El #ACM del TSH (1.5MB, 42 bones) contiene:
1. Header: `#ACM` + 0x20 + 0 + 2 + **n_bloques** (TSH=163) + 0x20 + **n_bones**
   (42) + offset tabla de labels.
2. **163 bloques** de 16B `[9, 0, cnt, offset]` → tabla de poses/expresiones
   (el TSH, humano, tiene 163 expresiones; el X19G, androide, solo 6 → por eso
   su #ACM es 4KB y da T-Pose).
3. Datos de poses en los offsets (los cnts suman 9002 poses).
4. **Tabla de labels de 32B** al final (`XTSH_BODY, TSH_WAIST, TSH_STMC...`
   = 42 labels) → la jerarquía de huesos.

El AWO del Gero B3 tiene 46 labels `X20G_*` (X20G_BODY, 20G_WAIST,
20G_RLEGROT... X20G_HAIR1/2/3, X20G_SHD3).

**Crash**: cambiar solo la tabla de labels + `+0x18` (42→46) SIN reconstruir
los datos de poses internos (indexados para 42 bones) → el runtime lee
poses/fuera de rango → 0xC0000005. Los datos de poses del #ACM dependen del
número de bones; generar un #ACM para el Gero exigiría reconstruir las 9002
poses con la jerarquía de 46 bones (RE completa del formato).

---

## 10. GAMECUBE (Budokai 1/2 GC) — formato NO reutilizable

El usuario aportó los ISOs de GC (`ps2_games\DragonBall Z - Budokai [NGC].iso`
y `... Budokai 2 [USA].iso`, extraídos de .rvz de Dolphin) porque la doc de
`AMA10.java` decía que el B1 HD usa el formato GC (BigEndian).

**Verificado (17/08)**: el formato de los `.acm` GC **NO es el #ACM HD**:
- Los `.acm` del GC (p.ej. `G_PTS.acm` 263KB, `BSTEN01.acm` 99KB) **no tienen
  magic `#ACM`** — son datos crudos de poses/animación (floats BigEndian sin
  estructura de labels de 32B).
- La estructura GC usa `.acm` (esqueleto), `.act` (animaciones), `.aco`
  (modelos), `.spx` (efectos) — distinta a los bins HD (#ACM/#CSK/#AWO/#AZT).
- La doc de `AMA10.java` (formato #AMA = header 0x10 + bloques de 0x40) NO
  coincide con el #ACM HD real (header `#ACM` + 163 bloques de 16B + labels).

**Conclusión**: los ISOs GC no son útiles para generar #ACM HD. Recurso
documentado por si el parser `budokai_updated.ms`/`Model-Rig_Extractor.py`
llegara a necesitar el formato GC de referencia.

---

## 11. PENDIENTE (futuros mods)

- RE completa del #ACM HD (las 9002 poses + jerarquía) para poder generar uno
  para cualquier personaje portado.
- RE del #CSK (formato de keyframes) y #CCM (comandos/técnicas).
- Los **ports de modelos B3→B1** (v2 + install_b3_to_b1.py) son la vía
  viable; el moveset queda como investigación futura.
- Investigar si el runtime puede usar el esqueleto bind del propio AWO en vez
  del #ACM del slot (eliminaría la dependencia del #ACM).
- Verificar si el runtime HD usa #CSK del personaje o del slot.
