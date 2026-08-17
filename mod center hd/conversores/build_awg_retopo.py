"""Retopologia del AWG0: reconstruir sec34 + IB con la topologia real del PS2.

La leccion de la sesion 6: las manos son perfectas porque sus AWGs (sec34+IB)
son nativos y coherentes. El AWG0 (cuerpo) necesita lo mismo: un sec34+IB
reconstruido con la topologia del PS2, en vez de rellenar slots arbitrarios.

Pipeline:
  1. Extraer la topologia del AMG0 del PS2 (verts + tris por part) con
     parse_ps2_mesh (faceType 0=tripletes, 1=strips).
  2. Construir el sec34 HD (44B/vert) con los verts PS2 en el orden de parts,
     cada vert con su bone (del skin) y las UVs/nrm del PS2.
  3. Construir el IB HD con los triangulos PS2 (indices con offset de part).
  4. Reemplazar sec34+IB en el AWG0 del bin base (mantener labels/ejes).
  5. Actualizar los sizes del header AWG0.

Uso:
  python build_awg_retopo.py <bin_hd_base.awo> <modelo_ps2.amo> <out.bin>
"""
import struct
import sys
import os as _os
import sys as _s

_here = _os.path.dirname(_os.path.abspath(__file__))
_s.path.insert(0, _here)
_s.path.insert(0, _os.path.join(_here, '..', 'parsers', 'lib_ps2'))


def u32r(b, o):
    return struct.unpack('>I', b[o:o + 4])[0]


def build_vert(pos, bone, weight, nrm, uv):
    """Layout 44B HD: pos3 + peso + bone + nrm3 + FFFFFFFF + uv.x + uv.y."""
    return struct.pack('>3ffI3fIff', pos[0], pos[1], pos[2], weight, bone,
                       nrm[0], nrm[1], nrm[2], 0xFFFFFFFF, uv[0], uv[1])


