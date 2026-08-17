"""Exportar la geometria de un bin HD (#AWO B1/B3) a OBJ (para Blender).

Uso:
  python export_sec34_obj.py <bin_hd.awo> <out.obj>

Lee el sec34 del bin HD (layout 01BD, stride 44, ver AGENTS.md) y el IB
(post), y exporta un OBJ para validar visualmente la geometria.

Layout del vertice (44B, big-endian):
  +00 pos.x +04 pos.y +08 pos.z
  +12 weight +16 BONE
  +20 nrm.x +24 nrm.y +28 nrm.z
  +32 0xFFFFFFFF +36 blend +40 uv

Offsets del header AWG0 (RELATIVOS al AWG):
  +0x28 sec_off (sec_abs = AWG + val) | +0x2C sec_size (n_sec = /44)
  +0x30 post_off | +0x34 post_size | +0x38 siguiente zona
"""
import struct
import sys


def u32r(data, off):
    return struct.unpack('>I', data[off:off + 4])[0]


def main():
    bin_path, out = sys.argv[1], sys.argv[2]
    awo = open(bin_path, 'rb').read()

    # Estructura AWO
    amg_am = u32r(awo, 0x18)
    tbl = u32r(awo, 0x1C)
    offs = [u32r(awo, tbl + i * 4) for i in range(amg_am)]
    AWG0 = offs[0]
    sec34_rel = u32r(awo, AWG0 + 0x28)
    sec34_sz = u32r(awo, AWG0 + 0x2C)
    post_rel = u32r(awo, AWG0 + 0x30)
    post_sz = u32r(awo, AWG0 + 0x34)
    sec34_abs = AWG0 + sec34_rel
    post_abs = AWG0 + post_rel

    n_sec = sec34_sz // 44
    n_ib = post_sz // 2

    print('sec34 @0x%X (%d verts), ib @0x%X (%d indices)' % (sec34_abs, n_sec, post_abs, n_ib))

    # Leer vertices (layout 01BD)
    verts = []
    for i in range(n_sec):
        d = awo[sec34_abs + i * 44:sec34_abs + (i + 1) * 44]
        if len(d) < 44:
            break
        x, y, z = struct.unpack('>3f', d[0:12])
        nx, ny, nz = struct.unpack('>3f', d[20:32])
        u, = struct.unpack('>f', d[40:44])
        verts.append((x, y, z, nx, ny, nz, u, 0.0))

    # IB: leer indices (u16)
    indices = []
    for i in range(0, n_ib * 2, 2):
        idx = struct.unpack('>H', awo[post_abs + i:post_abs + i + 2])[0]
        indices.append(idx)

    with open(out, 'w') as f:
        f.write('# Export del sec34 del bin HD\n')
        for (x, y, z, nx, ny, nz, u, v) in verts:
            f.write('v %.4f %.4f %.4f\n' % (x, y, z))
        for (x, y, z, nx, ny, nz, u, v) in verts:
            f.write('vn %.4f %.4f %.4f\n' % (nx, ny, nz))
        for (x, y, z, nx, ny, nz, u, v) in verts:
            f.write('vt %.4f %.4f\n' % (u, v))
        for i in range(0, len(indices) - 2, 3):
            a, b, c = indices[i], indices[i + 1], indices[i + 2]
            f.write('f %d/%d/%d %d/%d/%d %d/%d/%d\n' % (
                a + 1, a + 1, a + 1, b + 1, b + 1, b + 1, c + 1, c + 1, c + 1))
    print('OBJ guardado: %s (%d verts, %d caras)' % (
        out, len(verts), len(indices) // 3))


if __name__ == '__main__':
    main()
