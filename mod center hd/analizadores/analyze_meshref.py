"""analyze_meshref.py — RE de la cadena mesh-ref (bloques sello 0x2XX) del HD.

Cada bloque (0x50B) enlaza un submesh con sus datos. Estructura observada:
  +00 seal 0x9000020C/0x80000204/0x80000206/0x8000020C
  +04 ptr_rel (a otro bloque o dato)
  +08 0
  +0C tamaño
  +10 0
  +14 ptr_rel
  +18.. floats / datos
  +30 4x 0x3F800000 (escala 1.0)
  +40.. datos por tipo

El puntero +0x58 de cada descriptor de submesh apunta al primer bloque
de su submesh. Hay tantos bloques como submeshes.
"""
import struct
import sys


def u32r(b, o):
    return struct.unpack('>I', b[o:o + 4])[0]


def f32r(b, o):
    return struct.unpack('>f', b[o:o + 4])[0]


def main(path):
    b = open(path, 'rb').read()
    awg0 = u32r(b, u32r(b, 0x1C))
    print('%s: AWG0=%#x' % (path, awg0))
    target = awg0 + 0x1158
    print('cadena mesh-ref en abs %#x' % target)
    # caminar bloques: cada bloque 0x50, siguiente bloque = +0x50
    # el campo +04 apunta al siguiente bloque (rel AWG0)
    cur = target
    seen = set()
    for i in range(40):
        if cur in seen:
            break
        seen.add(cur)
        if cur + 0x50 > len(b):
            break
        seal = u32r(b, cur)
        p04 = u32r(b, cur + 4)
        p08 = u32r(b, cur + 8)
        p0C = u32r(b, cur + 0xC)
        p10 = u32r(b, cur + 0x10)
        p14 = u32r(b, cur + 0x14)
        fl = [f32r(b, cur + j) for j in range(0x18, 0x40, 4)]
        print('blk[%02d] @%#x seal=%08x +04=%08x +08=%08x +0C=%08x +10=%08x +14=%08x fl=%s' % (
            i, cur, seal, p04, p08, p0C, p10, p14,
            ' '.join('%.3f' % v for v in fl)))
        nxt = awg0 + p04 if p04 else None
        cur = nxt if nxt and nxt != cur else cur + 0x50


if __name__ == '__main__':
    main(sys.argv[1])