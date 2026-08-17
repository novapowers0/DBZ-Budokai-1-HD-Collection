"""Port de personaje DISTINTO (Gohan Kai B2) al slot Tenshinhan B1 HD.

Retargeting por label+align (NO matching por vecino, que asume geometria
similar). Pipeline:
  1. Extraer verts skin del GOH (coords locales al hueso GOH + bone GOH).
  2. world = bind_GOH[bone] * local (rot + pos).
  3. alinear rotacion entre esqueletos (align_joint): world_aligned.
  4. local_tsh = inv(bind_TSH[bone_tsh]) * (world_aligned - pos_tsh).
  5. Rellenar el sec34 del TSH: para cada slot (bone_tsh), usar el vert GOH
     del bone mapeado (por label), transformado.

El mesh group del TSH (sec34 nativo + IB) se mantiene intacto: el runtime
dibuja la topologia del TSH; solo cambian las coords de cada slot.

Uso:
  python port_personaje_a_tsh.py <bin_hd_tsh.awo> <modelo_ps2.amb> <out.bin>
"""
import struct
import sys
import os as _os
import sys as _s

_here = _os.path.dirname(_os.path.abspath(__file__))
_s.path.insert(0, _here)
_s.path.insert(0, _os.path.join(_here, '..', 'parsers', 'lib_ps2'))
import obj_to_awg_hd as oaw
from obj_to_awg_hd import u32r, f32r, build_world_mats_ps2, build_hd_world_mats, apply_mat, inv_rigid
import retarget_hd as rh


def u32l(b, o):
    return struct.unpack('<I', b[o:o + 4])[0]


def f32l(b, o):
    return struct.unpack('<f', b[o:o + 4])[0]


