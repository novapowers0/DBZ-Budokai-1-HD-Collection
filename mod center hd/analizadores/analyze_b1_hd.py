"""Analizador de bin HD B1 (#AWO / #AWG). Muestra la estructura completa.

Uso:
  python analyze_b1_hd.py <bin.awo>

Muestra:
  - Header AWO (bones, AWGs, tabla, labels)
  - Cada AWG: header (12 campos), sec34, vb2, IB, restart, bones
  - Labels de huesos por AWG
  - Rango de posiciones del sec34
  - Mesh group / mesh-ref blocks si se detectan
"""
import struct
import sys


def u32r(data, off):
    return struct.unpack('>I', data[off:off + 4])[0]


def f32r(data, off):
    return struct.unpack('>f', data[off:off + 4])[0]


def main():
    path = sys.argv[1]
    b = open(path, 'rb').read()
    print('=== %s (%d bytes) ===' % (path, len(b)))
    print('magic: %s' % b[:4])

    if b[:4] != b'#AWO':
        print('NO es un #AWO (quizas es AMB o requiere extraer)')
        return

    # Header AWO
    num_bones = u32r(b, 0x10)
    num_awgs = u32r(b, 0x18)
    tbl = u32r(b, 0x1C)
    bone_names_off = u32r(b, 0x24)
    print('\n=== Header AWO ===')
    print('  num_bones: %d' % num_bones)
    print('  num_awgs: %d' % num_awgs)
    print('  tabla AWG: 0x%X' % tbl)
    print('  bone_names: 0x%X' % bone_names_off)

    offs = [u32r(b, tbl + i * 4) for i in range(min(num_awgs, 32))]
    print('  AWG offsets:', [hex(x) for x in offs])

    # Labels de huesos (del AWO)
    print('\n=== Labels de huesos ===')
    for bi in range(min(num_bones, 51)):
        s = b[bone_names_off + bi * 2 * 16:bone_names_off + bi * 2 * 16 + 16]
        s = s.split(b'\x00')[0].decode('latin1', 'ignore')
        if s:
            print('  bone %2d: %s' % (bi, s))

    # Cada AWG
    for awg_i in range(min(num_awgs, 8)):
        AWG = offs[awg_i]
        if AWG + 0x40 > len(b):
            break
        print('\n=== AWG%d @0x%X (%s) ===' % (awg_i, AWG, b[AWG:AWG + 4]))
        # 12 campos del header
        campos = [
            ('offset subs', 0x10), ('size subs', 0x14), ('flag', 0x18),
            ('offset name', 0x1C), ('offset materials', 0x20),
            ('size materials', 0x24), ('offset vertices', 0x28),
            ('size vertices', 0x2C), ('offset faces', 0x30),
            ('size faces', 0x34), ('offset bones', 0x38),
            ('size bones', 0x3C),
        ]
        for name, off in campos:
            print('  %-18s +0x%02X: 0x%X' % (name, off, u32r(b, AWG + off)))
        # labels del AWG (offset name)
        oname = u32r(b, AWG + 0x1C)
        print('  labels @0x%X:' % (AWG + oname))
        for bi in range(min(8, 51)):
            s = b[AWG + oname + bi * 16:AWG + oname + bi * 16 + 16]
            s = s.split(b'\x00')[0].decode('latin1', 'ignore').encode('ascii', 'ignore').decode()
            if s:
                print('    bone %2d: %s' % (bi, s))
        # buffers — offsets RELATIVOS al AWG (v10, verificado en TSH nativo)
        # +0x28 sec_off, +0x2C sec_size, +0x30 post_off, +0x34 post_size
        sec34_rel = u32r(b, AWG + 0x28)
        sec34_sz = u32r(b, AWG + 0x2C)
        post_rel = u32r(b, AWG + 0x30)
        post_sz = u32r(b, AWG + 0x34)
        restart_rel = u32r(b, AWG + 0x38)
        sec34_abs = AWG + sec34_rel
        post_abs = AWG + post_rel
        n_sec = sec34_sz // 44
        n_ib = post_sz // 2
        print('  sec34 @0x%X (%d verts x44)' % (sec34_abs, n_sec))
        print('  post/IB @0x%X (%d indices)' % (post_abs, n_ib))
        # rango de posiciones del sec34
        if n_sec > 0:
            xs, ys, zs = [], [], []
            for i in range(min(n_sec, 2000)):
                d = b[sec34_abs + i * 44:sec34_abs + (i + 1) * 44]
                if len(d) < 12:
                    break
                x, y, z = struct.unpack('>3f', d[0:12])
                xs.append(x); ys.append(y); zs.append(z)
            if xs:
                print('  sec34 pos: x=[%.3f,%.3f] y=[%.3f,%.3f] z=[%.3f,%.3f]' % (
                    min(xs), max(xs), min(ys), max(ys), min(zs), max(zs)))
        # mesh group: buscar zona de labels con offset name
        # los mesh-ref blocks suelen estar en la zona de vertices antes del sec34
        print('  (mesh group: buscar en zona 0x%X..0x%X)' % (AWG + 0x40, sec34_abs))


if __name__ == '__main__':
    main()
