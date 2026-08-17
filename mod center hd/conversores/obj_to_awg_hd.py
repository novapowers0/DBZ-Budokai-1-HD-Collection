"""OBJ to AWG HD — Generar un bin #AWO HD B1 desde un modelo PS2.

Vía validada: el bin HD debe tener su mesh group coherente con la geometría.
La estrategia correcta es usar como BASE un bin nativo del MISMO personaje
(su mesh group ya es coherente) y reemplazar SOLO la geometría (sec34),
transformando las coords del origen al espacio de los huesos del destino.

Esto funciona para el mismo personaje entre juegos (Tenshinhan B2→B1 HD):
- El mesh group del TSH B1 HD nativo es coherente (funciona en el juego)
- Los huesos son los mismos (mismo personaje, orden distinto)
- Solo transformamos cada vértice: local_dest = inv(bind_dest) * bind_src * local_src
  usando el retargeting align_joint para esqueletos con rotaciones distintas.

Uso:
  python obj_to_awg_hd.py <bin_hd_base.awo> <modelo_ps2.amb> <output.bin>
"""
import struct
import sys

U32 = struct.Struct('>I')
F32 = struct.Struct('>f')


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


# ---- helpers de matriz (reutilizar de lib_ps2) ----
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


def build_world_mats_ps2(ps2, amo0=0):
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


def build_hd_world_mats(awo, awg=0):
    """World mats del HD (de los mesh-ref blocks / ejes). Detecta TODOS los
    sellos de eje (mesh, rig, transición, shadow), no solo 0x9000020C."""
    import math
    mats = {}
    ejes = {}  # rel_off -> (bone, parent)
    # sellos válidos de eje
    sellos_ok = (0x9000020C, 0x8000020C, 0x1000020C, 0x6000020F,
                 0x9000020E, 0x8000020E, 0x9800020E, 0x90000208,
                 0x80000208, 0x10000208, 0x204)
    for off in range(awg + 0x200, awg + 0x3000, 4):
        if off + 0x50 > len(awo):
            break
        s = u32r(awo, off)
        if s not in sellos_ok:
            continue
        e = off - 0x30  # inicio del bloque (80B)
        if e < awg:
            continue
        q = [f32r(awo, e + i * 4) for i in range(4)]
        n = math.sqrt(sum(v * v for v in q))
        if not (0.99 < n < 1.01):
            continue
        arm = u32r(awo, e + 0x34)
        parent = u32r(awo, e + 0x40)
        bone = -1
        if arm and awg + arm + 20 <= len(awo):
            bone = u32r(awo, awg + arm)
        ejes[e - awg] = {'bone': bone, 'parent': parent, 'q': q,
                         'pos': [f32r(awo, e + 16 + i * 4) for i in range(3)]}

    # world mats por recorrido jerárquico (parent -> raíz)
    cache = {}

    def world_mat(rel):
        if rel in cache:
            return cache[rel]
        d = ejes.get(rel)
        if not d:
            cache[rel] = None
            return None
        m = quat_to_mat(d['q'][0], d['q'][1], d['q'][2], d['q'][3])
        p = list(d['pos'])
        pr = d['parent']
        if pr:
            pw = world_mat(pr)
            if not pw:
                # buscar eje cercano
                for r2, d2 in ejes.items():
                    if abs(r2 - pr) <= 0x18:
                        pw = world_mat(r2)
                        if pw:
                            break
            if pw:
                pm, pp = pw
                m = mat_mul(pm, m)
                p = [pm[0][0] * p[0] + pm[0][1] * p[1] + pm[0][2] * p[2] + pp[0],
                     pm[1][0] * p[0] + pm[1][1] * p[1] + pm[1][2] * p[2] + pp[1],
                     pm[2][0] * p[0] + pm[2][1] * p[1] + pm[2][2] * p[2] + pp[2]]
        cache[rel] = (m, p)
        return m, p

    for rel, d in ejes.items():
        bi = d['bone']
        if bi < 0:
            continue
        wm = world_mat(rel)
        if wm:
            mats[bi] = wm
    return mats


