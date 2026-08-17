"""amo0_to_awo.py — Port COMPLETO de un modelo PS2 (#AMO0) a un bin HD B1 (#AWO).

Estrategia (lección 9/10/18/22-23, validada por el B3 el 17/08):
  - El runtime HD dibuja el bin completo tal cual. Pero el AWG0 NO puede
    cambiar de tamaño: crecer crashea en combate (B3 v4), encogerse no
    arranca (v5). Tamaño FIJO (delta=0) = rellenar los buffers del template
    EN SU POSICIÓN y decimar el PS2 para que quepa (B3 v6).
  - Se regenera SOLO la zona de descriptores de submesh (rangos A/B) — la
    pieza que causaba hang al copiar la del template (lección 18/21).
  - Los ARMS del template NO se tocan (lección 22): el B3 probó que re-mapear
    arms crashea; "los offsets de los arms NO son rangos del IB a dibujar.
    El IB se dibuja completo; los offsets definen otra información (skinning)".

Requisito: el esqueleto PS2 debe ser el MISMO que el del slot HD (mismos
labels en el mismo orden). Verificado para CHZ→TSH (42 bones, XCHZ_* ↔ XTSH_*).

Layout vértice HD (44B, sesión 5 / v10):
  +00 pos.x +04 pos.y +08 pos.z
  +12 weight +16 BONE(u32) +20 nrm +32 0xFFFFFFFF +36 blend +40 uv

Layout vértice PS2 (48B): +00 pos(3) +10 nrm(3) +20 uv(2)
  Submeshes en cadena: header 0x20 con FaceType(+0x10: 1=strip, 0=triplete)
  y VertCount(+0x14). FaceType 1 = strip zig-zag, 0 = tripletes.

Descriptores de submesh B1 (entre arms y sec34, 0x60/0x70B c/u):
  +00 hdr (0x500 cuerpo / 0x400 extremidades)  +08 A_start<<8  +0C A_size<<8
  +10 B_start<<8  +14 (B_size<<8)|1  +18 label 16B
  +28 flag tipo por label  +2C 0xF000000  +30 "max N m"  +58 ptr mesh-ref<<8
  +5C stride(44)<<8 = 0x2C00

Uso:
  python amo0_to_awo.py <bin_ps2.amo|amb> <bin_hd_plantilla.awo> <out.awo>
"""
import struct
import sys
import re

U32 = struct.Struct('>I')
F32 = struct.Struct('>f')
U16 = struct.Struct('>H')
R32 = struct.Struct('<I')
RF32 = struct.Struct('<f')

VERT_STRIDE = {0xBD: 48, 0xFD: 48, 0x3D: 48, 0xB5: 48, 0xB6: 48, 0xF5: 48,
               0x199: 32, 0xB4: 32, 0xA4: 32, 0x99: 32, 0x92: 32, 0x19: 32,
               0x90: 16}


def u32r(b, o):
    return U32.unpack_from(b, o)[0]


def f32(v):
    return F32.pack(v)


def u32(v):
    return U32.pack(v & 0xFFFFFFFF)


def u16(v):
    return U16.pack(v & 0xFFFF)


def r32(b, o):
    return R32.unpack_from(b, o)[0]


def rf32(b, o):
    return RF32.unpack_from(b, o)[0]


def read_ps2_vert(b, off, vtype):
    if vtype in (0xBD, 0xFD, 0x3D, 0xB5, 0xB6, 0xF5):
        v = (rf32(b, off), rf32(b, off + 4), rf32(b, off + 8))
        n = (rf32(b, off + 16), rf32(b, off + 20), rf32(b, off + 24))
        u = (rf32(b, off + 32), rf32(b, off + 36))
        return v, n, u
    if vtype == 0x199:
        return (rf32(b, off), rf32(b, off + 4), rf32(b, off + 8)), \
               (rf32(b, off + 16), rf32(b, off + 20), rf32(b, off + 24)), (0.0, 0.0)
    if vtype in (0xB4, 0xA4, 0x99, 0x92, 0x19):
        return (rf32(b, off), rf32(b, off + 4), rf32(b, off + 8)), \
               (0.0, 0.0, 0.0), (rf32(b, off + 16), rf32(b, off + 20))
    return (rf32(b, off), rf32(b, off + 4), rf32(b, off + 8)), (0.0, 0.0, 0.0), (0.0, 0.0)


