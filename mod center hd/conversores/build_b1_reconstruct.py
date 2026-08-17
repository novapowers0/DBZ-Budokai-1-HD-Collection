"""Reconstruir un bin HD B1 (#AWO) con la estructura del PS2 (1 AWG por AMG).

Vía validada por el Piccolo (mod test_piccolo_on_tenshinhan que SÍ funcionó):
el port funcional reconstruye el bin con 1 AWG por AMG del personaje origen,
NO inyecta en el template del anfitrión.

Estrategia:
1. Cargar el bin Piccolo HD (funciona) como PLANTILLA estructural (19 AWGs
   con labels, ejes, mesh groups, offsets).
2. Cargar el modelo PS2 origen (Goku SS2, 21 AMGs).
3. Por cada AMG origen, reemplazar la geometría (sec34 + IB) del AWG
   correspondiente de la plantilla.
4. Transformar coords: PS2 guarda coords LOCALES al hueso, HD también.
   Si el esqueleto difiere (GOK vs PIC), transformar world->local del hueso
   destino con inv_rigid. Si coincide, copiar directo (re-layout LE->BE).

Uso:
  python build_b1_reconstruct.py <plantilla_piccolo_hd.awo> <modelo_ps2.amb> <output.bin>
"""
import struct
import sys

U32 = struct.Struct('>I')
F32 = struct.Struct('>f')
U32L = struct.Struct('<I')


def u32r(b, o):
    return U32.unpack_from(b, o)[0]


def f32r(b, o):
    return F32.unpack_from(b, o)[0]


def f32(v):
    return F32.pack(v)


def u32(v):
    return U32.pack(v & 0xFFFFFFFF)


def build_v01(pos, weight, bone, nrm, uv):
    """Layout 44B real del B1: +00 pos3 +12 peso +16 BONE +20 nrm3
    +32 FFFFFFFF +36 blend +40 uv."""
    x, y, z = pos
    nx, ny, nz = nrm
    u, v = uv
    return (f32(x) + f32(y) + f32(z) +
            f32(weight) + u32(bone) +
            f32(nx) + f32(ny) + f32(nz) +
            u32(0xFFFFFFFF) + f32(0.0) + f32(u))


def quat_to_mat(x, y, z, w):
    xx, xy, xz, xw = x * x, x * y, x * z, x * w
    yy, yz, yw = y * y, y * z, y * w
    zz, zw = z * z, z * w
    return [
        [1 - 2 * (yy + zz), 2 * (xy - zw), 2 * (xz + yw)],
        [2 * (xy + zw), 1 - 2 * (xx + zz), 2 * (yz - xw)],
        [2 * (xz - yw), 2 * (yz + xw), 1 - 2 * (xx + yy)],
    ]


def mat_mul(A, B):
    return [[sum(A[i][k] * B[k][j] for k in range(3)) for j in range(3)] for i in range(3)]


def apply_mat(m, p, v):
    return (m[0][0] * v[0] + m[0][1] * v[1] + m[0][2] * v[2] + p[0],
            m[1][0] * v[0] + m[1][1] * v[1] + m[1][2] * v[2] + p[1],
            m[2][0] * v[0] + m[2][1] * v[1] + m[2][2] * v[2] + p[2])


def inv_rigid(M, p):
    Rt = [[M[j][i] for j in range(3)] for i in range(3)]
    tp = [-sum(Rt[i][j] * p[j] for j in range(3)) for i in range(3)]
    return Rt, tp


