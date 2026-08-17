"""analyze_submesh.py — RE completo de la zona de submesh data.

Localiza la zona entre arms y sec34, parsea los descriptores 0x60B
y cruza con mesh parts, arms y sec34 para determinar la base de los rangos.

Uso: python analyze_submesh.py <bin_hd> [--dump-zone]
"""
import struct
import re
import sys


def u32r(b, o):
    return struct.unpack('>I', b[o:o + 4])[0]


def f32r(b, o):
    return struct.unpack('>f', b[o:o + 4])[0]


def u16r(b, o):
    return struct.unpack('>H', b[o:o + 2])[0]


def analyze(path, dump=False):
    b = open(path, 'rb').read()
    print('== %s (%d B) ==' % (path, len(b)))
    awg_tbl = u32r(b, 0x1C)
    awg0 = u32r(b, awg_tbl)
    n_awg = u32r(b, 0x18)
    n_bones = u32r(b, awg0 + 0x3C)
    sec_rel = u32r(b, awg0 + 0x28)
    sec_size = u32r(b, awg0 + 0x2C)
    post_rel = u32r(b, awg0 + 0x30)
    post_size = u32r(b, awg0 + 0x34)
    axes_rel = u32r(b, awg0 + 0x14)
    arm_root_rel = u32r(b, awg0 + axes_rel + 0x34)
    arm_root = awg0 + arm_root_rel
    print('AWG0=%#x n_awg=%d n_bones=%d' % (awg0, n_awg, n_bones))
    print('sec_rel=%#x sec_size=%#x (%d v * 44)' % (sec_rel, sec_size, sec_size // 44))
    print('post_rel=%#x post_size=%#x' % (post_rel, post_size))
    print('axes_rel=%#x arm_root(rel)=%#x arm_root=%#x' % (axes_rel, arm_root_rel, arm_root))

    arms_end = arm_root + n_bones * 0x14
    zone = (arms_end, awg0 + sec_rel)
    print('zona submesh: [%#x .. %#x) len=%#x (%d)' % (zone[0], zone[1], zone[1] - zone[0], zone[1] - zone[0]))

    z = b[zone[0]:zone[1]]
    # buscar descriptores por su string 'max N m'
    idxs = [m.start() for m in re.finditer(rb'max \d+ m', z)]
    print('descriptores encontrados: %d' % len(idxs))
    desclabels = [m.start() for m in re.finditer(rb'(?:X)?(?:CHZ|TSH|GOK|X\d\w)_[A-Z0-9_]+', z)]
    print('labels en zona: %d' % len(desclabels))

    # asumir espaciado 0x60 entre 'max N m'
    for k, i in enumerate(idxs):
        s0 = i - 0x38  # offset del descriptor (max string a +0x38)
        if s0 < 0:
            continue
        c08 = u32r(z, s0 + 0x08)
        c0C = u32r(z, s0 + 0x0C)
        c10 = u32r(z, s0 + 0x10)
        c14 = u32r(z, s0 + 0x14)
        lbl = z[s0 + 0x18:s0 + 0x28].rstrip(b'\x00').decode('ascii', 'replace')
        maxs = z[i:i + 12]
        extra58 = u32r(z, s0 + 0x58)
        extra5C = u32r(z, s0 + 0x5C)
        # floats de transformación al inicio
        fl = [f32r(z, s0 + j) for j in range(0, 0x20, 4)]
        print('[%02d] +%04x lbl=%-20s c08=%#08x c0C=%#08x c10=%#08x c14=%#08x max=%s +58=%#08x +5C=%#08x' % (
            k, s0, lbl, c08, c0C, c10, c14, maxs[4:8].decode(), extra58, extra5C))

    # enlace mesh-ref: primer descriptor +0x58
    if idxs:
        s0 = idxs[0] - 0x38
        p58 = u32r(z, s0 + 0x58)
        print('\nprimer descriptor +58 = %#x (rel AWG0? abs=%#x)' % (p58, awg0 + p58))
        # cadena de mesh-ref blocks
        if 0 < p58 < len(b) - awg0:
            cur = awg0 + p58
            chain = []
            for _ in range(30):
                seal = u32r(b, cur)
                ptr = u32r(b, cur + 4)
                chain.append((cur - awg0, seal, ptr))
                if seal == 0:
                    break
                # avanzar a siguiente bloque (heurística)
                cur += 0x24
            for c in chain:
                print('  mesh-ref @rel %#x: seal=%#x ptr=%#x' % c)

    return zone


if __name__ == '__main__':
    analyze(sys.argv[1], '--dump-zone' in sys.argv)