def read_faces(vertcount, facetype):
    faces = []
    if facetype == 1:
        f1, f2 = 0, 1
        direction = -1
        for x in range(2, vertcount):
            f3 = x
            direction *= -1
            if f1 != f2 and f2 != f3 and f3 != f1:
                if direction > 0:
                    faces.append((f1, f2, f3))
                else:
                    faces.append((f1, f3, f2))
            f1, f2 = f2, f3
    else:
        for x in range(1, vertcount + 1, 3):
            if x + 2 <= vertcount:
                faces.append((x - 1, x, x + 1))
    return faces


def parse_ps2_full(ps2, amo0):
    """Parsea TODOS los AMGs del PS2 (triángulos reales FaceType + skin).

    Devuelve (parts, skin_map):
      parts[i] = {'bone_idx', 'vtype', 'verts': [(pos,nrm,uv), ...],
                  'tris': [(i0,i1,i2), ...], 'gi'}
      skin_map[(gi, pi, vi)] = (bone, weight, coords_locales)
    """
    n_amg = r32(ps2, amo0 + 0x18)
    amg_tbl = amo0 + 0x30
    parts_all = []
    skin_map = {}

    for gi in range(n_amg):
        amg_off = r32(ps2, amg_tbl + gi * 4)
        amg = amo0 + amg_off
        bone_am = r32(ps2, amg + 0x10)
        axes_loc = r32(ps2, amg + 0x14)
        part_ranges = []

        for bi in range(bone_am):
            e0 = amg + axes_loc + bi * 80
            p34 = r32(ps2, e0 + 0x34)
            if not p34:
                continue
            arm = amg + p34
            mesh_hdr = r32(ps2, arm + 4)
            if not mesh_hdr:
                continue
            mg = amg + mesh_hdr
            mp_amnt = r32(ps2, mg)
            if mp_amnt == 0 or mp_amnt > 64:
                continue
            part_offs = [r32(ps2, mg + 16 + i * 4) for i in range(mp_amnt)]
            for pi, rel in enumerate(part_offs):
                po = mg + rel
                type1 = r32(ps2, po)
                vtype = type1 & 0xFF
                stride = VERT_STRIDE.get(vtype, 48)
                size_field = r32(ps2, po + 0x90)
                mesh_size = (size_field - 0x60000000) * 16 if size_field >= 0x60000000 else 0
                md = po + 0xA0
                end = md + mesh_size if mesh_size > 0 else po + 0x400
                end = min(end, len(ps2))
                verts, tris = [], []
                pos = md
                base_v = 0
                while pos + 0x20 < end:
                    facetype = r32(ps2, pos + 0x10)
                    vertcount = r32(ps2, pos + 0x14)
                    if vertcount == 0 or vertcount > 0xFFFF:
                        break
                    vp = pos + 0x20
                    if vp + vertcount * stride > end:
                        break
                    for x in range(vertcount):
                        verts.append(read_ps2_vert(ps2, vp + x * stride, vtype))
                    for f0, f1, f2 in read_faces(vertcount, facetype):
                        tris.append((base_v + f0, base_v + f1, base_v + f2))
                    base_v = len(verts)
                    pos = vp + vertcount * stride
                if not verts:
                    continue
                part = {'bone_idx': bi, 'vtype': vtype, 'verts': verts,
                        'tris': tris, 'gi': gi}
                parts_all.append(part)
                part_ranges.append((len(parts_all) - 1, md, len(verts) * stride))

        for bi in range(bone_am):
            e0 = amg + axes_loc + bi * 80
            p34 = r32(ps2, e0 + 0x34)
            if not p34:
                continue
            arm = amg + p34
            rig_ptr = r32(ps2, arm + 8)
            if not rig_ptr:
                continue
            r = amg + rig_ptr
            chunk_amnt = r32(ps2, r + 12)
            for i in range(chunk_amnt):
                c = r + 16 + i * 32
                weight = rf32(ps2, c)
                ch_len = r32(ps2, c + 4)
                ch_loc = r32(ps2, c + 8)
                if not ch_loc:
                    continue
                for e in range(ch_len):
                    entry = amg + ch_loc + e * 32
                    coords = (rf32(ps2, entry), rf32(ps2, entry + 4), rf32(ps2, entry + 8))
                    voff = r32(ps2, entry + 12)
                    abs_off = amg + voff
                    for pi2, p_abs, p_len in part_ranges:
                        if p_abs <= abs_off < p_abs + p_len:
                            vi = (abs_off - p_abs) // 48
                            skin_map[(gi, pi2, vi)] = (bi, weight, coords)
                            break
    return parts_all, skin_map


