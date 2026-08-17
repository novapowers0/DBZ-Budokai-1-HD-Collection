# MAPEO DE PERSONAJES A BINS — DBZ BUDOKAI HD COLLECTION (B1)

> Copyright (c) NovaPowers. Released under the MIT License. Firmado por NovaPowers.
>
> Documento vivo: qué personaje vive en qué bins de los AFS del juego.
> Útil para model swaps (reemplazar bins de un personaje por otro).
> Se amplía conforme se identifican más personajes.
> Actualizado: 17/08/2026.

---

## 0. CATÁLOGO MAESTRO (fuente única para el launcher)

> ⭐ El **catálogo maestro** vive en `mod center hd/characters_db.py` con todos
> los códigos de personaje de B1 HD, B3 HD y B1 PS2 (nombre, variante,
> jugable, nota). Se regenera con:
> ```
> python "mod center hd\launcher_mod_pipeline.py" catalog
> ```
> → genera `mod center hd/cache/characters.cat` (109 modelos B1 + 183 B3),
> con formato: `juego|label|nombre|variante|jugable|nota|main|geom|tex|acm|csk|verts|awgs`.

### 0.1 Jugables vs no-jugables (B1 HD)
| Código | Personaje | Jugable |
|---|---|---|
| GOK, VGT, GHN, KLL, PIC, TSH, TRX, YMC, CHZ | Guerreros Z | ✅ |
| FRZ, CLD, RAD, RCM, SBM, NAP, GNY, ZBN, 16G-19G, GSM, STN | Enemigos/aliados jugables | ✅ |
| **20G / 20G_FACE** | **Dr. Gero (cuerpo / solo cara)** | ❌ historia |
| DND, BLM, YJR, WOO, MPP, KAM, POO, KIO, GOD, KRN | Dende, Bulma, Yajirobe, Oolong, Mr. Popo, **Roshi**, Popo, Kaio, Kami, Korin | ❌ |
| JES, GRD, BAT, DDR, NER, KWI | Jeice, Guldo, Burter, Dodoria, Nail, Cui | ❌ (Fuerzas) |

### 0.2 Ejemplos clave de variantes (B3 HD)
| Bin B3 | Personaje | Variante |
|---|---|---|
| 264-287 | Goku | Normal, Kaiohken, SSJ, SSJ2, SSJ3, SSJ4, trajes rotos, angelic |
| 181-193 | Freeza | Formas 1-4, 100%, cibernético, con nave |
| 416-429 | Vegeta / Majin Vegeta | Sin armadura, SSJ4, armaduras saga |
| 405-406 | **Uub** | Normal / alt |
| 377-378 | **Mr. Satan (Hércules)** | Normal / alt |
| 91-92 | **Dr. Gero** | Normal / alt |

### 0.3 Modelos B1 PS2 (personajes no-jugables swapeables)
Los 230 bins `XXX00.bin` de `Budokai 1 Models Converted to AMB` incluyen
muchos modelos no-jugables del B1 (Dende, Roshi, Bulma, Popo, Yajirobe...).
Catálogo en `characters_db.PS2`.

---

## 1. CÓDIGOS DE PERSONAJE (prefijos de labels de hueso)

Los labels de hueso en los #AWO/#ACM (ej. `20G_BODY`, `GOK_BODY`) identifican
al personaje. Códigos identificados por escaneo del data_us.afs (14/08):

