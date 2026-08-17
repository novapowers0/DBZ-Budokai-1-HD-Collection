"""Port B3 HD -> B1 HD v3 — v2 + REMAPEO DE BONES POR LABEL.

EXTIENDE port_b3_to_b1_v2.py (que queda intacto como referencia validada).
Añade el re-mapeo de bones que no existen en el esqueleto del personaje
anfitrión (p.ej. pelo -> HEAD) para evitar deformaciones por bones congelados.

PROBLEMA que resuelve (validado en runtime con el Gero B3):
  El runtime B1 anima el esqueleto del ANFITRIÓN (el #ACM del slot). Los bones
  del AWO portado que EXISTEN en el anfitrión por label -> se animan bien.
  Los bones que NO existen (X20G_HAIR1/2/3, X20G_M_DTEETH) -> quedan en pose
  bind y deforman (el pelo del Gero "se come el brazo" en Tenshinhan calvo).

SOLUCIÓN:
  Reasignar los vértices y arms de los bones huérfanos a un bone del anfitrión
  con label similar (pelo -> HEAD, dientes -> JAW, ...). El pelo se anima con
  la cabeza en vez de quedar congelado.

Mapeo por defecto (configurable con --map 'ORIGEN:DESTINO'):
  X20G_HAIR1 -> 20G_HEAD    (o el bone *HEAD del anfitrión)
  X20G_HAIR2 -> 20G_HEAD
  X20G_HAIR3 -> 20G_HEAD
  X20G_SHD3  -> 20G_NECK
  *DTEETH    -> *HEAD

IMPORTANTE: el mapeo usa la tabla de bones del PROPIO AWO (índices B3), NO
reindexa a la tabla del anfitrión. El runtime usa la tabla del bin instalado.

Uso:
  python port_b3_to_b1_v3.py <awo_b3.bin> <azt_b3.bin> <out.awo> <out_azt.bin> [--map 'X20G_HAIR1:20G_HEAD' ...] [--flatten] [--remap <ref.b1>]
"""
import struct
import sys
import os

# Reutiliza la logica del v2 (validada)
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
import port_b3_to_b1_v2 as v2

# Mapeo por defecto: bones del modelo que no existen en el anfitrion -> bone padre
DEFAULT_MAP = {
    'X20G_HAIR1': '20G_HEAD',
    'X20G_HAIR2': '20G_HEAD',
    'X20G_HAIR3': '20G_HEAD',
    'X20G_SHD3': '20G_NECK',
    'X20G_M_DTEETH': '20G_HEAD',
}