def build_vertex_44(pos, weight, bone, nrm, uv):
    """Layout HD B1 44B: pos(3) weight bone nrm(3) FFFF blend uv."""
    x, y, z = pos
    nx, ny, nz = nrm
    u = uv[0]
    return (f32(x) + f32(y) + f32(z) +
            f32(weight) + u32(bone) +
            f32(nx) + f32(ny) + f32(nz) +
            u32(0xFFFFFFFF) + f32(0.0) + f32(u))


def build_buffers(parts, skin_map):
    """sec34 (dedup por bytes) + IB REAL desde los triángulos PS2.

    Devuelve (sec_bytes, ib_indices, part_a, part_b).
    """
    sec = []
    sec_map = {}
    ib = []
    part_a = []
    part_b = []
    for pi, p in enumerate(parts):
        a_start = len(sec)
        b_start = len(ib)
        vremap = []
        for vi, (pos, nrm, uv) in enumerate(p['verts']):
            sk = skin_map.get((p['gi'], pi, vi))
            if sk:
                bone, weight, coords = sk
                pos = coords
            else:
                bone, weight = p['bone_idx'], 1.0
            vb = build_vertex_44(pos, weight, bone, nrm, uv)
            if vb not in sec_map:
                sec_map[vb] = len(sec)
                sec.append(vb)
            vremap.append(sec_map[vb])
        for a, bb, c in p['tris']:
            if a < len(vremap) and bb < len(vremap) and c < len(vremap):
                ia, ib2, ic = vremap[a], vremap[bb], vremap[c]
                if ia != ib2 and ib2 != ic and ia != ic:
                    ib.append(ia)
                    ib.append(ib2)
                    ib.append(ic)
        part_a.append((a_start, len(sec) - a_start))
        part_b.append((b_start, len(ib) - b_start))
    return sec, ib, part_a, part_b


def decimate(sec, ib, cell, max_sec):
    """Decima por (bone, voxel) para caber en max_sec slots."""
    if isinstance(sec, list):
        sec = b''.join(sec)
    n_orig = len(sec) // 44
    cell_of = {}
    rep_of = {}
    for i in range(n_orig):
        off = i * 44
        bone = u32r(sec[off + 16:off + 20], 0)
        px = struct.unpack('>f', sec[off + 0:off + 4])[0]
        py = struct.unpack('>f', sec[off + 4:off + 8])[0]
        pz = struct.unpack('>f', sec[off + 8:off + 12])[0]
        key = (bone, int(px / cell), int(py / cell), int(pz / cell))
        cell_of[i] = key
        if key not in rep_of:
            rep_of[key] = i
    new_ib = []
    for t in range(0, len(ib) - 2, 3):
        a, b, c = ib[t], ib[t + 1], ib[t + 2]
        if a >= n_orig or b >= n_orig or c >= n_orig:
            continue
        ra, rb, rc = rep_of[cell_of[a]], rep_of[cell_of[b]], rep_of[cell_of[c]]
        if ra == rb or rb == rc or ra == rc:
            continue
        new_ib.append((ra, rb, rc))
    rep_list = []
    rep_idx = {}
    for t in new_ib:
        for v in t:
            if v not in rep_idx:
                rep_idx[v] = len(rep_list)
                rep_list.append(v)
    compact_ib = []
    for t in new_ib:
        compact_ib.append((rep_idx[t[0]], rep_idx[t[1]], rep_idx[t[2]]))
    out_vb = b''.join(sec[r * 44:(r + 1) * 44] for r in rep_list)
    out_ib = []
    for t in compact_ib:
        out_ib.extend(t)
    return out_vb, out_ib, len(rep_list)


