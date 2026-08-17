# CONVERSOR B3/IW → B1 (COMUNIDAD) — RE DEL BYTECODE
> Copyright (c) NovaPowers. Released under the MIT License. Firmado por NovaPowers.
>

> Analizado el 14/08/2026. Fuente: `modding resources discord\tools\B3-IW_to_Budokai1_AMO_FacialSplit_TEST.exe`
> (PyInstaller 3.10). Extraído con pyinstxtractor_ng, desensamblado con xdis.
> Autor de la herramienta: comunidad "Dragon Ball Z Budokai Modding Community".

---

## 1. HALLAZGO CLAVE

**La conversión B3/IW → B1 ES UN RE-LAYOUT DE HEADERS DE MESH PART.**
No es un re-rigging ni un re-mapeo de huesos. La función `convert_model()`
busca los headers de mesh part B3/IW en el binario y **reescribe cada uno**
a formato B1 con valores fijos. El resto del binario (vértices, índice,
rigs, malla) se conserva intacto.

Esto explica por qué nuestros experimentos de re-rigging B3→B1 fallaban:
**no hace falta tocar huesos ni pesos** — solo hay que convertir los headers
de mesh part (type1/type2) y el campo de matriz.

## 2. CONSTANTES DECODIFICADAS (del bytecode)

Headers buscados en el archivo B3/IW (patrón no-solapado, `find_non_overlapping`):

| Constante | Bytes | Significado |
|-----------|-------|-------------|
| `STANDARD_HEADER` | `B5 01 00 00 BD 29` | Mesh part B5 estándar B3/IW |
| `FACIAL_HEADER` | `B4 01 00 00 B4 01` | Mesh part facial B3/IW |

Constantes globales del módulo (declaradas con `bytes.fromhex` en top-level,
orden del bytecode — los NOMBRES reales del autor):

```
STANDARD_HEADER   = bytes.fromhex("B5 01 00 00 BD 29")
STANDARD_B1_HEADER = bytes.fromhex("BD 01 00 00 BD 01")
FACIAL_HEADER     = bytes.fromhex("B4 01 00 00 B4 01")
FACIAL_B1_HEADER  = bytes.fromhex("B4 62 00 00 BD 29")
FIELD_FFFFFFFF    = bytes.fromhex("FF FF FF FF")
FACIAL_FIELD_14   = bytes.fromhex("8C 28 87 3F")   # 1.0559
FACIAL_FIELD_18   = bytes.fromhex("BC E3 64 3E")   # 0.2235
STANDARD_FIELD_14 = bytes.fromhex("C4 D5 5D 3F")   # 0.8665
STANDARD_FIELD_18 = bytes.fromhex("10 2B 3C BE")   # -0.1838
FLOAT_08          = bytes.fromhex("CD CC 4C 3F")   # 0.8000
FLOAT_085         = bytes.fromhex("9A 99 59 3F")   # 0.8500
FLOAT_10          = bytes.fromhex("00 00 80 3F")   # 1.0000
FLOAT_SHADOW      = bytes.fromhex("B9 8D FE 42")   # 127.2768
FLOAT_128         = bytes.fromhex("00 00 00 43")   # 128.0000
MIN_RECORD_SIZE   = 64
```

## 3. POSICIONES ESCRITAS POR LA FUNCIÓN convert_model (bytecode)

Para CADA mesh part encontrado (offset = posición del header):

```
data[offset+0 : offset+6]  = STANDARD_B1_HEADER o FACIAL_B1_HEADER
data[offset+12 : offset+16] = FIELD_FFFFFFFF
data[offset+14 : offset+24] = STANDARD_FIELD_14 / FACIAL_FIELD_14
data[offset+18 : offset+28] = STANDARD_FIELD_18 / FACIAL_FIELD_18
data[offset+19]             = 0
data[offset+32 : offset+36] = FLOAT_08      (0.8000)
data[offset+36 : offset+40] = FLOAT_085     (0.8500)
data[offset+40 : offset+44] = FLOAT_10      (1.0000)
data[offset+44 : offset+48] = FLOAT_SHADOW  (127.2768)
data[offset+48 : offset+52] = FLOAT_128     (128.0000)
data[offset+52 : offset+56] = FLOAT_128     (128.0000)
data[offset+56 : offset+60] = FLOAT_128     (128.0000)
data[offset+60 : offset+64] = FLOAT_128     (128.0000)
```

Nota: mi primera lectura asignó `FLOAT_08=1.0559` por el orden de co_consts,
pero el top-level del bytecode revela que `8C 28 87 3F` es en realidad
`FACIAL_FIELD_14` y `BC E3 64 3E` es `FACIAL_FIELD_18`. Los valores correctos
de los floats de la matriz (+32..64) son: **0.8, 0.85, 1.0, 127.27, 128.0**.

La variable `is_facial` decide STANDARD vs FACIAL: los faciales (B4) usan
FACIAL_B1_HEADER y FACIAL_FIELD_14/18.

Validación de truncamiento: `if offset + MIN_RECORD_SIZE (64) > len(data):
raise ValueError("...is truncated...")` — el parser exige al menos 64 bytes
por mesh part.

## 4. IMPLICACIONES PARA EL PORT B3→B1 HD

1. **El mesh part header del AWO HD es el MISMO que el PS2** (type1/type2).
   El conversor PS2 B3→B1 valida que el re-layout es solo: type1/type2 + campos
   +14/+18/+19 + matriz de floats.

2. **Los floats de matriz (+32..64) en B1 son: 1.0559, 0.2235, 0.8665, -0.1838,
   0.8, 0.85, 1.0, 127.27, 128.0** — estos son constantes del shader de B1
   (sombra/normales), NO una matriz de bind pose.

3. **En el HD**, los mesh parts B3 (Gero, Krillin) tienen type1/type2 que deben
   convertirse igual. Nuestro `build_hd_pipeline.py` ya maneja type1 (0x1B5→0xBD)
   pero NO el campo de matriz +32..64 ni el +14/+18.

4. **Plan de acción HD**: aplicar la misma lógica al AWO HD:
   - Buscar `B5 01 00 00 BD 29` y `B4 01 00 00 B4 01` en el bin HD B3
   - Reemplazar por `BD 01 00 00 BD 01` / `B4 62 00 00 BD 29`
   - Escribir `FF FF FF FF` en +12, `0` en +19, y los floats en +32..64

## 5. CÓMO SE EXTRAJO

- `pyinstxtractor_ng <exe>` → extrae PyInstaller 2.1+, Python 3.10
- Entry point: `AMO_Converter_FacialSplit_TEST.pyc`
- `xdis.load_module()` + `xdis.opcodes.opcode_310` + `Bytecode(c, opc)` →
  desensambla `convert_model`, `find_non_overlapping`, `resource_path`,
  `unique_path`, `default_output_path`
- Las constantes son strings de bytes hex en los co_consts del módulo

## 6. PENDIENTE

- Extraer `STANDARD_FIELD_14`, `STANDARD_FIELD_18`, `FACIAL_FIELD_14`,
  `FACIAL_FIELD_18` (más constantes del bytecode de ConverterApp, la GUI)
- Aplicar la lógica al pipeline HD y probar con Gero B3→B1
- Verificar si `MIN_RECORD_SIZE` limita el parseo (el bytecode usa `offset +
  MIN_RECORD_SIZE > len(data)` para validar truncamiento)