def parse_ps2_model(ps2):
    """Extrae AMGs del modelo PS2: lista de dicts con verts/tris/skin."""
    import os as _os
    import sys as _s
    _here = _os.path.dirname(_os.path.abspath(__file__))
    _s.path.insert(0, _os.path.join(_here, '..', 'parsers', 'lib_ps2'))
    from extract_geometry import PS2Model
    m = PS2Model(ps2)
    amgs = m.amg_offsets()
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
        print('Uso: obj_to_awg_hd.py <bin_hd_base.awo> <modelo_ps2.amb> <out.bin>')
        return
    base = bytearray(open(sys.argv[1], 'rb').read())
    ps2 = open(sys.argv[2], 'rb').read()
    out = sys.argv[3]

    # 1. Labels del bin HD base (mismo personaje) y del modelo PS2
    def labels_hd(b):
        n = u32r(b, 0x10)
        off = u32r(b, 0x24)
        out = {}
        for bi in range(n):
            s = b[off + bi * 32: off + bi * 32 + 32].split(b'\x00')[0].decode('latin1', 'ignore')
            if s:
                out[bi] = s
        return out

    model, amgs = parse_ps2_model(ps2)
    base_labels = labels_hd(base)
    ps2_labels = {}
    for off in model.amg_offsets():
        amg0 = model.amo0 + off
        bone_am = struct.unpack('<I', ps2[amg0 + 0x10:amg0 + 0x14])[0]
        lo = struct.unpack('<I', ps2[amg0 + 0x1C:amg0 + 0x20])[0]
        for bi in range(bone_am):
            s = ps2[amg0 + lo + bi * 16: amg0 + lo + bi * 16 + 16]
            s = s.split(b'\x00')[0].decode('latin1', 'ignore')
            if s and bi not in ps2_labels:
                ps2_labels[bi] = s

    # 2. Mapa de bones PS2 -> HD por label
    base_by_label = {l: i for i, l in base_labels.items()}
    bone_map = {}
    for ps2i, lab in ps2_labels.items():
        # normalizar sufijo
        suf = lab.split('_', 1)[1] if '_' in lab else lab
        matched = 0
        for blab, bidx in base_by_label.items():
            if blab.endswith(suf) or blab.replace('XTSH_', 'TSH_').endswith(suf):
                bone_map[ps2i] = bidx
                matched = 1
                break
        if not matched:
            bone_map[ps2i] = 0
    # impares heredan del par vecino
    for bi in range(1, 50):
        if bi in bone_map:
            continue
        for cand in (bi - 1, bi + 1, bi - 2, bi + 2):
            if cand in bone_map:
                bone_map[bi] = bone_map[cand]
                break
        if bi not in bone_map:
            bone_map[bi] = 0
    print('Mapa bones PS2->HD: %d' % len(bone_map))

    # 3. World mats de ambos
    mats_src, _ = build_world_mats_ps2(ps2, amo0=model.amo0)
    AWG0 = u32r(base, u32r(base, 0x1C))
    mats_dst = build_hd_world_mats(base, AWG0)
    print('Mats: src=%d dst=%d' % (len(mats_src), len(mats_dst)))

    # 4. Extraer skin del PS2 (bone, weight, coords locales) por vertice
    skin_map = {}  # (amg_idx, part_idx, vert_idx) -> (bone_ps2, weight, coords)
    for amg_idx, a in enumerate(amgs):
        amg0 = a['amg0']
        axes_loc = struct.unpack('<I', ps2[amg0 + 0x14:amg0 + 0x18])[0]
        parts = a['parts']
        part_ranges = []
        for pi, p in enumerate(parts):
            md = p['po'] + 0xA0
            vstart = md + 0x20
            part_ranges.append((pi, vstart, len(p['verts']) * 48))
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
                            skin_map[(amg_idx, pi, vi)] = (bi, weight, coords)
                            break

    # 5. Construir sec34 del bin base: MANTENER el sec34 nativo (su mesh group
    #    y orden de slots es coherente) y SOLO reemplazar las coords locales
    #    de cada slot con las del vertice PS2 correspondiente por bone.
    #    El mesh group nativo dibuja cada slot con su bone; si ponemos la
    #    geometria PS2 del mismo hueso en ese slot, el IB conecta bien.
    sec_rel = u32r(base, AWG0 + 0x28)
    sec_sz = u32r(base, AWG0 + 0x2C)
    sec = AWG0 + sec_rel
    n_sec = sec_sz // 44
    print('sec34 base: %d slots' % n_sec)

    # -- preparar verts PS2 por bone HD (coords world del skin con mats_src) --
    # El cuerpo del HD esta "baked" en el bone 0 (raiz): sus slots usan coords
    # world. Por eso para el bone 0 usamos TODOS los verts PS2 (pool global).
    import math
    ps2_by_bone = {}  # bone_dst -> lista de (wx, wy, wz, weight, nrm, uv, coords)
    all_ps2_world = []  # pool global (para el bone 0 / cuerpo)
    a = amgs[0]
    for pi, p in enumerate(a['parts']):
        for vi, v in enumerate(p['verts']):
            sk = skin_map.get((0, pi, vi))
            if not sk:
                continue
            bone_ps2, weight, coords = sk
            bone_dst = bone_map.get(bone_ps2, 0)
            Ms, ps_ = mats_src.get(bone_ps2, (None, None))
            if Ms is not None:
                wx, wy, wz = apply_mat(Ms, ps_, coords)
            else:
                wx, wy, wz = coords
            item = (wx, wy, wz, weight, v['nrm'], v['uv'], coords, bone_dst)
            ps2_by_bone.setdefault(bone_dst, []).append(item)
            all_ps2_world.append(item)
    print('Verts PS2 por bone HD: %d (pool global: %d)' % (
        sum(len(v) for v in ps2_by_bone.values()), len(all_ps2_world)))

    # -- world mats HD por bone para transformar world->local del hueso destino --
    # mats_dst ya calculado en el paso 3 (build_hd_world_mats)

    # -- rellenar slot a slot (ATAJO v8): sec34 nativo + vecinos PS2 con umbral --
    # Se preserva el sec34 nativo (orden + mesh group coherentes) y SOLO se
    # sustituyen las coords locales de cada slot por el vecino world PS2 mas
    # cercano. El bone del slot se mantiene (es del mesh group nativo).
    # Las UVs/normales se mantienen del nativo (que ya van a los sitios bien).
    #
    # Mejora v8 (reduce poligonos agrandados):
    #  1. UMBRAL: si el vecino PS2 mas cercano esta a > UMBRAL unidades, se
    #     DEJAN las coords nativas del slot (que ya son un cuerpo correcto).
    #     Asi los slots mal mapeados no crean triangulos gigantes.
    #  2. POOL RESTRINGIDO por bone: el bone 0 (cuerpo baked) usa TODOS los
    #     verts PS2 world; los demas bones usan solo los de su mismo hueso
    #     (para extremidades), sin penalizacion (solo restriccion).
    #  3. DECIMACION voxel del pool: evita que muchos slots mapeen al MISMO
    #     vecino (triangulos degenerados con area ~0).
    import math
    UMBRAL = 1.5  # unidades: vecino PS2 mas lejos que esto -> mantener nativo
    VOXEL = 0.08  # decimar el pool PS2 (celda de rejilla)

    # decimar pool global por voxel
    cell = VOXEL
    seen_cells = set()
    pool_global = []
    for (wx, wy, wz, weight, nrm, uv, coords, pb) in all_ps2_world:
        key = (int(wx / cell), int(wy / cell), int(wz / cell), pb)
        if key in seen_cells:
            continue
        seen_cells.add(key)
        pool_global.append((wx, wy, wz, weight, nrm, uv, coords, pb))
    print('Pool global decimado: %d (de %d)' % (len(pool_global), len(all_ps2_world)))

    # pool por bone (decimado)
    pool_by_bone = {}
    for item in pool_global:
        pool_by_bone.setdefault(item[7], []).append(item)

    n_replaced = 0
    n_native = 0
    n_nobone = 0
    for i in range(n_sec):
        d = base[sec + i * 44:sec + (i + 1) * 44]
        bone_dst = struct.unpack('>I', d[16:20])[0]
        # pool: bone 0 (cuerpo) usa global; demas bones usan solo su hueso
        if bone_dst == 0:
            pool = pool_global
        else:
            pool = pool_by_bone.get(bone_dst, [])
        if not pool:
            n_nobone += 1
            continue
        # world del slot nativo (coords locales nativas + mat del hueso)
        M, p = mats_dst.get(bone_dst, (None, None))
        nx, ny, nz = struct.unpack('>3f', d[0:12])
        if M is not None:
            swx, swy, swz = apply_mat(M, p, (nx, ny, nz))
        else:
            swx, swy, swz = nx, ny, nz
        # vecino PS2 world mas cercano
        best = None
        bd = 1e18
        for (wx, wy, wz, weight, nrm, uv, coords, pb) in pool:
            dd = (swx - wx) ** 2 + (swy - wy) ** 2 + (swz - wz) ** 2
            if dd < bd:
                bd = dd
                best = (wx, wy, wz, weight, nrm, uv, coords)
        if best is None:
            n_nobone += 1
            continue
        dist = math.sqrt(bd)
        if dist > UMBRAL:
            # vecino demasiado lejos: mantener coords nativas (cuerpo correcto)
            n_native += 1
            continue
        wx, wy, wz, weight, nrm, uv, coords = best
        # coords world del PS2 -> local del hueso nativo del slot (inv_rigid)
        if M is not None:
            iM, ip = inv_rigid(M, p)
            lx, ly, lz = apply_mat(iM, ip, (wx, wy, wz))
        else:
            lx, ly, lz = wx, wy, wz
        # escribir SOLO las coords (mantener weight/bone/uv/nrm nativos)
        base[sec + i * 44:sec + i * 44 + 12] = struct.pack('>3f', lx, ly, lz)
        n_replaced += 1
    print('Slots: reemplazados=%d nativos(mal mapeado)=%d sin-pool=%d (total %d)' % (
        n_replaced, n_native, n_nobone, n_sec))

    open(out, 'wb').write(bytes(base))
    print('Guardado: %s (%d bytes)' % (out, len(base)))


def _to_local(M, p, world):
    """world -> local del hueso (inv_rigid). M es 3x3 rotacion, p es 3x1 pos."""
    # transpuesta de la rotacion (rigida)
    dx = world[0] - p[0]; dy = world[1] - p[1]; dz = world[2] - p[2]
    return (M[0][0] * dx + M[1][0] * dy + M[2][0] * dz,
            M[0][1] * dx + M[1][1] * dy + M[2][1] * dz,
            M[0][2] * dx + M[1][2] * dy + M[2][2] * dz)


if __name__ == '__main__':
    main()
