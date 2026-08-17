"""Extraer el #AWO + #AZT de un contenedor #AMB HD (B3/B1).

El #AMB del HD (360) es [header, #AWO, #AZT]:
  - #AWO en +0x40 (o buscar magic)
  - #AZT después (o buscar magic)

Uso:
  python extract_amb_awo.py <bin_amb.bin> [out_prefix]
  -> <out_prefix>_awo.bin, <out_prefix>_azt.bin
"""
import struct
import sys
import os

U32 = struct.Struct('>I')


def u32r(b, o):
    return U32.unpack_from(b, o)[0]


def main():
    if len(sys.argv) < 2:
        print('Uso: extract_amb_awo.py <bin_amb.bin> [out_prefix]')
        return
    src = sys.argv[1]
    prefix = sys.argv[2] if len(sys.argv) > 2 else src.rsplit('.', 1)[0]
    b = open(src, 'rb').read()

    print('%s: %d bytes magic=%s' % (src, len(b), b[:4]))
    if b[:4] != b'#AMB':
        print('NO es #AMB')
        return

    # buscar #AWO y #AZT
    i_awo = b.find(b'#AWO')
    i_azt = b.find(b'#AZT')
    if i_awo < 0:
        # quizás es un #AWO directo
        if b[:4] == b'#AWO':
            open(prefix + '_awo.bin', 'wb').write(b)
            print('Es #AWO directo, copiado')
        else:
            print('No #AWO encontrado')
        return
    if i_azt < 0:
        i_azt = len(b)
    awo = b[i_awo:i_azt]
    azt = b[i_azt:] if i_azt < len(b) else b''

    open(prefix + '_awo.bin', 'wb').write(awo)
    if azt:
        open(prefix + '_azt.bin', 'wb').write(azt)
    print('#AWO: %d bytes (%d AWGs) | #AZT: %d bytes' % (
        len(awo), u32r(awo, 0x18), len(azt)))

    # resumen de AWGs
    n = u32r(awo, 0x18)
    tbl = u32r(awo, 0x1C)
    for i in range(min(n, 8)):
        off = u32r(awo, tbl + i * 4)
        if off + 0x40 <= len(awo):
            no = u32r(awo, off + 0x1C)
            lab = awo[off + no: off + no + 16].split(b'\x00')[0].decode('latin1', 'ignore')
            flag = u32r(awo, off + 0x0C)
            print('  AWG%d @0x%X: %s (flag 0x%X)' % (i, off, lab, flag))


if __name__ == '__main__':
    main()
