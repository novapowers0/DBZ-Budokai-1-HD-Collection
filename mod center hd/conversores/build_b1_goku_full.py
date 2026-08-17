"""Reconstruir un bin HD B1 (#AWO) con geometria de un modelo PS2 + IB real.

Enfoque correcto (validado: Krillin PS2->HD en el proyecto hermano):
- Extraer la geometria del modelo PS2 (vertices + triangulos reales).
- Convertir a world con las matrices de hueso (pose bind).
- Escribir el sec34 (layout 01BD del B1) + reconstruir el IB.
- Mantener la estructura del template HD (labels, materiales, bones).

Uso:
  python build_b1_goku_full.py <template_hd.awo> <modelo_ps2.amb> <output.bin>
"""
import struct
import sys

import os
_here = os.path.dirname(os.path.abspath(__file__))
sys.path.insert(0, os.path.join(_here, '..', 'parsers', 'lib_ps2'))
from extract_geometry import PS2Model
from convert_personaje import SkinData
from pose_matrix import build_world_mats, apply_mat
from extract_hd_mats import build_hd_world_mats, inv_rigid

# Parsers PS2 locales en lib_ps2/ (formato #AMO0/#AMG compartido por
# B1/B2/B3/IW). Ya no dependemos del proyecto B3.


def u32r(data, off):
    return struct.unpack('>I', data[off:off + 4])[0]


def f32(v):
    return struct.pack('>f', v)


def u32(v):
    return struct.pack('>I', v & 0xFFFFFFFF)


def get_hd_labels(awo):
    n = u32r(awo, 0x10)
    labels_off = u32r(awo, 0x24)
    labels = {}
    for bi in range(n):
        s = awo[labels_off + bi * 2 * 16:labels_off + bi * 2 * 16 + 16]
        s = s.split(b'\x00')[0].decode('latin1', 'ignore')
        if s:
            labels[bi] = s
    return labels


def get_goku_labels(ps2):
    model = PS2Model(ps2)
    labels = {}
    for amg_off in model.amg_offsets():
        amg0 = model.amo0 + amg_off
        bone_am = struct.unpack('<I', ps2[amg0 + 0x10:amg0 + 0x14])[0]
        labels_off = struct.unpack('<I', ps2[amg0 + 0x1C:amg0 + 0x20])[0]
        for bi in range(bone_am):
            s = ps2[amg0 + labels_off + bi * 16:amg0 + labels_off + bi * 16 + 16]
            s = s.split(b'\x00')[0].decode('latin1', 'ignore')
            if s and bi not in labels:
                labels[bi] = s
    return labels


def build_mapping(gok_labels, tsh_labels):
    tsh_by_label = {l: i for i, l in tsh_labels.items()}
    mapping = {}
    for gidx, label in gok_labels.items():
        t_label = label.replace('XGOK_', 'X20G_').replace('GOK_', '20G_')
        mapping[gidx] = tsh_by_label.get(t_label, -1)
    manual = {
        0: 0, 1: 1, 2: 1, 3: 38, 4: 44, 5: 45, 6: 45, 7: 46, 8: 46,
        9: 46, 10: 47, 11: 47, 12: 48, 13: 48, 14: 43, 15: 43,
        17: 9, 19: 13, 21: 12, 23: 12, 25: 19, 27: 19, 29: 15,
        31: 16, 33: 16, 35: 20, 37: 23, 39: 23, 41: 24, 43: 25,
    }
    # El skin del Goku usa los bones IMPARES (25, 27, 13, 9...) que NO tienen
    # label en gok_labels. Aplicar el manual SIEMPRE, incluso si el bone no
    # aparece en gok_labels (el skin los usa igual).
    for gidx, target in manual.items():
        mapping[gidx] = target
    return mapping


def build_v01(pos, weight, bone, nrm, uv):
    """Layout 44B real del B1 (RE Piccolo/Tenshinhan nativos, sesión 5):
    +00 pos3 +12 peso(float) +16 BONE(u32) +20 nrm3 +32 FFFFFFFF
    +36 blend(float) +40 uv(float)."""
    x, y, z = pos
    nx, ny, nz = nrm
    u, v = uv
    return (f32(x) + f32(y) + f32(z) +
            f32(weight) +
            u32(bone) +
            f32(nx) + f32(ny) + f32(nz) +
            u32(0xFFFFFFFF) +
            f32(0.0) +
            f32(u))