### 1.1 Personajes jugables / principales
| Código | Personaje | Bins (rig #ACM → #AWO trajes) |
|---|---|---|
| GOK | Goku | 368(#ACM) → 380,381,536,984... |
| VGT | Vegeta | 2486(#ACM) → 2491-2519 (16 AWO) |
| GHN | Gohan | 378,379,531-533... |
| KLL | Krillin | 382,537,538... |
| PIC | Piccolo | 1761(#ACM) → 1768,1770...; 383,384 |
| TSH | Tenshinhan | 2445(#ACM) → 2450,2452,2454 |
| TRX | Trunks | 2415(#ACM) → 2420-2442 (12 AWO); 944,945 |
| YMC | Yamcha | 2528(#ACM) → 2533-2539 |
| TJR | Tenshinhan joven? | 358(#ACM) → 363,365; 1097,1099 |
| THL | Thales?/Gohan adulto? | 326(#ACM) → 331-347 (9 AWO) |
| CHZ | Chaozu | 350,352,354 |
| FRZ | Frieza | 1109(#ACM) → 1114-1128 (8 AWO); 377 |
| CLD | Cell | 356 |
| RAD | Raditz | 1997(#ACM) → 2002-2006; 385 |
| RCM | Recoome | 2009(#ACM) → 2014-2018; 386 |
| SBM | Saibaman | 2034(#ACM) → 2039 |
| NAP | Nappa | (en contenedores 960-968) |
| GNY | Ginyu | (en contenedores 1004-1010) |
| ZBN | **Zarbon** | 2554(#ACM) → 2559-2569 (6 AWO) — confirmado (ID SLXS 19=Zarbon) |
| DDR | ? | 475(#ACM) → 480,482 |
| DND | ? | 513 |
| THL | ¿Thales? | 326(#ACM) → 331-347 (9 AWO) |
| TJR | Tenshinhan joven? | 358(#ACM) → 363,365 |

### 1.2 Androides
| Código | Personaje | Bins |
|---|---|---|
| 16G | Android 16 | 0(#ACM) → 5,7,9,13,15 |
| 17G | Android 17 | 18(#ACM) → 23,25 |
| 18G | Android 18 | 28(#ACM) → 33,35,37; 375 |
| 19G | Android 19 | 40(#ACM) → 45,47,49 |
| 20G | **Dr. Gero** | 52(#AWO) + 53(#AZT) — **no jugable** (historia) |

> ⚠️ **Identidad verificada por labels (16/08)**: el label de hueso raíz del
> bin 49 es `X19G_BODY` = **Android 19**, NO Dr. Gero. El 49 forma parte del
> bloque del Android 19 (45/47/49) junto con su #AZT 48. El Dr. Gero es
> `X20G_BODY`/`20G` = bin 52 (#AWO) + 53 (#AZT), personaje de historia no
> jugable.

### 1.3 Otros / no-jugables
| Código | Bins | Nota |
|---|---|---|
| STN | 2358(#ACM) → 2363-2367 | ? |
| ZKA-ZKF | 2542-2552 | ? (¿Zenkai/saiyans?) |
| WOO | 2524 | ? |
| YJR | 2526 | ? |
| BAT | 79 | ? |
| BBR | 125,127 | ? |
| BLM | 237-251 (8 AWO), 526 | ? |
| SEI | 162 (#ZDD) | ? |
| P00/P01/P02/P03 | 253,527,1953... | ? (¿prop?) |
| S00/S01/S07 | 57,2374 | ? |
| KWI/KIN/KRN/KSN | (rango medio) | ? |
| GRD/GRY/GSM/HEM/HIP/JES | (en contenedores) | ? |
| T01/T05/G00/I00/J00/J01 | (rango medio) | ? |
| 707/905 | (¿IDs de audio?) | ? |

### 1.4 Otros juegos (B3 HD)
| Código | Personaje | B3 bin |
|---|---|---|
| BAB | Babidi | 96 |
| BDK | Bardock | 99-100 |

### 1.5 No-personaje
| Código | Contenido |
|---|---|
| ALL | Mapas/escenarios (ALL_ROOT, ALL_P32...) |
| DEL | Efectos (DEL_L00_EFT...) |
| ANS | Android genérico |

---

## 2. BINS DE PERSONAJES EN data_XX.afs (data_us / data_sp / data_fr)

> Los AFS de idioma (data_us, data_sp, data_fr) comparten la MISMA numeración
> de bins. Escaneo completo del data_us.afs (14/08): 446 bins con labels de
> personaje. El output completo está en `%TEMP%\opencode\b1_chars_scan.txt`.

### 2.1 Estructura por personaje
Cada personaje tiene un bloque:
- **#ACM** (rig, ~1.3-1.6MB) seguido de **varios #AWO** (trajes, ~0.2-0.8MB c/u)
- Ej: VGT 2486(#ACM) → 2491-2519 (16 AWO = 16 trajes/variantes)
- Los #AWO pueden compartir un #AZT de texturas (el bin posterior)

### 2.2 Bloque de androides (bins 0-60) — VERIFICADO
| Bin | Tipo | Personaje |
|---|---|---|
| 0 | #ACM | Android 16 |
| 5,7,9,13,15 | #AWO | Android 16 (trajes) |
| 18 | #ACM | Android 17 |
| 23,25 | #AWO | Android 17 |
| 28 | #ACM | Android 18 |
| 33,35,37 | #AWO | Android 18 |
| 40 | #ACM | Android 19 |
| 45,47,49 | #AWO | Android 19 (`X19G_BODY`) |
| **52** | **#AWO** | **Dr. Gero (`X20G_BODY`)** |
| **53** | **#AZT (4 tex)** | **Texturas Gero nativo** |
| 50 | #AZT | Texturas (19G/20G) |

### 2.3 Bloques de personajes jugables (VERIFICADO por instrumentación)
| Personaje | #ACM rig | #AWO combate | #AZT combate |
|---|---|---|---|
| **Tenshinhan** | 2445 | 2450 | 2451 (bloque 2445-2456) |
| **Piccolo** | 1761 | 1768 | 1769 (bloque 1761-1770) |
| **Vegeta** | 2486 | 2491-2519 | — |
| **Trunks** | 2415 | 2420-2442 | — |
| **Yamcha** | 2528 | 2533-2539 | — |
| **Frieza** | 1109 | 1114-1128 | — |
| **Gero (20G, no jugable)** | — | 52 | 53 |

### 2.4 Contenedores multi-personaje (modo historia/cinemáticas)
Los bins #AMB ~944-1100 y 1977-1996 contienen varios personajes (datos de
historia). Ej:
| Bin | Personajes |
|---|---|
| 520,525 | GOK, RAD, GHN, PIC, TSH, KLL, RCM, VGT, FRZ, 18G, THL |
| 1046 | GOK, 20G, 19G |
| 1050 | VGT, 20G, 19G |
| 1004-1010 | GOK, GNY, JES, VGT (saga Ginyu) |
| 1012-1044 | FRZ, VGT, GOK (saga Freeza) |
| 960-968 | NAP, SBM, VGT (saga Saiyan) |

---

## 3. ESTRUCTURA DE UN PERSONAJE (bloque de combate)

Cada personaje jugable tiene un bloque de bins contiguos:
```
[rig #ACM][#CCM][#CFC][#CSK][#SPX][#AWO geom][#AZT tex][#AWO #AZT...]  (trajes)
```
Ejemplo Tenshinhan: 2445(#ACM) 2446(#CCM) 2447(#CFC) 2448(#CSK) 2449(#SPX)
2450(#AWO) 2451(#AZT) 2452-2455(trajes 2-3) 2456(#ACM extra).

Para un **model swap**: reemplazar el #AWO + #AZT del personaje objetivo con
los de otro personaje. Ver `docs/INVESTIGACION_FORMATO_B1_HD.md` sección 10.

---

## 4. B3 HD (referencia para portar personajes)

El B3 HD (`C:\...\DBZ Budokai 3 HD Collection\us\data_cmn.afs`) usa bins #AMB
(con #AWO + #AZT adentro). Personajes verificados:

| Personaje | Bin B3 | Labels |
|---|---|---|
| **Dr. Gero (20G)** | 91 | 20G_* |
| Goku | 90, 95 | GOK_* |
| Babidi | 96 | BAB_* |
| Bardock | 99-100 | BDK_* |

Los bins de B3 son #AMB BE (separar con `split_amb.py`).

---

## 5. MÉTODO PARA IDENTIFICAR UN PERSONAJE

1. **Jugar con el personaje** (si es jugable): activar el log "AFS BIN READ"
   (ya integrado en `host_path_file.cpp`) para capturar qué bins lee.
2. **Escaneo estático**: descomprimir bins y buscar el label `XXX_BODY`
   (el hueso raíz del esqueleto). Script: `scan_gero_body.py` (adaptable).
3. **Comparar bloques**: los personajes tienen bloques contiguos de bins
   con el patrón #ACM→#AWO→#AZT.

---

## 6. CHARACTER IDs (SLXS) — de tutoriales B3/IW

Los IDs de personaje del sistema SLXS (distintos de los códigos de labels):
```
05 GREAT SAIYAMAN | 08 FUTURE TRUNKS | 0E HERCULE SATAN (Mr. Satan)
16 GULDO | 17 JEICE | 18 BURTER | 19 ZARBON | 1A DODORIA (Ginyu force)
1F ANDROID 19 | 29 OMEGA SHENRON | 2D SUPER BABY VEGETA 2 | 2E SUPER ANDROID 17
40 GOTENKS | 44 GOGETA | 46 GOGETA SSJ4 | 48 VEGITO | 4C KIBITO KAI
4E BUU GOTENKS | 4F BUU GOHAN | 54 BUU PICCOLO | 55 GOTENKS LARGE
5B GOKU SSJ4 | 5C VEGETA SSJ4 | 5D MAJIN VEGETA | 5E-62 FRIEZA formas
63-65 CELL semi/perfect/super | 66-67 COOLER | 68 BROLY LSSJ | 69 DEMON KING PICCOLO
```
> Sirven para identificar a qué personaje corresponde un código de label ambiguo.
> Ver `docs/TUTORIALES_MODDING.md` sección 3.

---

## 7. PERSONAJES CONVERTIDOS EN "Budokai 1 Models Converted to AMB"

En `C:\...\DBZ Budokai 3 HD Collection\modding resources update\Budokai 1 Models Converted to AMB\`:
- 230 bins `XXX00.bin` = #AMB PS2 LE (modelo + texturas)
- `20G00.bin` = Gero, `TSH00.bin` = Tenshinhan, etc.
- Formato: #AMO0 (modelo LE) + #AMT (texturas LE)