def main():
    if len(sys.argv) < 4:
        print('Uso: amo0_to_awo.py <bin_ps2.amo|amb> <bin_hd_plantilla.awo> <out.awo>')
        return
    ps2 = open(sys.argv[1], 'rb').read()
    base = bytearray(open(sys.argv[2], 'rb').read())
    out = sys.argv[3]

    amo0 = 0x40 if ps2[:4] == b'#AMB' else 0
    if ps2[amo0:amo0 + 4] not in (b'#AMO0', b'#AMO'):
        print('No es #AMO0 en 0x%X: %s' % (amo0, ps2[amo0:amo0 + 4]))
        return

    parts, skin_map = parse_ps2_full(ps2, amo0)
    nv = sum(len(p['verts']) for p in parts)
    nt = sum(len(p['tris']) for p in parts)
    print('PS2: %d parts, %d verts expandidos, %d tris reales, skin %d' % (
        len(parts), nv, nt, len(skin_map)))

    sec, ib, part_a, part_b = build_buffers(parts, skin_map)
    print('sin decimar: sec34=%d únicos | IB=%d índices (%d tris)' % (
        len(sec), len(ib), len(ib) // 3))

    # ---- buffers del template ----
    n_awgs = u32r(base, 0x18)
    awg_tbl = u32r(base, 0x1C)
    AWG0 = u32r(base, awg_tbl)
    axes_rel = u32r(base, AWG0 + 0x14)
    arm_root_rel = u32r(base, AWG0 + axes_rel + 0x34)
    arm_root = AWG0 + arm_root_rel
    n_bones = u32r(base, AWG0 + 0x3C)
    arms_zone_end = arm_root + n_bones * 0x14
    sec_rel = u32r(base, AWG0 + 0x28)
    sec_sz = u32r(base, AWG0 + 0x2C)
    post_rel = u32r(base, AWG0 + 0x30)
    post_sz = u32r(base, AWG0 + 0x34)
    sec_abs = AWG0 + sec_rel
    struct_end = AWG0 + sec_rel
    post_abs = AWG0 + post_rel
    max_sec = sec_sz // 44
    max_ib = post_sz // 2
    print('AWG0 @0x%X | arms @0x%X..0x%X | zona desc @0x%X..0x%X' % (
        AWG0, arm_root, arms_zone_end, arms_zone_end, struct_end))
    print('Buffers template: sec34 %d slots | IB %d índices | bin %d B' % (
        max_sec, max_ib, len(base)))

    # ---- decimar para caber en los buffers del template ----
    sec_bytes = b''.join(sec) if isinstance(sec, list) else sec
    cell = 0.01
    while True:
        sec_b, ib_b, n_u = decimate(sec_bytes, ib, cell, max_sec)
        if n_u <= max_sec and len(ib_b) <= max_ib:
            break
        cell *= 1.4
        if cell > 2.0:
            print('ERROR: no cabe ni con cell=%.3f (sec=%d > %d)' % (cell, n_u, max_sec))
            return
    print('decimado cell=%.3f: sec34=%d (max %d) | IB=%d (max %d) | %d tris' % (
        cell, n_u, max_sec, len(ib_b), max_ib, len(ib_b) // 3))
    sec_blob = sec_b if isinstance(sec_b, bytes) else b''.join(sec_b)
    ib = ib_b

    # ---- descriptores: regenerar rangos A/B ----
    # (las partes decimadas ya no mapean 1:1; distribuimos uniformemente
    #  dentro de los buffers reales — enfoque del B3 krillin_rec)
    z = bytearray(base[arms_zone_end:struct_end])
    anchors = sorted(m.start() for m in re.finditer(rb'max \d+ m', z))
    n_desc = len(anchors)
    print('Template: %d descriptores' % n_desc)
    n_sec_f = len(sec_blob) // 44
    if n_desc > 0:
        for k in range(n_desc):
            d = anchors[k] - 0x30
            a_start = (n_sec_f * k) // n_desc
            a_end = (n_sec_f * (k + 1)) // n_desc
            b_start = (len(ib) * k) // n_desc
            b_end = (len(ib) * (k + 1)) // n_desc
            z[d + 0x08:d + 0x0C] = struct.pack('>I', (a_start << 8))
            z[d + 0x0C:d + 0x10] = struct.pack('>I', ((a_end - a_start) << 8))
            z[d + 0x10:d + 0x14] = struct.pack('>I', (b_start << 8))
            z[d + 0x14:d + 0x18] = struct.pack('>I', ((b_end - b_start) << 8) | 1)

    # ---- rellenar EN SU POSICIÓN (tamaño fijo, delta=0) ----
    out_bin = bytearray(base)
    out_bin[sec_abs:sec_abs + len(sec_blob)] = sec_blob
    for i in range(len(sec_blob) // 44, max_sec):
        off = sec_abs + i * 44
        out_bin[off:off + 44] = b'\x00' * 44
    ib_bytes = b''.join(u16(i) for i in ib)
    out_bin[post_abs:post_abs + len(ib_bytes)] = ib_bytes
    for i in range(len(ib), max_ib):
        off = post_abs + i * 2
        out_bin[off:off + 2] = b'\xff\xff'
    out_bin[arms_zone_end:struct_end] = bytes(z)

    open(out, 'wb').write(bytes(out_bin))
    print('Guardado: %s (%d B, delta=0, arms intactos)' % (out, len(out_bin)))


if __name__ == '__main__':
    main()