def main():
    gero_tpl, goku_path, out = sys.argv[1], sys.argv[2], sys.argv[3]
    awo = bytearray(open(gero_tpl, 'rb').read())
    ps2 = open(goku_path, 'rb').read()

    tsh_labels = get_hd_labels(awo)
    gok_labels = get_goku_labels(ps2)
    mapping = build_mapping(gok_labels, tsh_labels)
    mapped = sum(1 for v in mapping.values() if v >= 0)
    print('Mapeo GOK->20G: %d/%d' % (mapped, len(gok_labels)))

    model = PS2Model(ps2)
    amgs = model.amg_offsets()
    mats, parents = build_world_mats(ps2)

    # Mapear skin voff -> (bone_tsh, weight, coords world) usando ch_loc/sb_loc
    # del rig (metodo Model-Rig Extractor v0.9). Esto cubre el 100% del cuerpo
    # (el SkinData solo cubria ~31%).
    # Estructura del rig (por bone): eje +0x34 = arm_ptr, arm +8 = rig_ptr,
    # rig +12 = chunk_amnt, rig+16 + i*32 = chunk:
    #   [weight(4), ch_len(4), ch_loc(4), sb_len(4), sb_loc(4)]
    # ch_loc: entries de 32B, el OFFSET del vertice va en +12 del entry.
    skin_voff = {}
    for amg_off in amgs:
        amg0 = model.amo0 + amg_off
        parts = model.mesh_parts(amg0)
        part_ranges = []
        for pi, p in enumerate(parts):
            md = p['po'] + 0xA0
            vstart = md + 0x20
            part_ranges.append((pi, vstart, len(p['verts']) * 48))
        bone_am = struct.unpack('<I', ps2[amg0 + 0x10:amg0 + 0x14])[0]
        axes_loc = struct.unpack('<I', ps2[amg0 + 0x14:amg0 + 0x18])[0]
        for bi in range(bone_am):
            e0 = amg0 + axes_loc + bi * 80
            p34 = struct.unpack('<I', ps2[e0 + 0x34:e0 + 0x38])[0]
            if not p34:
                continue
            arm = amg0 + p34
            rig_ptr = struct.unpack('<I', ps2[arm + 8:arm + 12])[0]
            if not rig_ptr:
                continue
            r = amg0 + rig_ptr
            chunk_amnt = struct.unpack('<I', ps2[r + 12:r + 16])[0]
            for i in range(chunk_amnt):
                c = r + 16 + i * 32
                weight = struct.unpack('<f', ps2[c:c + 4])[0]
                ch_len = struct.unpack('<I', ps2[c + 4:c + 8])[0]
                ch_loc = struct.unpack('<I', ps2[c + 8:c + 12])[0]
                if not ch_loc:
                    continue
                tsh_bone = mapping.get(bi, -1)
                if tsh_bone < 0:
                    tsh_bone = 0
                m, pos = mats.get(bi, ([[1, 0, 0], [0, 1, 0], [0, 0, 1]], [0, 0, 0]))
                for e in range(ch_len):
                    entry = amg0 + ch_loc + e * 32
                    coords = struct.unpack('<fff', ps2[entry:entry + 12])
                    voff = struct.unpack('<I', ps2[entry + 12:entry + 16])[0]
                    abs_off = amg0 + voff
                    wx, wy, wz = apply_mat(m, pos, coords)
                    for pi, vstart, vlen in part_ranges:
                        if vstart <= abs_off < vstart + vlen:
                            vi = (abs_off - vstart) // 48
                            skin_voff[(amg_off, pi, vi)] = (tsh_bone, weight, (wx, wy, wz))
                            break
    print('Skin voffs mapeados (ch_loc): %d' % len(skin_voff))

    # Extraer vertices + triangulos reales del Goku (submeshes)
    # Cada vertice de la malla -> buscar su skin por proximidad de offset
    all_verts = []  # (pos_ps2, nrm, uv, skin_info)
    all_tris = []   # indices locales

    for amg_off in amgs:
        amg0 = model.amo0 + amg_off
        parts = model.mesh_parts(amg0)
        if not parts:
            continue
        for pi, p in enumerate(parts):
            po = p['po']
            md = po + 0xA0
            sub_verts = []  # verts de este part en orden de submesh
            # Los vertices del part vienen del PS2Model (ya parseados).
            # El skin se mapea por indice del vertice en el part (rel_vi).
            for vi, v in enumerate(p['verts']):
                px, py, pz = v['pos']
                nx, ny, nz = v['nrm']
                tu, tv = v['uv']
                skin_info = skin_voff.get((amg_off, pi, vi))
                if skin_info is None:
                    skin_info = (0, 1.0, (px, py, pz))
                sub_verts.append((px, py, pz, nx, ny, nz, tu, tv, skin_info))
            # Triangulos del part desde los submeshes (headers FaceType)
            pos = md
            base = len(all_verts) + (len(sub_verts) - len(p['verts']))
            vert_cursor = 0  # indice del vertice dentro del part
            while pos + 0x20 < po + 0x8000:
                ft = struct.unpack('<I', ps2[pos + 0x10:pos + 0x14])[0]
                vc = struct.unpack('<I', ps2[pos + 0x14:pos + 0x18])[0]
                if vc == 0 or vc > 0xFFFF:
                    break
                b0 = base + vert_cursor
                if ft == 1:  # strip
                    for i in range(2, vc):
                        f1, f2, f3 = b0 + i - 2, b0 + i - 1, b0 + i
                        if i % 2 == 0:
                            all_tris.append((f1, f3, f2))
                        else:
                            all_tris.append((f1, f2, f3))
                elif ft == 0:  # triplets
                    for i in range(0, vc - 2, 3):
                        all_tris.append((b0 + i, b0 + i + 1, b0 + i + 2))
                vert_cursor += vc
                pos = pos + 0x20 + vc * 48
            all_verts.extend(sub_verts)
    print('Verts totales: %d, Tris: %d' % (len(all_verts), len(all_tris)))

    # Solo usar verts CON skin (bone != 0). Los verts sin skin no tienen world
    # pos correcta -> descartarlos para que todos los slots tengan bones reales.
    skinned_map = {}
    skinned_verts = []
    for vi, v in enumerate(all_verts):
        if v[8][0] != 0:
            skinned_map[vi] = len(skinned_verts)
            skinned_verts.append(v)
    print('Verts con skin (bone != 0): %d de %d' % (len(skinned_verts), len(all_verts)))
    all_verts = skinned_verts
    new_tris = []
    for t in all_tris:
        if t[0] in skinned_map and t[1] in skinned_map and t[2] in skinned_map:
            new_tris.append((skinned_map[t[0]], skinned_map[t[1]], skinned_map[t[2]]))
    all_tris = new_tris
    print('Tris con verts skinned: %d' % len(all_tris))

    # Limites del slot del Gero (necesario para el retargeting y el fill)
    amg_am = u32r(awo, 0x18)
    tbl = u32r(awo, 0x1C)
    offs = [u32r(awo, tbl + i * 4) for i in range(amg_am)]
    AWG0 = offs[0]

    # RETARGETING: world del Goku -> local del hueso del Tenshinhan.
    # El runtime B1 (como el B3) skinnea cada vertice con la matriz del hueso
    # del mesh group (Tenshinhan). Las coords del sec34 deben ser LOCALES al
    # hueso destino: local_tsh = inv_rigid(M_tsh) * world_goku.
    # (AGENTS B3: 'el guest interpreta los verts del origen con los huesos del
    #  anfitrion del arm del mesh group -> masa deforme si no se transforma').
    mats_tsh, _ = build_hd_world_mats(awo, AWG0)
    print('World mats Tenshinhan HD: %d huesos' % len(mats_tsh))

    verts_out = []
    n_unmapped = 0
    for (px, py, pz, nx, ny, nz, tu, tv, skin_info) in all_verts:
        tsh_bone, weight, wpos = skin_info
        wx, wy, wz = wpos
        M3, p3 = mats_tsh.get(tsh_bone, (None, None))
        if M3 is None:
            n_unmapped += 1
            M3 = [[1, 0, 0], [0, 1, 0], [0, 0, 1]]
            p3 = [0.0, 0.0, 0.0]
        iM, ip = inv_rigid(M3, p3)
        lx, ly, lz = apply_mat(iM, ip, (wx, wy, wz))
        verts_out.append(build_v01((lx, ly, lz), weight, tsh_bone,
                                   (nx, ny, nz), (tu, tv)))
    print('Verts convertidos: %d (retarget inv_rigid), sin mapear: %d' % (
        len(verts_out), n_unmapped))
    # Header AWG del B1 (RE Piccolo/Tenshinhan nativos, sesión 5):
    #   +0x28 vb off | +0x2C vb size | +0x30 ib off | +0x34 ib size
    #   +0x38 bones off | +0x3C bones size
    sec34_rel = u32r(awo, AWG0 + 0x28)
    vb2_size = u32r(awo, AWG0 + 0x2C)
    ib_rel = u32r(awo, AWG0 + 0x30)
    bones_rel = u32r(awo, AWG0 + 0x38)
    n_sec = vb2_size // 44
    n_ib_max = (bones_rel - ib_rel) // 2
    max_tri = n_ib_max // 3
    print('Slot: sec34=%d slots, IB=%d indices (%d tris max)' % (n_sec, n_ib_max, max_tri))

    # Decimar tris a max_tri (eliminar los de mayor area)
    # area por posicion transformada
    def vpos(vi):
        return verts_out[vi][0:12]
    if len(all_tris) > max_tri:
        import math
        tris = list(all_tris)
        while len(tris) > max_tri:
            def area(t):
                a = struct.unpack('>3f', vpos(t[0] % len(verts_out)))[0:3]
                b = struct.unpack('>3f', vpos(t[1] % len(verts_out)))[0:3]
                c = struct.unpack('>3f', vpos(t[2] % len(verts_out)))[0:3]
                return abs((b[0]-a[0])*(c[1]-a[1]) - (b[1]-a[1])*(c[0]-a[0]))
            wi, wa = 0, -1
            step = max(1, len(tris)//2000)
            for i in range(0, len(tris), step):
                ar = area(tris[i])
                if ar > wa:
                    wa, wi = ar, i
            del tris[wi]
        all_tris = tris
        print('Tris decimados a: %d' % len(all_tris))

    # Compactar vertices a MAXIMO n_sec slots usando decimacion por voxel
    # sobre las posiciones WORLD originales, INCLUYENDO el bone en la clave
    # (para no colapsar huesos distintos en la misma celda).
    world_pos = [v[8][2] for v in all_verts]
    world_bone = [v[8][0] for v in all_verts]  # bone TSH de cada vert
    import math
    cell = 0.06
    cell_map = {}
    unique_idx = []
    remap = {}
    for vi in range(len(world_pos)):
        wx, wy, wz = world_pos[vi]
        if math.isnan(wx) or math.isnan(wy) or math.isnan(wz):
            wx, wy, wz = 0.0, 0.0, 0.0
        key = (int(wx / cell), int(wy / cell), int(wz / cell), world_bone[vi])
        if key not in cell_map:
            cell_map[key] = len(unique_idx)
            unique_idx.append(vi)
        remap[vi] = cell_map[key]
    print('Verts unicos world (cell=%.2f, por bone): %d' % (cell, len(unique_idx)))
    verts_out = [verts_out[vi] for vi in unique_idx]
    if len(verts_out) > n_sec:
        verts_out = verts_out[:n_sec]
        print('  truncados a %d slots' % n_sec)

    # Remapear tris con los indices unicos
    new_tris = []
    for t in all_tris:
        a, b, c = remap[t[0]], remap[t[1]], remap[t[2]]
        if a != b and b != c and a != c:
            new_tris.append((a, b, c))
    all_tris = new_tris
    if len(all_tris) > max_tri:
        all_tris = all_tris[:max_tri]
    print('Tris finales: %d (max %d)' % (len(all_tris), max_tri))

    # Escribir sec34 + IB en el bin
    sec34_abs = AWG0 + sec34_rel
    ib_abs = AWG0 + ib_rel

    # Llenar sec34: escribir SOLO verts con bone valido (0-51). Los slots
    # restantes se rellenan con copias de verts validos (sin dejar basura).
    # Cada slot debe tener UN vertice con su bone real (no fallback 0).
    def bone_of(v44):
        return struct.unpack('>I', v44[16:20])[0]

    valid = [v for v in verts_out if bone_of(v) <= 51]
    print('Verts validos para el sec34: %d de %d' % (len(valid), len(verts_out)))
    if len(valid) == 0:
        raise SystemExit('ERROR: 0 verts validos, abortando')
    order = sorted(range(len(valid)), key=lambda i: bone_of(valid[i]))
    n_fill = min(len(valid), n_sec)
    for i in range(n_fill):
        awo[sec34_abs + i * 44:sec34_abs + (i + 1) * 44] = valid[order[i]]
    # rellenar el resto con verts validos (ciclando)
    for i in range(n_fill, n_sec):
        awo[sec34_abs + i * 44:sec34_abs + (i + 1) * 44] = valid[order[i % len(valid)]]

    # IB: escribir indices (clip a n_ib_max y rellenar a los conteos FIJOS
    # con 0xFFFF — el guest exige conteos exactos como B3).
    ib_data = b''
    for t in all_tris:
        a, b, c = t[0], t[1], t[2]
        ib_data += struct.pack('>HHH', a, b, c)
    n_ib = len(ib_data) // 2
    if n_ib > n_ib_max:
        ib_data = ib_data[:n_ib_max * 2]
        n_ib = n_ib_max
    elif n_ib < n_ib_max:
        ib_data = ib_data + b'\xff\xff' * (n_ib_max - n_ib)
        n_ib = n_ib_max
    print('IB indices: %d (fijo a %d)' % (n_ib, n_ib_max))
    awo[ib_abs:ib_abs + len(ib_data)] = ib_data

    with open(out, 'wb') as f:
        f.write(bytes(awo))
    print('Guardado: %s (%d bytes)' % (out, len(awo)))


if __name__ == '__main__':
    main()