def main():
    base = bytearray(open(sys.argv[1], 'rb').read())
    ps2bin = open(sys.argv[2], 'rb').read()
    out = sys.argv[3]

    # AMB PS2: el AMO0 esta en 0x40 si es #AMB; si es #AMO directo, en 0
    if ps2bin[0:4] == b'#AMB':
        ps2 = ps2bin[0x40:]
    else:
        ps2 = ps2bin

    # ---- 1. Modelo GOH (AMG0) y mundo mats ----
    model, amgs = oaw.parse_ps2_model(ps2)
    a = amgs[0]
    print('GOH AMG0 %s: bone_am=%d nv=%d parts=%d' % (a['label'], a['bone_am'], a['nv'], len(a['parts'])))
    mats_src, _ = build_world_mats_ps2(ps2, amo0=model.amo0)
    print('mats GOH: %d' % len(mats_src))

    # ---- 2. Labels HD (TSH) y mapeo por label ----
    def labels_hd(b):
        n = u32r(b, 0x10)
        off = u32r(b, 0x24)
        out = {}
        for bi in range(n):
            s = b[off + bi * 32: off + bi * 32 + 32].split(b'\x00')[0].decode('latin1', 'ignore')
            if s:
                out[bi] = s
        return out

    base_labels = labels_hd(base)
    base_by_label = {l: i for i, l in base_labels.items()}

    # labels del PS2 por bone (AMG0 y resto)
    ps2_labels = {}
    for off in model.amg_offsets():
        amg0 = model.amo0 + off
        bone_am = u32l(ps2, amg0 + 0x10)
        lo = u32l(ps2, amg0 + 0x1C)
        for bi in range(bone_am):
            s = ps2[amg0 + lo + bi * 16: amg0 + lo + bi * 16 + 16].split(b'\x00')[0].decode('latin1', 'ignore')
            if s and bi not in ps2_labels:
                ps2_labels[bi] = s

    bone_map = {}  # bone GOH -> bone TSH
    for ps2i, lab in ps2_labels.items():
        suf = lab.split('_', 1)[1] if '_' in lab else lab
        suf = suf.replace('XGHL_', '').replace('GHL_', '')
        matched = 0
        for blab, bidx in base_by_label.items():
            b_suf = blab.replace('XTSH_', '').replace('TSH_', '')
            if b_suf == suf or blab.endswith(suf):
                bone_map[ps2i] = bidx
                matched = 1
                break
        if not matched:
            bone_map[ps2i] = -1  # sin match (pelo, dientes) -> no portar
    # herencia de pares para huesos sin label
    for bi in range(0, 60):
        if bi in bone_map:
            continue
        for cand in (bi - 1, bi + 1, bi - 2, bi + 2):
            if cand in bone_map and bone_map[cand] >= 0:
                bone_map[bi] = bone_map[cand]
                break
        if bi not in bone_map:
            bone_map[bi] = -1
    print('bone_map GOH->TSH: %d mapeados' % sum(1 for v in bone_map.values() if v >= 0))

    # ---- 3. Mats TSH (destino) ----
    AWG0 = u32r(base, u32r(base, 0x1C))
    mats_dst = build_hd_world_mats(base, AWG0)
    print('mats TSH: %d' % len(mats_dst))

    # ---- 4. Skin GOH: coords locales por vertice ----
    skin_map = {}  # (part, vert) -> (bone_goh, weight, coords)
    amg0 = a['amg0']
    axes_loc = u32l(ps2, amg0 + 0x14)
    part_ranges = []
    for pi, p in enumerate(a['parts']):
        md = p['po'] + 0xA0
        part_ranges.append((pi, md + 0x20, len(p['verts']) * 48))
    for bi in range(a['bone_am']):
        e0 = amg0 + axes_loc + bi * 80
        p34 = u32l(ps2, e0 + 0x34)
        if not p34:
            continue
        arm = amg0 + p34
        rig_ptr = u32l(ps2, arm + 8)
        if not rig_ptr:
            continue
        r = amg0 + rig_ptr
        chunk_amnt = u32l(ps2, r + 12)
        for i in range(chunk_amnt):
            c = r + 16 + i * 32
            weight = f32l(ps2, c)
            ch_len = u32l(ps2, c + 4)
            ch_loc = u32l(ps2, c + 8)
            if not ch_loc:
                continue
            for e in range(ch_len):
                entry = amg0 + ch_loc + e * 32
                coords = struct.unpack('<fff', ps2[entry:entry + 12])
                voff = u32l(ps2, entry + 12)
                abs_off = amg0 + voff
                for pi, vstart, vlen in part_ranges:
                    if vstart <= abs_off < vstart + vlen:
                        vi = (abs_off - vstart) // 48
                        skin_map[(pi, vi)] = (bi, weight, coords)
                        break
    print('skin GOH: %d verts' % len(skin_map))

    # ---- 5. Retargeting: verts GOH transformados al espacio TSH ----
    # verts_tsh[bone_tsh] = lista de (local_tsh, weight, nrm, uv)
    # Transformacion explicita (corrige retarget_local que no resta pos_dest):
    #   world_src = R_src * local_src + pos_src
    #   world_align = R_align * world_src        (align_joint de rotaciones)
    #   local_dst = R_dst^T * (world_align - pos_dst)
    verts_tsh = {}
    for pi, p in enumerate(a['parts']):
        for vi, v in enumerate(p['verts']):
            sk = skin_map.get((pi, vi))
            if not sk:
                continue
            bone_goh, weight, coords = sk
            bone_tsh = bone_map.get(bone_goh, -1)
            if bone_tsh < 0:
                continue
            Ms, ps = mats_src.get(bone_goh, (None, None))
            M3, p3 = mats_dst.get(bone_tsh, (None, None))
            if Ms is None or M3 is None:
                continue
            # world del vertice GOH (local -> world del hueso GOH)
            wx, wy, wz = apply_mat(Ms, ps, coords)
            # alinear rotacion entre esqueletos (GOH -> TSH)
            R = rh.quat_to_mat(*rh.align_bone_pair(Ms, M3))
            vx = R[0][0] * wx + R[0][1] * wy + R[0][2] * wz
            vy = R[1][0] * wx + R[1][1] * wy + R[1][2] * wz
            vz = R[2][0] * wx + R[2][1] * wy + R[2][2] * wz
            # local del hueso TSH (world -> local, restando pos_dst)
            iM = rh.mat_inv(M3)
            lx = iM[0][0] * (vx - p3[0]) + iM[0][1] * (vy - p3[1]) + iM[0][2] * (vz - p3[2])
            ly = iM[1][0] * (vx - p3[0]) + iM[1][1] * (vy - p3[1]) + iM[1][2] * (vz - p3[2])
            lz = iM[2][0] * (vx - p3[0]) + iM[2][1] * (vy - p3[1]) + iM[2][2] * (vz - p3[2])
            verts_tsh.setdefault(bone_tsh, []).append(
                ((lx, ly, lz), weight, v['nrm'], v['uv']))
    print('verts retargeteados por bone TSH: %d' % sum(len(v) for v in verts_tsh.values()))

    # ---- 6. Rellenar el sec34 del TSH ----
    sec_rel = u32r(base, AWG0 + 0x28)
    sec_sz = u32r(base, AWG0 + 0x2C)
    sec = AWG0 + sec_rel
    n_sec = sec_sz // 44
    print('sec34 base: %d slots' % n_sec)

    # para cada slot del sec34 (bone_tsh), si hay verts GOH de ese bone, usar el
    # primero disponible (o el mas cercano en coords world).
    import math
    n_replaced = 0
    n_native = 0
    n_nobone = 0
    for i in range(n_sec):
        d = base[sec + i * 44:sec + (i + 1) * 44]
        bone_tsh = struct.unpack('>I', d[16:20])[0]
        pool = verts_tsh.get(bone_tsh, [])
        if not pool:
            n_native += 1  # sin verts GOH de ese hueso -> mantener nativo
            continue
        # elegir el vert GOH mas cercano (en coords world) al slot nativo
        M, p = mats_dst.get(bone_tsh, (None, None))
        nx, ny, nz = struct.unpack('>3f', d[0:12])
        if M is not None:
            swx, swy, swz = apply_mat(M, p, (nx, ny, nz))
        else:
            swx, swy, swz = nx, ny, nz
        best = None
        bd = 1e18
        for (local_tsh, weight, nrm, uv) in pool:
            # world del vert GOH (transformado al espacio TSH)
            if M is not None:
                wx, wy, wz = apply_mat(M, p, local_tsh)
            else:
                wx, wy, wz = local_tsh
            dd = (swx - wx) ** 2 + (swy - wy) ** 2 + (swz - wz) ** 2
            if dd < bd:
                bd = dd
                best = (local_tsh, weight, nrm, uv)
        if best is None:
            n_nobone += 1
            continue
        local_tsh, weight, nrm, uv = best
        base[sec + i * 44:sec + i * 44 + 12] = struct.pack('>3f', *local_tsh)
        n_replaced += 1
    print('Slots: reemplazados=%d nativo=%d sin-pool=%d (total %d)' % (
        n_replaced, n_native, n_nobone, n_sec))

    open(out, 'wb').write(bytes(base))
    print('Guardado: %s (%d bytes)' % (out, len(base)))


if __name__ == '__main__':
    main()
