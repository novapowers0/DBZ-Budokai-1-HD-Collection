"""analyze_submesh5.py — verificación DEFINITIVA de la semántica de rangos A/B.

Hipótesis: A/B son (offset<<8) y (size<<8) donde las unidades son:
  A = vértices sec34 (stride 44), B = índices IB (u16).
Desc0 A=0..0x2600 -> verts 0..37 (0x26). Verifica contiguidad y totales.
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
    anchors = [m.start() for m in re.finditer(rb'max \d+ m', z)]
    anchors.sort()
    print('%s: zona=%#x..%#x len=%#x, desc=%d' % (path, arms_end, sec, len(z), len(anchors)))
    a_start = a_size = b_start = b_size = None
    rows = []
    for k, a in enumerate(anchors):
        d = a - 0x30
        a08, a0C, a10, a14 = [u32r(z, d + o) for o in (0x08, 0x0C, 0x10, 0x14)]
        lbl = s(z[d + 0x18:d + 0x28])
        maxs = s(z[a:a + 8])
        # valores en unidades (>>8), y el byte bajo
        rows.append((k, lbl, a08 >> 8, a0C >> 8, a10 >> 8, a14 >> 8,
                     a08 & 0xFF, a0C & 0xFF, a10 & 0xFF, a14 & 0xFF, maxs))
        a_start, a_size, b_start, b_size = a08 >> 8, a0C >> 8, a10 >> 8, a14 >> 8
    # verificación A contiguo
    okA = True
    exp = 0
    totalA = 0
    for k, r in enumerate(rows):
        st, sz = r[2], r[3]
        if st != exp:
            okA = False
            print('  A no contiguo en %d: start=%d esperado=%d' % (k, st, exp))
        exp += sz
        totalA += sz
    # verificación B contiguo (con gaps?)
    totalB = 0
    prev_end = None
    gaps = []
    for k, r in enumerate(rows):
        st, sz = r[4], r[5]
        if prev_end is not None:
            gaps.append(st - prev_end)
        prev_end = st + sz
        totalB += sz
    print('A total=%d (sec_verts=%d) contiguo=%s' % (totalA, u32r(b, awg0 + 0x2C) // 44, okA))
    print('B total=%d (post_idx=%d)' % (totalB, u32r(b, awg0 + 0x34) // 2))
    print('gaps B entre descs: %s' % gaps)
    # bytes bajos
    print('bytes bajos A(start,size):', [(r[6], r[7]) for r in rows[:5]])
    print('bytes bajos B(start,size):', [(r[8], r[9]) for r in rows[:5]])
    # tabla compacta
    for r in rows:
        k, lbl, a_s, a_z, b_s, b_z, *_ = r
        print('[%02d] %-14s A=%5d..%5d(%3d) B=%6d..%6d(%4d) %s' % (k, lbl, a_s, a_s + a_z, a_z, b_s, b_s + b_z, b_z, r[10]))


if __name__ == '__main__':
    main(sys.argv[1])