"""Port B3 HD -> B1 HD v4 - v2 + RETARGETING DE BONES POR MATRICES BIND.

EXTIENDE port_b3_to_b1_v2.py (que queda intacto como referencia validada).
A diferencia del v3 (que solo cambiaba el bone index y estiraba la geometria),
el v4 TRANSFORMA las coordenadas locales de los vertices huerfanos al espacio
del bone destino usando las matrices bind world (retarget_hd.retarget_local).

PROBLEMA (validado en runtime):
  - v2: el pelo del Gero queda congelado (bones HAIR sin animacion en TSH calvo)
        y deforma el brazo.
  - v3: cambiar solo el bone index (HAIR->HEAD) SIN transformar coords estira
        la geometria porque los vertices estan en coords LOCALES al bone HAIR.

SOLUCION (v4):
  local_head = inv(M_head_world) * M_hair_world * local_hair
  donde M_*_world se componen recorriendo la jerarquia de ejes del AWO.

Mapeo por defecto (configurable con --map 'ORIGEN:DESTINO'):
  X20G_HAIR1 -> 20G_HEAD
  X20G_HAIR2 -> 20G_HEAD
  X20G_HAIR3 -> 20G_HEAD
  X20G_SHD3  -> 20G_NECK
  X20G_M_DTEETH -> 20G_HEAD

Uso:
  python port_b3_to_b1_v4.py <awo_b3.bin> <azt_b3.bin> <out.awo> <out_azt.bin> [--map 'X20G_HAIR1:20G_HEAD' ...] [--flatten] [--remap <ref>]
"""
import struct
import sys
import os

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
import port_b3_to_b1_v2 as v2

DEFAULT_MAP = {
    'X20G_HAIR1': '20G_HEAD',
    'X20G_HAIR2': '20G_HEAD',
    'X20G_HAIR3': '20G_HEAD',
    'X20G_SHD3': '20G_NECK',
    'X20G_M_DTEETH': '20G_HEAD',
}

# jerarquia canonica Budokai: parent de cada label (por sufijo)
# BODY -> WAIST -> STMC -> CHEST -> [LCHN->LARMROT->LARM1->LARM2->LHANDROT->L00_LHAND, RCHN->RARM..., NECK->HEAD...]
#                 |-> LLEGROT->LLEG1->LLEG2->LFOOT1->LFOOT2
#                 |-> RLEGROT->RLEG1->RLEG2->RFOOT1->RFOOT2
HIERARCHY = {
    'BODY': None,
    'WAIST': 'BODY',
    'STMC': 'WAIST',
    'CHEST': 'STMC',
    'LCHN': 'CHEST', 'LARMROT': 'LCHN', 'LARM1': 'LARMROT', 'LARM2': 'LARM1',
    'LHANDROT': 'LARM2', 'L00_LHAND': 'LHANDROT',
    'RCHN': 'CHEST', 'RARMROT': 'RCHN', 'RARM1': 'RARMROT', 'RARM2': 'RARM1',
    'RHANDROT': 'RARM2', 'L00_RHAND': 'RHANDROT',
    'NECK': 'CHEST', 'HEAD': 'NECK',
    'NH': 'HEAD', 'M_JAW': 'HEAD',
    'M_LMOUTH2': 'M_JAW', 'M_RMOUTH2': 'M_JAW', 'M_DTEETH': 'M_JAW',
    'M_LMOUTH1': 'M_JAW', 'M_RMOUTH1': 'M_JAW', 'M_UTEETH': 'M_JAW',
    'L00_FACE': 'HEAD', 'HAIR1': 'HEAD', 'HAIR2': 'HEAD', 'HAIR3': 'HEAD',
    'SHD3': 'HEAD',
    'LLEGROT': 'WAIST', 'LLEG1': 'LLEGROT', 'LLEG2': 'LLEG1',
    'LFOOT1': 'LLEG2', 'LFOOT2': 'LFOOT1',
    'RLEGROT': 'WAIST', 'RLEG1': 'RLEGROT', 'RLEG2': 'RLEG1',
    'RFOOT1': 'RLEG2', 'RFOOT2': 'RFOOT1',
}


def labels_hd(b):
    n = v2.u32r(b, 0x10)
    off = v2.u32r(b, 0x24)
    out = {}
    for bi in range(n):
        s = b[off + bi * 32: off + bi * 32 + 32].split(b'\x00')[0].decode('latin1', 'ignore')
        if s:
            out[bi] = s
    return out


def bone_suffix(label):
    """Extrae el sufijo del label quitando el prefijo de personaje (X20G_/20G_)."""
    if '_' in label:
        parts = label.split('_')
        # prefijos como X20G o 20G
        if len(parts) >= 2 and (parts[0].startswith(('X', 'TSH', 'GOK', 'PIC', 'VEG')) or parts[0].isdigit()):
            return '_'.join(parts[1:])
    return label