def main():
    base = bytearray(open(sys.argv[1], 'rb').read())
    ps2 = open(sys.argv[2], 'rb').read()
    out = sys.argv[3]

    import parse_ps2_mesh as pm
    import extract_geometry as eg
    import obj_to_awg_hd as oaw

    # ---- 1. AMG0 del PS2 (cuerpo) via obj_to_awg_hd (validado) ----
    model, amgs = oaw.parse_ps2_model(ps2)
    a = amgs[0]  # AMG0 = BODY
    print('PS2 AMG0 %s: %d verts, %d parts' % (a['label'], a['nv'], len(a['parts'])))

    # ---- 2. Topologia (tris) via parse_ps2_mesh ----
    amg0_off = model.amg_offsets()[0]
    _, tris, parts = pm.parse_amg(ps2, amg0_off, model.amo0)
    print('Topologia PS2: %d tris, %d parts' % (len(tris), len(parts)))

    # ---- 3. skin_map (bone/weight por vert de malla) via oaw ----
    # reusar la logica del oaw paso 4
    def build_skin_map():
        skin_map = {}
        amg0 = a['amg0']
        axes_loc = struct.unpack('<I', ps2[amg0 + 0x14:amg0 + 0x18])[0]
        part_ranges = []
        for pi, p in enumerate(a['parts']):
            md = p['po'] + 0xA0
            part_ranges.append((pi, md + 0x20, len(p['verts']) * 48))
        for bi in range(a['bone_am']):
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
                for e in range(ch_len):
                    entry = amg0 + ch_loc + e * 32
                    coords = struct.unpack('<fff', ps2[entry:entry + 12])
                    voff = struct.unpack('<I', ps2[entry + 12:entry + 16])[0]
                    abs_off = amg0 + voff
                    for pi, vstart, vlen in part_ranges:
                        if vstart <= abs_off < vstart + vlen:
                            vi = (abs_off - vstart) // 48
                            skin_map[(0, pi, vi)] = (bi, weight, coords)
                            break
        return skin_map

    skin_map = build_skin_map()
    print('skin_map: %d' % len(skin_map))

    # ---- 4. Bone HD por vert (re-mapeo por label) ----
    # labels HD y PS2
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
    ps2_labels = {}
    for off in model.amg_offsets():
        amg0 = model.amo0 + off
        bone_am = struct.unpack('<I', ps2[amg0 + 0x10:amg0 + 0x14])[0]
        lo = struct.unpack('<I', ps2[amg0 + 0x1C:amg0 + 0x20])[0]
        for bi in range(bone_am):
            s = ps2[amg0 + lo + bi * 16: amg0 + lo + bi * 16 + 16].split(b'\x00')[0].decode('latin1', 'ignore')
            if s and bi not in ps2_labels:
                ps2_labels[bi] = s
    base_by_label = {l: i for i, l in base_labels.items()}
    bone_map = {}
    for ps2i, lab in ps2_labels.items():
        suf = lab.split('_', 1)[1] if '_' in lab else lab
        matched = 0
        for blab, bidx in base_by_label.items():
            if blab.endswith(suf) or blab.replace('XTSH_', 'TSH_').endswith(suf):
                bone_map[ps2i] = bidx
                matched = 1
                break
        if not matched:
            bone_map[ps2i] = 0
    for bi in range(1, 50):
        if bi in bone_map:
            continue
        for cand in (bi - 1, bi + 1, bi - 2, bi + 2):
            if cand in bone_map:
                bone_map[bi] = bone_map[cand]
                break
        if bi not in bone_map:
            bone_map[bi] = 0
    print('bone_map: %d' % len(bone_map))

    # ---- 5. Construir sec34 + IB ----
    # verts por part (orden del AMG0). Cada vert: pos (malla, world), nrm, uv.
    # bone: del skin_map (bone_ps2) -> bone_map -> HD.
    sec34 = bytearray()
    offset_global = 0
    vert_offsets = []  # (part_idx, global_start) para el IB

    # Recolectar verts con su part de origen (orden por part)
    rich_verts = []  # (pos, nrm, uv, bone_ps2, weight)
    for pi, p in enumerate(a['parts']):
        part_start = len(rich_verts)
        for vi, v in enumerate(p['verts']):
            sk = skin_map.get((0, pi, vi))
            if sk:
                bone_ps2, weight, _ = sk
            else:
                bone_ps2, weight = 0, 1.0
            rich_verts.append((tuple(v['pos']), tuple(v['nrm']), tuple(v['uv']), bone_ps2, weight))
        vert_offsets.append((pi, part_start, len(p['verts'])))

    # sec34
    for pos, nrm, uv, bone_ps2, weight in rich_verts:
        bone_dst = bone_map.get(bone_ps2, 0)
        sec34 += build_vert(pos, bone_dst, weight, nrm, uv)
    print('sec34: %d verts' % len(rich_verts))

    # IB: los tris de parse_amg ya tienen indices globales (offset aplicado).
    # Verificar que los indices globales de parse_amg correspondan al orden de rich_verts.
    # parse_amg concatena verts en el MISMO orden que mesh_parts (mismo parser interno),
    # asi que los indices globales coinciden con rich_verts.
    ib = bytearray()
    for t0, t1, t2 in tris:
        if t0 < len(rich_verts) and t1 < len(rich_verts) and t2 < len(rich_verts):
            ib += struct.pack('>HHH', t0, t1, t2)
    print('IB: %d indices (%d tris)' % (len(ib) // 2, len(ib) // 6))

    # ---- 6. Reemplazar en el bin base (reempaquetar dentro del AWG0) ----
    # El AWG0 tiene las zonas: [labels/mesh/ejes/arms] [sec34] [IB] [bones].
    # sec34 e IB nuevos pueden cambiar de tamano. Reempaquetamos:
    #   sec34 nuevo en sec_abs
    #   IB nuevo en sec_abs + len(sec34)
    #   si el IB nuevo termina despues del IB nativo, desplazamos lo que sigue
    #   (bones y el resto del bin) y actualizamos ib_rel.
    AWG0 = u32r(base, u32r(base, 0x1C))
    sec_rel = u32r(base, AWG0 + 0x28)
    sec_abs = AWG0 + sec_rel
    ib_rel = u32r(base, AWG0 + 0x30)
    ib_abs = AWG0 + ib_rel
    bones_rel = u32r(base, AWG0 + 0x38)
    bones_abs = AWG0 + bones_rel

    new_sec_sz = len(sec34)
    new_ib_sz = len(ib)
    new_ib_rel = sec_rel + new_sec_sz
    new_ib_abs = AWG0 + new_ib_rel
    new_ib_end = new_ib_abs + new_ib_sz

    # cuanto se desplazan las zonas posteriores (bones + resto del bin)
    old_ib_end = ib_abs + u32r(base, AWG0 + 0x34)
    shift = new_ib_end - old_ib_end
    if shift > 0:
        # mover todo lo que sigue al IB nativo hacia adelante
        tail = bytes(base[old_ib_end:])
        base[new_ib_end:new_ib_end + len(tail)] = tail
    # escribir sec34 e IB nuevos
    base[sec_abs:sec_abs + new_sec_sz] = sec34
    base[new_ib_abs:new_ib_abs + new_ib_sz] = ib
    # actualizar offsets y sizes en el header
    struct.pack_into('>I', base, AWG0 + 0x2C, new_sec_sz)        # size vertices
    struct.pack_into('>I', base, AWG0 + 0x30, new_ib_rel)        # ib offset
    struct.pack_into('>I', base, AWG0 + 0x34, new_ib_sz)         # size faces
    if shift > 0:
        struct.pack_into('>I', base, AWG0 + 0x38, bones_rel + shift)  # bones offset

    open(out, 'wb').write(bytes(base))
    print('Guardado: %s (%d bytes)' % (out, len(base)))


if __name__ == '__main__':
    main()