def remap_bones(awo, bone_map_labels):
    """Reasigna los vertices y arms de bones huerfanos a bones padre.

    bone_map_labels: dict {label_origen: label_destino} (labels del PROPIO AWO).
    Devuelve (n_verts_remap, n_arms_remap).
    """
    # indices de la tabla de bones del AWO
    n = v2.u32r(awo, 0x10)
    off = v2.u32r(awo, 0x24)
    labels = {}
    for bi in range(n):
        s = awo[off + bi * 32: off + bi * 32 + 32].split(b'\x00')[0].decode('latin1', 'ignore')
        if s:
            labels[bi] = s

    # resolver indices: origen -> indice, destino -> indice
    idx_by_label = {l: i for i, l in labels.items()}
    # mapeo origen(indice) -> destino(indice); solo si ambos existen
    remap = {}
    for lsrc, ldst in bone_map_labels.items():
        if lsrc in idx_by_label and ldst in idx_by_label:
            remap[idx_by_label[lsrc]] = idx_by_label[ldst]
    if not remap:
        print('AVISO: ningun mapeo de bones aplicado (labels no encontrados)')
        return 0, 0

    print('Remap de bones (indice_origen -> indice_destino):')
    for src, dst in sorted(remap.items()):
        print('  %2d (%s) -> %2d (%s)' % (src, labels[src], dst, labels[dst]))

    amg_am = v2.u32r(awo, 0x18)
    amg_tbl = v2.u32r(awo, 0x1C)
    n_verts = n_arms = 0

    for i in range(amg_am):
        awg = v2.u32r(awo, amg_tbl + i * 4)
        if awg + 0x40 > len(awo):
            continue
        # vertices (+16)
        sec_rel = v2.u32r(awo, awg + 0x28)
        sec_sz = v2.u32r(awo, awg + 0x2C)
        sec = awg + sec_rel
        for v in range(sec_sz // 44):
            q = sec + v * 44
            bone = v2.u32r(awo, q + 16)
            if bone in remap:
                struct.pack_into('>I', awo, q + 16, remap[bone])
                n_verts += 1
        # arms (mesh-ref blocks 0x9000020C/0x8000020C -> arm [bone,...])
        for off in range(awg, sec, 4):
            sv = v2.u32r(awo, off)
            if sv in (0x9000020C, 0x8000020C):
                arm_ptr = v2.u32r(awo, off + 4)
                arm_abs = awg + arm_ptr
                if arm_abs + 4 <= len(awo):
                    bone = v2.u32r(awo, arm_abs)
                    if bone in remap:
                        struct.pack_into('>I', awo, arm_abs, remap[bone])
                        n_arms += 1
    return n_verts, n_arms


def main():
    args = sys.argv[1:]
    if len(args) < 4:
        print('Uso: port_b3_to_b1_v3.py <awo_b3.bin> <azt_b3.bin> <out.awo> <out_azt.bin> [--map "ORIG:DEST" ...] [--flatten] [--remap <ref>]')
        return

    # extraer opciones
    do_flatten = '--flatten' in args
    do_remap_ref = '--remap' in args
    remap_ref = None
    if do_remap_ref:
        ri = args.index('--remap')
        if ri + 1 < len(args):
            remap_ref = args[ri + 1]
            args = args[:ri] + args[ri + 2:]

    # mapeos custom --map
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

    # 1. Pipeline v2 (flag, type2, materiales, u34, alpha AZT)
    print('=== Pipeline v2 (validado) ===')
    import tempfile
    tmpdir = os.path.join(os.environ.get('TEMP', '/tmp'), 'opencode', 'v3_work')
    os.makedirs(tmpdir, exist_ok=True)
    tmp_awo = os.path.join(tmpdir, 'port_v2.awo')
    tmp_azt = os.path.join(tmpdir, 'port_v2.azt')
    v2_args = [awo_path, azt_path, tmp_awo, tmp_azt]
    if do_flatten:
        v2_args.append('--flatten')
    if do_remap_ref and remap_ref:
        v2_args += ['--remap', remap_ref]
    # ejecutar v2 como subproceso para no mezclar mains
    import subprocess
    v2_script = os.path.join(os.path.dirname(os.path.abspath(__file__)), 'port_b3_to_b1_v2.py')
    r = subprocess.run([sys.executable, v2_script] + v2_args, capture_output=True)
    print(r.stdout.decode('utf-8', 'ignore'))
    if r.returncode != 0:
        print('ERROR v2:', r.stderr.decode('utf-8', 'ignore'))
        return
    awo = bytearray(open(tmp_awo, 'rb').read())
    azt = open(tmp_azt, 'rb').read()

    # 2. Remapeo de bones por label (v3)
    bone_map = dict(DEFAULT_MAP)
    bone_map.update(custom_map)
    print('=== Remapeo de bones por label (v3) ===')
    nv, na = remap_bones(awo, bone_map)
    print('Remap: %d vertices, %d arms' % (nv, na))

    open(out, 'wb').write(bytes(awo))
    open(out_azt, 'wb').write(azt)
    print('Guardado: %s (%d B) + %s (%d B)' % (out, len(awo), out_azt, len(azt)))


if __name__ == '__main__':
    main()