def parent_label(label):
    suf = bone_suffix(label)
    p = HIERARCHY.get(suf)
    if p is None:
        return None
    # reconstruir el prefijo del padre usando el mismo prefijo del hijo
    pref = label[:len(label) - len(suf)]
    return pref + p


def leer_ejes(awo):
    """Lee los ejes del AWG0: {label: {quat, pos, sello, off}}."""
    amg = v2.u32r(awo, 0x18)
    tbl = v2.u32r(awo, 0x1C)
    awg0 = v2.u32r(awo, tbl)
    hdr_off = v2.u32r(awo, awg0 + 0x20)
    hdr_cnt = v2.u32r(awo, awg0 + 0x24)
    hdr_abs = awg0 + hdr_off
    mesh_end = hdr_abs + hdr_cnt * 0x50
    sec = awg0 + v2.u32r(awo, awg0 + 0x28)

    labels = labels_hd(awo)
    ejes = {}
    idx = 0
    for off in range(mesh_end, sec - 0x50 + 1, 0x50):
        sello = v2.u32r(awo, off + 0x30)
        if sello in (0x6000020F, 0x9000020C, 0x8000020C):
            quat = struct.unpack('>4f', awo[off:off + 16])
            pos = struct.unpack('>3f', awo[off + 16:off + 28])
            label = labels.get(idx, 'bone_%d' % idx)
            ejes[label] = {'quat': quat, 'pos': pos, 'sello': sello, 'off': off}
            idx += 1
    return ejes


# --- matrices bind world ---
def quat_to_mat(x, y, z, w):
    xx, xy, xz, xw = x * x, x * y, x * z, x * w
    yy, yz, yw = y * y, y * z, y * w
    zz, zw = z * z, z * w
    return [
        [1 - 2 * (yy + zz), 2 * (xy - zw), 2 * (xz + yw)],
        [2 * (xy + zw), 1 - 2 * (xx + zz), 2 * (yz - xw)],
        [2 * (xz - yw), 2 * (yz + xw), 1 - 2 * (xx + yy)],
    ]


def mat_apply_rot(M, v):
    return (M[0][0] * v[0] + M[0][1] * v[1] + M[0][2] * v[2],
            M[1][0] * v[0] + M[1][1] * v[1] + M[1][2] * v[2],
            M[2][0] * v[0] + M[2][1] * v[1] + M[2][2] * v[2])


def mat_transpose(M):
    return [[M[j][i] for j in range(3)] for i in range(3)]


def mat_mul(A, B):
    return [[sum(A[i][k] * B[k][j] for k in range(3)) for j in range(3)] for i in range(3)]


def mat_inv(M):
    return mat_transpose(M)


def build_world_mats(ejes):
    """Compone las matrices bind world (R, p) de cada bone por jerarquia."""
    # quat local -> matriz local 3x3, pos local
    local = {}
    for label, e in ejes.items():
        R = quat_to_mat(e['quat'][0], e['quat'][1], e['quat'][2], e['quat'][3])
        local[label] = (R, e['pos'])
    # world: M_world = M_parent * M_local (rotacion + traslacion)
    world = {}
    # resolver recursivo con memo
    import functools
    @functools.lru_cache(None)
    def w(label):
        R, p = local[label]
        par = parent_label(label)
        if par is None or par not in local:
            return (R, p)
        Rw, pw = w(par)
        # M = Rw * R ; p_world = Rw*p + pw
        Rtot = mat_mul(Rw, R)
        ptot = (Rw[0][0] * p[0] + Rw[0][1] * p[1] + Rw[0][2] * p[2] + pw[0],
                Rw[1][0] * p[0] + Rw[1][1] * p[1] + Rw[1][2] * p[2] + pw[1],
                Rw[2][0] * p[0] + Rw[2][1] * p[1] + Rw[2][2] * p[2] + pw[2])
        return (Rtot, ptot)
    for label in ejes:
        world[label] = w(label)
    return world


def retarget_local_coords(world, src_label, dst_label, local_src):
    """local_dst = inv(Rd) * (Rs * local_src + ps - pd)  (solo rotacion+pos)."""
    Rs, ps = world[src_label]
    Rd, pd = world[dst_label]
    # world del vertice origen
    wx = Rs[0][0] * local_src[0] + Rs[0][1] * local_src[1] + Rs[0][2] * local_src[2] + ps[0]
    wy = Rs[1][0] * local_src[0] + Rs[1][1] * local_src[1] + Rs[1][2] * local_src[2] + ps[1]
    wz = Rs[2][0] * local_src[0] + Rs[2][1] * local_src[1] + Rs[2][2] * local_src[2] + ps[2]
    # a espacio local del destino: inv(Rd) * (world - pd)
    iRd = mat_inv(Rd)
    lx = iRd[0][0] * (wx - pd[0]) + iRd[0][1] * (wy - pd[1]) + iRd[0][2] * (wz - pd[2])
    ly = iRd[1][0] * (wx - pd[0]) + iRd[1][1] * (wy - pd[1]) + iRd[1][2] * (wz - pd[2])
    lz = iRd[2][0] * (wx - pd[0]) + iRd[2][1] * (wy - pd[1]) + iRd[2][2] * (wz - pd[2])
    return (lx, ly, lz)