def build_world_mats_ps2(ps2, amo0=0x40):
    """World mats del modelo PS2 (formato #AMO0/#AMG, LE)."""
    import struct as st
    R32 = st.Struct('<I')
    F32 = st.Struct('<f')
    cnt = R32.unpack_from(ps2, amo0 + 0x10)[0]
    start = R32.unpack_from(ps2, amo0 + 0x14)[0]
    bone_off = {}
    parents = {}
    for bi in range(cnt):
        e = amo0 + start + bi * 32
        bone_table = R32.unpack_from(ps2, e + 4)[0]
        t3 = R32.unpack_from(ps2, e + 0x10)[0]
        pid = R32.unpack_from(ps2, amo0 + t3)[0] + 1 if t3 else 0
        bo = R32.unpack_from(ps2, amo0 + bone_table + 8)[0] if bone_table else 0
        bone_off[bi] = amo0 + bo if bo else 0
        parents[bi] = pid
    cache = {}

    def get_mat(i):
        if i in cache:
            return cache[i]
        b = bone_off[i]
        if not b:
            m = [[1, 0, 0], [0, 1, 0], [0, 0, 1]]
            p = [0, 0, 0]
        else:
            c = [F32.unpack_from(ps2, b + j * 4)[0] for j in range(12)]
            m = quat_to_mat(c[0], c[1], c[2], -c[3])
            p = [c[4], c[5], c[6]]
        pid = parents[i]
        if pid and pid <= cnt:
            pm, pp = get_mat(pid - 1)
            m = mat_mul(pm, m)
            p = [pm[0][0] * p[0] + pm[0][1] * p[1] + pm[0][2] * p[2] + pp[0],
                 pm[1][0] * p[0] + pm[1][1] * p[1] + pm[1][2] * p[2] + pp[1],
                 pm[2][0] * p[0] + pm[2][1] * p[1] + pm[2][2] * p[2] + pp[2]]
        cache[i] = (m, p)
        return m, p

    return {bi: get_mat(bi) for bi in range(cnt)}, parents


def parse_ps2_model(ps2):
    """Extrae AMGs del modelo PS2: lista de dicts con verts/tris/skin."""
    import sys as _s
    _here = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
    _s.path.insert(0, os.path.join(_here, 'parsers', 'lib_ps2'))
    from extract_geometry import PS2Model
    m = PS2Model(ps2)
    amgs = m.amg_offsets()
    model = m
    out = []
    for amg_off in amgs:
        amg0 = m.amo0 + amg_off
        parts = m.mesh_parts(amg0)
        bone_am = struct.unpack('<I', ps2[amg0 + 0x10:amg0 + 0x14])[0]
        label = ''
        if bone_am:
            lo = struct.unpack('<I', ps2[amg0 + 0x1C:amg0 + 0x20])[0]
            label = ps2[amg0 + lo:amg0 + lo + 16].split(b'\x00')[0].decode('latin1', 'ignore')
        out.append({'amg0': amg0, 'bone_am': bone_am, 'label': label,
                    'parts': parts, 'nv': sum(len(p['verts']) for p in parts)})
    return m, out


