"""analyze_submesh2.py — dump limpio de los descriptores de submesh con offsets correctos.

Descriptor 0x60B, label en +0x18, 'max N m' en +0x30.
"""
import struct
import re
import sys


def u32r(b, o):
    return struct.unpack('>I', b[o:o + 4])[0]


def u16r(b, o):
    return struct.unpack('>H', b[o:o + 2])[0]


def main(path):
    b = open(path, 'rb').read()
    awg0 = u32r(b, u32r(b, 0x1C))
    n_bones = u32r(b, awg0 + 0x3C)
    axes_rel = u32r(b, awg0 + 0x14)
    arm_root_rel = u32r(b, awg0 + axes_rel + 0x34)
    arms_end = awg0 + arm_root_rel + n_bones * 0x14
    sec = awg0 + u32r(b, awg0 + 0x28)
    z = b[arms_end:sec]
    d0 = 0x3bd - 0x18
    print('zona=%#x..%#x primer_desc=%#x (%d desc * 0x60)' % (arms_end, sec, d0, (len(z) - d0) // 0x60))
    for k in range((len(z) - d0) // 0x60):
        s = d0 + k * 0x60
        lbl = z[s + 0x18:s + 0x28].rstrip(b'\x00').decode('ascii', 'replace')
        a08 = u32r(z, s + 0x08)
        a0C = u32r(z, s + 0x0C)
        a10 = u32r(z, s + 0x10)
        a14 = u32r(z, s + 0x14)
        a20u16 = u16r(z, s + 0x20)
        a22u16 = u16r(z, s + 0x22)
        a24u16 = u16r(z, s + 0x24)
        a26u16 = u16r(z, s + 0x26)
        a28 = u32r(z, s + 0x28)
        a2C = u32r(z, s + 0x2C)
        maxs = z[s + 0x30:s + 0x38].rstrip(b'\x00').decode('ascii', 'replace')
        a58 = u32r(z, s + 0x58)
        a5C = u32r(z, s + 0x5C)
        print('[%02d] %-16s +08=%#08x +0C=%#08x +10=%#08x +14=%#08x  +20=%d +22=%d +24=%d +26=%d  +28=%#x +2C=%#x  %-8s +58=%#08x +5C=%#08x' % (
            k, lbl, a08, a0C, a10, a14, a20u16, a22u16, a24u16, a26u16, a28, a2C, maxs, a58, a5C))
    # sec34 / post para comparar
    sec_size = u32r(b, awg0 + 0x2C)
    post_size = u32r(b, awg0 + 0x34)
    print('\nsec_size=%#x (%d v)  post_size=%#x (%d idx)' % (sec_size, sec_size // 44, post_size, post_size // 2))


if __name__ == '__main__':
    main(sys.argv[1])