def remap_bones_retarget(awo, ejes, world, bone_map):
    """Reasigna vertices huerfanos al bone destino transformando coords."""
    amg = v2.u32r(awo, 0x18)
    tbl = v2.u32r(awo, 0x1C)
    labels = labels_hd(awo)
    idx_by_label = {l: i for i, l in labels.items()}
    remap = {}
    for lsrc, ldst in bone_map.items():
        if lsrc in idx_by_label and ldst in idx_by_label and lsrc in world and ldst in world:
            remap[lsrc] = (idx_by_label[lsrc], idx_by_label[ldst], ldst)
    print('Retarget de bones (origen -> destino):')
    for lsrc, (si, di, ldst) in sorted(remap.items()):
        print('  %s (%d) -> %s (%d)' % (lsrc, si, ldst, di))

    n_verts = 0
    for i in range(amg):
        awg = v2.u32r(awo, tbl + i * 4)
        if awg + 0x40 > len(awo):
            continue
        sec = awg + v2.u32r(awo, awg + 0x28)
        sec_sz = v2.u32r(awo, awg + 0x2C)
        for v in range(sec_sz // 44):
            q = sec + v * 44
            bone = v2.u32r(awo, q + 16)
            lab = labels.get(bone, '')
            if lab in remap:
                x, y, z = struct.unpack('>3f', awo[q:q + 12])
                lx, ly, lz = retarget_local_coords(world, lab, remap[lab][2], (x, y, z))
                struct.pack_into('>3f', awo, q, lx, ly, lz)
                struct.pack_into('>I', awo, q + 16, remap[lab][1])
                n_verts += 1
    return n_verts


def main():
    args = sys.argv[1:]
    if len(args) < 4:
        print("Uso: port_b3_to_b1_v4.py <awo_b3.bin> <azt_b3.bin> <out.awo> <out_azt.bin> [--map ORIG:DEST ...] [--flatten] [--remap ref]")
        return
    do_flatten = '--flatten' in args
    do_remap_ref = '--remap' in args
    remap_ref = None
    if do_remap_ref:
        ri = args.index('--remap')
        if ri + 1 < len(args):
            remap_ref = args[ri + 1]
            args = args[:ri] + args[ri + 2:]
    custom_map = {}
    while '--map' in args:
        mi = args.index('--map')
        if mi + 1 < len(args):
            kv = args[mi + 1]
            if ':' in kv:
                src, dst = kv.split(':', 1)
                custom_map[src.strip()] = dst.strip()
            args = args[:mi] + args[mi + 2:]

    awo_path, azt_path, out, out_azt = args[0], args[1], args[2], args[3]
    awo = bytearray(open(awo_path, 'rb').read())
    azt = open(azt_path, 'rb').read()

    print('=== Pipeline v2 (validado) ===')
    import tempfile
    tmpdir = os.path.join(os.environ.get('TEMP', '/tmp'), 'opencode', 'v4_work')
    os.makedirs(tmpdir, exist_ok=True)
    tmp_awo = os.path.join(tmpdir, 'port_v2.awo')
    tmp_azt = os.path.join(tmpdir, 'port_v2.azt')
    v2_args = [awo_path, azt_path, tmp_awo, tmp_azt]
    if do_flatten:
        v2_args.append('--flatten')
    if do_remap_ref and remap_ref:
        v2_args += ['--remap', remap_ref]
    import subprocess
    v2_script = os.path.join(os.path.dirname(os.path.abspath(__file__)), 'port_b3_to_b1_v2.py')
    r = subprocess.run([sys.executable, v2_script] + v2_args, capture_output=True)
    print(r.stdout.decode('utf-8', 'ignore'))
    if r.returncode != 0:
        print('ERROR v2:', r.stderr.decode('utf-8', 'ignore'))
        return
    awo = bytearray(open(tmp_awo, 'rb').read())
    azt = open(tmp_azt, 'rb').read()

    # retargeting (usa el AWO ORIGINAL para las matrices bind, antes del v2)
    awo_orig = bytearray(open(awo_path, 'rb').read())
    ejes = leer_ejes(awo_orig)
    world = build_world_mats(ejes)

    bone_map = dict(DEFAULT_MAP)
    bone_map.update(custom_map)
    print('=== Retargeting de bones por matrices bind (v4) ===')
    nv = remap_bones_retarget(awo, ejes, world, bone_map)
    print('Retarget: %d vertices transformados' % nv)

    open(out, 'wb').write(bytes(awo))
    open(out_azt, 'wb').write(azt)
    print('Guardado: %s (%d B) + %s (%d B)' % (out, len(awo), out_azt, len(azt)))


if __name__ == '__main__':
    main()