def main():
    if len(sys.argv) < 4:
        print('Uso: build_b1_reconstruct.py <plantilla_piccolo.awo> <modelo_ps2.amb> <out.bin>')
        return
    tpl = bytearray(open(sys.argv[1], 'rb').read())
    ps2 = open(sys.argv[2], 'rb').read()
    out = sys.argv[3]

    # 1. Analizar la plantilla (bin Piccolo HD funcional)
    n_awg = u32r(tpl, 0x18)
    tbl = u32r(tpl, 0x1C)
    awg_offs = [u32r(tpl, tbl + i * 4) for i in range(n_awg)]
    print('Plantilla: %d AWGs' % n_awg)

    # 2. Analizar el modelo PS2 origen
    model, amgs = parse_ps2_model(ps2)
    print('Modelo PS2: %d AMGs' % len(amgs))
    for i, a in enumerate(amgs):
        print('  AMG%d: %d verts label=%s' % (i, a['nv'], a['label']))

    # 3. Mapeo AMG origen -> AWG plantilla
    #    El cuerpo (AMG0) -> AWG0. Los dedos LHAND/RHAND -> AWGs de dedos.
    #    Las caras -> AWGs de caras. Por tipo + orden.
    tpl_labels = []
    for i, off in enumerate(awg_offs):
        nameoff = u32r(tpl, off + 0x1C)
        lab = tpl[off + nameoff:off + nameoff + 16].split(b'\x00')[0].decode('latin1', 'ignore')
        tpl_labels.append(lab)
    print('Labels plantilla:', tpl_labels)

    # Clasificar AWGs plantilla y AMGs origen
    def classify(label):
        l = label.upper()
        if 'BODY' in l:
            return 'body'
        if 'FACE' in l:
            return 'face'
        if 'LHAND' in l or 'RHAND' in l:
            return 'finger'
        return 'other'

    tpl_by_type = {'body': [], 'face': [], 'finger': [], 'other': []}
    for i, lab in enumerate(tpl_labels):
        tpl_by_type[classify(lab)].append(i)
    src_by_type = {'body': [], 'face': [], 'finger': [], 'other': []}
    for i, a in enumerate(amgs):
        src_by_type[classify(a['label'])].append(i)

    # mapeo: AMG origen -> AWG plantilla
    amg_to_awg = {}
    for typ in ['body', 'finger', 'face', 'other']:
        srcs = src_by_type[typ]
        dsts = tpl_by_type[typ]
        for j, si in enumerate(srcs):
            if j < len(dsts):
                amg_to_awg[si] = dsts[j]
    print('Mapeo AMG->AWG:', amg_to_awg)

    # 4. Para cada AMG, transformar verts y escribir en el AWG destino
    #    Extraer skin (bone por vertice) + world mats del PS2
    mats_ps2, _ = build_world_mats_ps2(ps2, amo0=model.amo0)
    print('World mats PS2: %d' % len(mats_ps2))

    # Mapeo bone origen -> bone PIC por SUFIJO de label (no por prefijo).
    # Funciona para cualquier esqueleto Budokai (GOK_, TSH_, KLL_, JNB_...).
    pic_labels = {}
    AWG0 = awg_offs[0]
    pic_nameoff = u32r(tpl, AWG0 + 0x1C)
    for bi in range(0, 51, 2):
        s = tpl[AWG0 + pic_nameoff + bi * 16: AWG0 + pic_nameoff + bi * 16 + 16]
        s = s.split(b'\x00')[0].decode('latin1', 'ignore')
        if s:
            pic_labels[s] = bi
    gok_labels = {}
    for off in model.amg_offsets():
        amg0 = model.amo0 + off
        bone_am = struct.unpack('<I', ps2[amg0 + 0x10:amg0 + 0x14])[0]
        lo = struct.unpack('<I', ps2[amg0 + 0x1C:amg0 + 0x20])[0]
        for bi in range(bone_am):
            s = ps2[amg0 + lo + bi * 16:amg0 + lo + bi * 16 + 16]
            s = s.split(b'\x00')[0].decode('latin1', 'ignore')
            if s and bi not in gok_labels:
                gok_labels[bi] = s
    # mapeo bone origen -> bone PIC por sufijo
    def label_suffix(lab):
        # XTSH_BODY -> BODY, TSH_WAIST -> WAIST, PIC_L01_LHAND -> L01_LHAND
        parts = lab.split('_')
        if len(parts) >= 3 and parts[1].startswith('L0') or len(parts) >= 3 and parts[1].startswith('M_'):
            return '_'.join(parts[1:])  # L01_LHAND, M_JAW
        if len(parts) >= 2:
            return parts[-1] if parts[-1] in ('BODY', 'NLA', 'NRA', 'HEAD', 'NECK', 'JAW') else '_'.join(parts[1:])
        return lab

    gok_to_pic = {}
    for gidx, glab in gok_labels.items():
        suf = label_suffix(glab)
        matched = 0
        for plab, pidx in pic_labels.items():
            if plab == suf or plab.endswith('_' + suf) or plab.replace('XPIC_', 'PIC_').endswith(suf):
                gok_to_pic[gidx] = pidx
                matched = 1
                break
        if not matched:
            gok_to_pic[gidx] = 0
    # bones IMPARES (sin label): heredan del par vecino
    for bi in range(1, 50):
        if bi in gok_to_pic:
            continue
        for cand in (bi - 1, bi + 1, bi - 2, bi + 2):
            if cand in gok_to_pic:
                gok_to_pic[bi] = gok_to_pic[cand]
                break
        if bi not in gok_to_pic:
            gok_to_pic[bi] = 0
    print('Mapeo origen->PIC: %d bones' % len(gok_to_pic))
    # world mats del Piccolo (de la plantilla HD) por bone PIC
    # Los ejes se detectan por sello 0x9000020C (no por stride fijo).
    pic_mats = {}
    import math as _math
    for off in range(AWG0 + 0x200, AWG0 + 0x2400, 4):
        if off + 0x50 > len(tpl):
            break
        if u32r(tpl, off) != 0x9000020C:
            continue
        o = off - 0x30
        q = [f32r(tpl, o + i * 4) for i in range(4)]
        n = _math.sqrt(sum(v * v for v in q))
        if not (0.99 < n < 1.01):
            continue
        arm = u32r(tpl, o + 0x34)
        if not arm or AWG0 + arm + 20 > len(tpl):
            continue
        bone = u32r(tpl, AWG0 + arm)
        if 0 <= bone <= 51:
            pic_mats[bone] = (quat_to_mat(q[0], q[1], q[2], q[3]),
                              [f32r(tpl, o + 16 + i * 4) for i in range(3)])
    print('World mats PIC: %d' % len(pic_mats))

    # extraer skin por vertice (ch_loc -> bone)
    # Reutilizamos la logica de build_b1_goku_full: mapeo ch_loc por AMG
    skin_map = {}  # (amg_idx, part_idx, vert_idx) -> (bone_ps2, weight, coords_local)
    for amg_idx, a in enumerate(amgs):
        amg0 = a['amg0']
        bone_am = a['bone_am']
        axes_loc = struct.unpack('<I', ps2[amg0 + 0x14:amg0 + 0x18])[0]
        parts = a['parts']
        part_ranges = []
        for pi, p in enumerate(parts):
            md = p['po'] + 0xA0
            vstart = md + 0x20
            part_ranges.append((pi, vstart, len(p['verts']) * 48))
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
                for e in range(ch_len):
                    entry = amg0 + ch_loc + e * 32
                    coords = struct.unpack('<fff', ps2[entry:entry + 12])
                    voff = struct.unpack('<I', ps2[entry + 12:entry + 16])[0]
                    abs_off = amg0 + voff
                    for pi, vstart, vlen in part_ranges:
                        if vstart <= abs_off < vstart + vlen:
                            vi = (abs_off - vstart) // 48
                            skin_map[(amg_idx, pi, vi)] = (bi, weight, coords)
                            break

    # 5. Para cada AWG destino, escribir sec34 + IB
    for amg_idx, awg_idx in amg_to_awg.items():
        a = amgs[amg_idx]
        AWG = awg_offs[awg_idx]
        sec34_rel = u32r(tpl, AWG + 0x28)
        sec34_size = u32r(tpl, AWG + 0x2C)
        ib_rel = u32r(tpl, AWG + 0x30)
        bones_rel = u32r(tpl, AWG + 0x38)
        n_sec = sec34_size // 44
        n_ib = (bones_rel - ib_rel) // 2
        print('AMG%d -> AWG%d: sec34=%d slots, IB=%d idx, label=%s' % (
            amg_idx, awg_idx, n_sec, n_ib, a['label']))

        # construir sec34 del Goku
        sec34 = bytearray(n_sec * 44)
        # los verts del AMG, transformados a local del hueso del AWG destino
        written = 0
        for pi, p in enumerate(a['parts']):
            for vi, v in enumerate(p['verts']):
                sk = skin_map.get((amg_idx, pi, vi))
                if not sk:
                    continue
                bone_ps2, weight, coords_local = sk
                px, py, pz = coords_local
                nx, ny, nz = v['nrm']
                tu, tv = v['uv']
                # bone destino: mapeo GOK->PIC por labels
                bone_dst = gok_to_pic.get(bone_ps2, 0)
                # retargeting: world GOK -> local PIC
                Mg, pg = mats_ps2.get(bone_ps2, ([[1, 0, 0], [0, 1, 0], [0, 0, 1]], [0, 0, 0]))
                Mp, pp = pic_mats.get(bone_dst, (None, None))
                if Mp is None:
                    lx, ly, lz = px, py, pz
                else:
                    wx, wy, wz = apply_mat(Mg, pg, (px, py, pz))
                    iM, ip = inv_rigid(Mp, pp)
                    lx, ly, lz = apply_mat(iM, ip, (wx, wy, wz))
                if written < n_sec:
                    sec34[written * 44:written * 44 + 44] = build_v01(
                        (lx, ly, lz), weight, bone_dst, (nx, ny, nz), (tu, tv))
                    written += 1
        # rellenar el resto con copias
        if written < n_sec and written > 0:
            for i in range(written, n_sec):
                sec34[i * 44:i * 44 + 44] = sec34[(i % written) * 44:(i % written) * 44 + 44]
        elif written == 0:
            # rellenar con verts vacios (bone 0)
            for i in range(n_sec):
                sec34[i * 44:i * 44 + 44] = build_v01((0, 0, 0), 1.0, 0, (0, 1, 0), (0, 0))

        # escribir sec34 en el AWG
        tpl[AWG + sec34_rel:AWG + sec34_rel + len(sec34)] = sec34

        # IB: mantener el IB de la plantilla (los indices 0..n_sec-1 ya apuntan
        # al sec34 nuevo). Si el IB referencia mas verts de los escritos,
        # quedan degenerados pero no crashea.

    with open(out, 'wb') as f:
        f.write(bytes(tpl))
    print('Guardado: %s (%d bytes)' % (out, len(tpl)))


if __name__ == '__main__':
    main()
