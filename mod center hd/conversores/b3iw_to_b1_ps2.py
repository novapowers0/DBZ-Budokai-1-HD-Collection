"""Conversor B3/IW -> B1 PS2 (re-layout de headers de mesh part).

Portado del exe de la comunidad 'B3-IW_to_Budokai1_AMO_FacialSplit_TEST'
(descompilado con pyinstxtractor + xdis). La conversion es un RE-LAYOUT de
headers de mesh part, NO un re-rigging.

Constantes del bytecode original:
  STANDARD_HEADER   = B5 01 00 00 BD 29   (mesh part B3/IW)
  STANDARD_B1_HEADER = BD 01 00 00 BD 01   (destino B1)
  FACIAL_HEADER     = B4 01 00 00 B4 01
  FACIAL_B1_HEADER  = B4 62 00 00 BD 29
  FIELD_FFFFFFFF    = FF FF FF FF
  FACIAL_FIELD_14   = 8C 28 87 3F  (1.0559)
  FACIAL_FIELD_18   = BC E3 64 3E  (0.2235)
  STANDARD_FIELD_14 = C4 D5 5D 3F  (0.8665)
  STANDARD_FIELD_18 = 10 2B 3C BE  (-0.1838)
  FLOAT_08          = CD CC 4C 3F  (0.8)
  FLOAT_085         = 9A 99 59 3F  (0.85)
  FLOAT_10          = 00 00 80 3F  (1.0)
  FLOAT_SHADOW      = B9 8D FE 42  (127.27)
  FLOAT_128         = 00 00 00 43  (128.0)
  MIN_RECORD_SIZE   = 64

Posiciones escritas por convert_model para cada mesh part:
  data[off+0 : off+6]   = STANDARD_B1_HEADER / FACIAL_B1_HEADER
  data[off+12 : off+16] = FIELD_FFFFFFFF
  data[off+14 : off+24] = STANDARD_FIELD_14 / FACIAL_FIELD_14
  data[off+18 : off+28] = STANDARD_FIELD_18 / FACIAL_FIELD_18
  data[off+19]          = 0
  data[off+32..off+64]  = FLOAT_08, FLOAT_085, FLOAT_10, FLOAT_SHADOW,
                          FLOAT_128 x4

Uso:
  python b3iw_to_b1_ps2.py <archivo_b3iw.amo> <output.amo>
"""
import struct
import sys

STANDARD_HEADER = bytes.fromhex("B5 01 00 00 BD 29")
STANDARD_B1_HEADER = bytes.fromhex("BD 01 00 00 BD 01")
FACIAL_HEADER = bytes.fromhex("B4 01 00 00 B4 01")
FACIAL_B1_HEADER = bytes.fromhex("B4 62 00 00 BD 29")
FIELD_FFFFFFFF = bytes.fromhex("FF FF FF FF")
FACIAL_FIELD_14 = bytes.fromhex("8C 28 87 3F")
FACIAL_FIELD_18 = bytes.fromhex("BC E3 64 3E")
STANDARD_FIELD_14 = bytes.fromhex("C4 D5 5D 3F")
STANDARD_FIELD_18 = bytes.fromhex("10 2B 3C BE")
FLOAT_08 = bytes.fromhex("CD CC 4C 3F")
FLOAT_085 = bytes.fromhex("9A 99 59 3F")
FLOAT_10 = bytes.fromhex("00 00 80 3F")
FLOAT_SHADOW = bytes.fromhex("B9 8D FE 42")
FLOAT_128 = bytes.fromhex("00 00 00 43")
MIN_RECORD_SIZE = 64


def find_non_overlapping(data, pattern):
    positions = []
    start = 0
    while True:
        position = data.find(pattern, start)
        if position == -1:
            return positions
        positions.append(position)
        start = position + len(pattern)


def convert_model(source, output):
    original = open(source, 'rb').read()
    data = bytearray(original)

    standard_positions = find_non_overlapping(data, STANDARD_HEADER)
    facial_positions = find_non_overlapping(data, FACIAL_HEADER)

    parts = [(p, False) for p in standard_positions]
    parts.extend((p, True) for p in facial_positions)
    parts.sort()

    if not parts:
        print("No supported original B3/IW model-part headers were found.")
        return

    for offset, is_facial in parts:
        if offset + MIN_RECORD_SIZE > len(data):
            print("A possible model part at 0x%X is truncated." % offset)
            continue
        if is_facial:
            data[offset:offset + 6] = FACIAL_B1_HEADER
            data[offset + 14:offset + 24] = FACIAL_FIELD_14
            data[offset + 18:offset + 28] = FACIAL_FIELD_18
        else:
            data[offset:offset + 6] = STANDARD_B1_HEADER
            data[offset + 14:offset + 24] = STANDARD_FIELD_14
            data[offset + 18:offset + 28] = STANDARD_FIELD_18
        data[offset + 12:offset + 16] = FIELD_FFFFFFFF
        data[offset + 19] = 0
        data[offset + 32:offset + 36] = FLOAT_08
        data[offset + 36:offset + 40] = FLOAT_085
        data[offset + 40:offset + 44] = FLOAT_10
        data[offset + 44:offset + 48] = FLOAT_SHADOW
        data[offset + 48:offset + 52] = FLOAT_128
        data[offset + 52:offset + 56] = FLOAT_128
        data[offset + 56:offset + 60] = FLOAT_128
        data[offset + 60:offset + 64] = FLOAT_128

    with open(output, 'wb') as f:
        f.write(bytes(data))
    print('Convertidos %d mesh parts (estandar=%d, faciales=%d)' % (
        len(parts), len(standard_positions), len(facial_positions)))
    print('Guardado: %s (%d bytes)' % (output, len(data)))


if __name__ == '__main__':
    if len(sys.argv) < 3:
        print('Uso: b3iw_to_b1_ps2.py <archivo_b3iw.amo> <output.amo>')
        sys.exit(1)
    convert_model(sys.argv[1], sys.argv[2])
