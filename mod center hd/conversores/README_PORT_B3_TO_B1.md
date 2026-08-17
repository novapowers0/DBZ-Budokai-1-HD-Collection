# PORT B3 HD → B1 HD — Pipeline automático (validado 16/08/2026)

Convierte un modelo de **Budokai 3 HD** al formato de **Budokai 1 HD** e
instala el mod. **Validado 100% en runtime** con el Gero B3 → slot Tenshinhan.

## Requisitos

- Par de bins del personaje B3 HD: `#AWO` (geom) + `#AZT` (tex) del MISMO
  personaje (extraer del `data_cmn.afs` del B3).
- `xbcompress.exe` / `xbdecompress.exe` en `%TEMP%\opencode\xbcomp\` o en
  `mod center\Xbox 360 Compression...`.

## Uso (todo automático)

```
python install_b3_to_b1.py <awo_b3.bin> <azt_b3.bin> --mod <nombre> [--dest 2450] [--tex 2451]
```

- Porta el AWO (flag 0x2, type2 0x1BD/0x11BD, u34 FFFFFFFF, materiales B1).
- Fuerza el alpha DXT3 a 0xFF en el AZT.
- Comprime `/N:2048`, padea a slot, verifica round-trip, instala el mod y
  activa solo este mod.

## Solo conversión (sin instalar)

```
python port_b3_to_b1_v2.py <awo_b3.bin> <azt_b3.bin> <out.awo> <out_azt.bin> [--flatten] [--remap <ref.b1>]
```

## Qué convierte (crítico — omitir cualquiera → cuerpo negro)

| Concepto | B3 | B1 |
|---|---|---|
| Flag AWG `+0x0C` | 0x4 | 0x2 |
| Type2 mesh part `+0x38/+0x3C` | 0x1B5 / 0x29BD | 0x1BD |
| Sombra type2 | 0x1B4 | 0x190 |
| u34 `+0x34` mesh part | 1/5/7 | 0xFFFFFFFF |
| Escala material `+00` | 1.0 | **128.0** (specular) |
| Weights material `+10` | 1,1,1,0 | **0.85/0.80/0.70/1.0** |
| Type2 no-sombra | 0x1BD | **0x11BD** (shader alt) |
| Alpha AZT | DXT3 variable | **DXT3 0xFF** (opaco) |

## Detalle y fallos conocidos

- `docs/re/SESION10_PORT_B3_B1_FUNCIONAL.md`
- `docs/tutoriales/MODEL_SWAPS_METODOLOGIA.md` §4b
