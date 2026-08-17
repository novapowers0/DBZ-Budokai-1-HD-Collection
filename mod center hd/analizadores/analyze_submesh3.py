"""analyze_submesh3.py — verifica la semántica de los rangos A/B de los descriptores.

Hipótesis: los campos se almacenan escalados por 256.
  A: size = n_verts*256, start = cum_verts*256
  B: size = n_idx*256+1, start = (cum_idx + 2*part)*256
Verifica contra sec_size (verts) y post_size (indices).
"""
import struct
import re
import sys


def u32r(b, o):
    return struct.unpack('>I', b[o:o + 4])[0]


def main(path):
    b = open(path, 'rb').read()
    awg0 = u32r(b, u32r(b, 0x1C))
    n_bones = u32r(b, awg0 + 0x3C)
    axes_rel = u32r(b, awg0 + 0x14)
    arm_root_rel = u32r(b, awg0 + axes_rel + 0x34)
    arms_end = awg0 + arm_root_rel + n_bones * 0x14
    sec = awg0 + u32r(b, awg0 + 0x28)
    z = b[arms_end:sec]
    d0 = z.find(b'max ') - 0x38
    if d0 < 0:
        d0 = re.search(rb'(?:X?)(?:CHZ|TSH|GOK|X\d\w)_[A-Z0-9_]+', z).start() - 0x18
    n_desc = (len(z) - d0) // 0x60
    print('desc=%d zona=%#x' % (n_desc, d0))
    totA = 0
    totB = 0
    startsA = []
    startsB = []
    for k in range(n_desc):
        s = d0 + k * 0x60
        a_start, a_size = u32r(z, s + 0x08), u32r(z, s + 0x0C)
        b_start, b_size = u32r(z, s + 0x10), u32r(z, s + 0x14)
        lbl = z[s + 0x18:s + 0x28].rstrip(b'\x00')
        cntA = a_size >> 8
        cntB = b_size >> 8
        totA += cntA
        totB += cntB
        startsA.append(a_start >> 8)
        startsB.append(b_start >> 8)
        if k < 25:
            print('[%02d] %-16s A=%4d v (%#x) B=%4d i (%#x)  cumA=%#x cumB=%#x' % (
                k, lbl[:12].decode('ascii', 'replace'), cntA, a_size, cntB, b_size, a_start >> 8, b_start >> 8))
    print('\nTOTAL A (verts): %d' % totA)
    print('TOTAL B (indices): %d' % totB)
    sec_size = u32r(b, awg0 + 0x2C)
    post_size = u32r(b, awg0 + 0x34)
    print('sec_size//44 = %d verts | post_size//2 = %d indices' % (sec_size // 44, post_size // 2))
    # verificar contiguidad
    expA = 0
    okA = True
    for k, (st, sz) in enumerate(zip(startsA, [u32r(z, d0 + k2 * 0x60 + 0x0C) >> 8 for k2 in range(n_desc)])):
        if st != expA:
            okA = False
            print('A no contiguo en %d: start=%d esperado=%d' % (k, st, expA))
        expA += sz
    print('A contiguo:', okA, '| A total*256 =', hex(totA * 256))


if __name__ == '__main__':
    main(sys.argv[1])