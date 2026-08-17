"""analyze_submesh4.py — análisis completo usando 'max N m' (+0x30) como ancla.

Cada descriptor 0x60/0x70 B tiene 'max N m' en +0x30 y label en +0x18.
Verifica la semántica de rangos A/B contra sec34 y post.
"""
import struct
import re
import sys


def u32r(b, o):
    return struct.unpack('>I', b[o:o + 4])[0]


def s(b):
    return b.split(b'\x00')[0].decode('ascii', 'replace')


def main(path):
    b = open(path, 'rb').read()
    awg0 = u32r(b, u32r(b, 0x1C))
    n_bones = u32r(b, awg0 + 0x3C)
    axes_rel = u32r(b, awg0 + 0x14)
    arm_root_rel = u32r(b, awg0 + axes_rel + 0x34)
    arms_end = awg0 + arm_root_rel + n_bones * 0x14
    sec = awg0 + u32r(b, awg0 + 0x28)
    z = b[arms_end:sec]
    # anclas 'max N m' (cada descriptor tiene exactamente uno en +0x30)
    anchors = [m.start() for m in re.finditer(rb'max \d+ m', z)]
    anchors.sort()
    print('%s: zona=%#x..%#x len=%#x, descriptores=%d' % (path, arms_end, sec, len(z), len(anchors)))
    totA = 0
    totB = 0
    prev_end = None
    for k, a in enumerate(anchors):
        d = a - 0x30
        if prev_end is not None:
            gap = d - prev_end
        else:
            gap = 0
        prev_end = d + 0x70
        a08, a0C, a10, a14 = [u32r(z, d + o) for o in (0x08, 0x0C, 0x10, 0x14)]
        lbl = s(z[d + 0x18:d + 0x28])
        maxs = s(z[a:a + 8])
        a58, a5C = u32r(z, d + 0x58), u32r(z, d + 0x5C)
        totA += a0C
        totB += a14
        print('[%02d] +%04x gap=%#x %-14s A=%8x..%8x B=%8x..%8x %-8s +58=%8x +5C=%8x' % (
            k, d, gap, lbl, a08, a08 + a0C, a10, a10 + a14, maxs, a58, a5C))
    print()
    print('sumA=%#x (%.1f KB)  sumB=%#x (%.1f KB)' % (totA, totA / 1024, totB, totB / 1024))
    print('sec_size=%#x (%.1f KB, %d v*44)  post_size=%#x (%.1f KB, %d idx*2)' % (
        u32r(b, awg0 + 0x2C), u32r(b, awg0 + 0x2C) / 1024, u32r(b, awg0 + 0x2C) // 44,
        u32r(b, awg0 + 0x34), u32r(b, awg0 + 0x34) / 1024, u32r(b, awg0 + 0x34) // 2))


if __name__ == '__main__':
    main(sys.argv[1])