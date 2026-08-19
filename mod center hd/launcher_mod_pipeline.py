"""Orquestador para el launcher: catalogo de personajes + ports/swaps.

Copyright (c) NovaPowers. Released under the MIT License.
Firmado por NovaPowers.

Unifica los pipelines CLI ya validados para que el launcher C++ pueda:
  - catalog: escanear los AFS (B1 data_sp.afs y B3 data_cmn.afs) y generar un
    catalogo de personajes en un archivo de texto simple (characters.cat).
  - swap: model swap B1->B1 (swap_b1.py).
  - port: port B3 HD -> B1 HD (install_b3_to_b1.py + extract_amb_awo.py).

Formato characters.cat (una linea por modelo/traje, '#' = comentario):
  juego|label|nombre|variante|jugable|nota|main|slot_geom|slot_tex|slot_acm|slot_csk|verts|awgs
  juego: B1 o B3
  main: 1 = fila principal (destino valido), 0 = traje/variante extra
  slot_geom: entrada AFS geom (B1) o AMB bin (B3)
  slot_tex:  entrada AFS tex
  variante:  traje/transformacion ('' en la fila principal)

Uso:
  python launcher_mod_pipeline.py catalog [--b1 <afs>] [--b3 <afs>] [--out <file>]
  python launcher_mod_pipeline.py swap --origen <label|bin> --dest <slot> [--tex <slot>] [--mod <name>]
  python launcher_mod_pipeline.py port --b3 <label> [--bin <idx>] --dest <slot> --tex <slot> [--mod <name>]
"""
import argparse
import os
import struct
import subprocess
import sys

HERE = os.path.dirname(os.path.abspath(__file__))
ROOT = os.path.abspath(os.path.join(HERE, '..'))
SWAPS = os.path.join(HERE, 'swaps')
CONV = os.path.join(HERE, 'conversores')
sys.path.insert(0, SWAPS)
sys.path.insert(0, CONV)
sys.path.insert(0, HERE)

import swap_b1  # noqa: E402
import characters_db  # noqa: E402
import paths  # noqa: E402

U32 = struct.Struct('>I')


def u32r(b, o):
    return U32.unpack_from(b, o)[0]


# ---------------------------------------------------------------------------
# Nombres legibles por codigo (characters_db.py)
# ---------------------------------------------------------------------------
def code_of_label(label):
    """'XGOK_BODY' -> 'GOK'; 'XFRZ_BODY_1' -> 'FRZ'; '20G_FACE' -> '20G_FACE'."""
    prefix = label.split('_')[0]
    if prefix.startswith('X'):
        return prefix[1:]
    return prefix


def lookup(game, label):
    """Devuelve (nombre, variante, jugable, nota) o (None, '', None, '').

    Prioriza el label completo sin la X (ej. '20G_FACE' -> 'Solo cara') antes
    de caer al primer token ('20G' -> 'Cuerpo'). Solo reconoce codigos en
    characters_db; los demas (efectos/escenarios) devuelven (None, ...).
    """
    table = characters_db.B1 if game == 'B1' else characters_db.PS2
    full = label[1:] if label.startswith('X') else label
    if full in table:
        return table[full]
    code = code_of_label(label)
    if code in table:
        return table[code]
    return (None, '', None, '')


def lookup_b3_bin(bin_idx):
    """Resuelve un bin B3 en la tabla (clave = bin REAL del data_cmn.afs)."""
    entry = characters_db.B3.get(bin_idx)
    if entry:
        return entry
    # bins de animacion/aura/efecto: no son modelos, devolver None
    return (None, '', None, '')


# Los AFS por defecto de cada juego.
# B1: los modelos de personaje viven en CUALQUIER data_*.afs del juego
# (data_us, data_sp, data_fr, data_en, data_ge, data_it) — todos comparten la
# misma numeracion de bins (2575 entradas). Se elige el primero que exista,
# priorizando data_us.afs.
B1_AFS_NAMES = ('data_us.afs', 'data_sp.afs', 'data_fr.afs',
                'data_en.afs', 'data_ge.afs', 'data_it.afs')


def find_b1_afs(region_dir):
    """Primer data_*.afs de personaje existente en un dir de region (o None)."""
    for name in B1_AFS_NAMES:
        p = os.path.join(region_dir, name)
        if os.path.exists(p):
            return p
    return None


def default_b1_afs():
    return paths.find_b1_afs()


def default_b3_afs():
    # B3: los modelos viven en data_cmn.afs. Se detecta el directorio del B3
    # de forma portable (paths.py: DBZ3_ROOT o el proyecto hermano junto a este).
    return paths.find_b3_afs()


def catalog_path():
    return os.path.join(HERE, 'cache', 'characters.cat')


def cat_rows():
    """Lee characters.cat y devuelve lista de (label, geom, tex) de los B1."""
    rows = []
    p = catalog_path()
    if not os.path.isfile(p):
        return rows
    with open(p, encoding='utf-8') as f:
        for line in f:
            if not line.startswith('B1|'):
                continue
            parts = line.rstrip('\n').split('|')
            if len(parts) >= 9 and parts[7].isdigit() and parts[8].isdigit():
                rows.append((parts[1], int(parts[7]), int(parts[8])))
    return rows


def pairs_for_label(label):
    """Todos los pares (geom, tex) de un label B1 (todos sus trajes)."""
    return [(g, t) for l, g, t in cat_rows() if l == label]


def pairs_arg(pairs):
    return ','.join('%d:%d' % p for p in pairs)


# ---------------------------------------------------------------------------
# Catalogo
# ---------------------------------------------------------------------------
def verts_of(dec, afs, geom_idx, workdir):
    """Verts del AWO geom_idx (0 si no se puede leer)."""
    try:
        d = swap_b1.decompress_entry(dec, swap_b1.extract_afs_entry(afs, geom_idx),
                                     workdir, 'v%d' % geom_idx)
        if d and d[:4] == b'#AWO':
            AWG0 = u32r(d, u32r(d, 0x1C))
            return u32r(d, AWG0 + 0x2C) // 44
    except Exception:
        pass
    return 0


def classify_variants(geoms, verts):
    """Clasifica los pares de un personaje en (traje, transformacion).

    Heuristica (los modelos HD guardan una variante por par geom/tex):
      - Si el conteo de vertices sube un poco respecto al anterior (<= 15%),
        es una TRANSFORMACION del mismo traje (ej. SSJ, forma monstruo).
      - Si baja o sube mucho, es un TRAJE nuevo (cambio de ropa/modelo).
    Devuelve lista de (traje_idx, form_idx) alineada con `geoms`.

    Los casos con muchas transformaciones que cambian el modelo (Goku, Gohan,
    Vegeta, Trunks) son intrínsecamente ambiguos; la heuristica los aproxima.
    """
    out = []
    traje = 1
    form = 1
    prev = None
    for i, g in enumerate(geoms):
        v = verts[i] if i < len(verts) else 0
        if i == 0:
            traje, form = 1, 1
        elif prev and v:
            delta = (v - prev) / float(prev)
            if delta > 0 and delta <= 0.15:
                form += 1  # misma ropa, transformacion (más geometría)
            else:
                traje += 1
                form = 1
        out.append((traje, form))
        if v:
            prev = v
    return out


def variant_label(traje, form):
    """'Traje 1', 'Traje 1 (Transformación 2)', ..."""
    if form <= 1:
        return 'Traje %d' % traje
    return 'Traje %d (Transformación %d)' % (traje, form)


def catalog_b1(afs, workdir):
    """Devuelve lista de tuplas (label, nombre, variante, jugable, nota,
    main, geom, tex, acm, csk, verts, awgs).

    Emite una fila por modelo/traje: la principal (main=1) con el primer par
    geom/tex, y una por variante extra (main=0). Distingue trajes de
    transformaciones por el conteo de vertices. Solo personajes conocidos:
    el prefijo del label debe estar en characters_db.B1.
    """
    dec = swap_b1.find_tools()[1]
    cat = swap_b1.scan_catalog(afs, workdir)
    out = []
    for label, info in sorted(cat.items()):
        nombre, db_variant, jugable, nota = lookup('B1', label)
        if nombre is None:
            continue
        pares = info.get('pares') or []
        if not pares:
            continue
        geoms = [g for g, t in pares]
        texs = [t for g, t in pares]
        # verts por geom (solo si se puede descomprimir; el primero ya viene)
        verts = [info.get('verts', 0)]
        for g in geoms[1:]:
            verts.append(verts_of(dec, afs, g, workdir))
        classes = classify_variants(geoms, verts)
        acm = max(0, (info.get('bloque') or (0, 0))[0] - 1) if pares else 0
        for idx, (g, t) in enumerate(pares):
            traje, form = classes[idx]
            if idx == 0:
                # fila principal: usar la variante del DB (ej. 'Solo cara' de
                # 20G_FACE, 'Cuerpo' de X20G_BODY) si existe.
                vname = db_variant if db_variant else variant_label(traje, form)
                main = 1
                awgs = info.get('awgs', 0)
                vcount = info.get('verts', 0)
            else:
                vname = variant_label(traje, form)
                main = 0
                awgs = 0
                vcount = verts[idx] if idx < len(verts) else 0
            out.append((label, nombre, vname, '1' if jugable else '0',
                        nota or '', main, g, t, acm if main else 0, 0,
                        vcount, awgs))
    return out


def labels_amb(amb):
    """Devuelve el label raiz del primer AWG del #AWO contenido en un #AMB."""
    i = amb.find(b'#AWO')
    if i < 0:
        return None
    awo = amb[i:]
    n = u32r(awo, 0x18) if len(awo) >= 0x20 else 0
    tbl = u32r(awo, 0x1C) if len(awo) >= 0x20 else 0
    if not n or tbl + 4 > len(awo):
        return None
    off = u32r(awo, tbl)
    if off + 0x40 > len(awo):
        return None
    no = u32r(awo, off + 0x1C)
    if off + no + 16 > len(awo):
        return None
    lab = awo[off + no: off + no + 16].split(b'\x00')[0].decode('latin1', 'ignore')
    return lab or None


def catalog_b3(afs, workdir, dec):
    """Escanea data_cmn.afs del B3 buscando contenedores #AMB (modelos).

    Devuelve {bin_idx: {"label": str, "nombre": str, "variante": str,
                         "jugable": str, "nota": str, "verts": int, "awgs": int}}.
    Solo se conservan bins que estan en characters_db.B3 (personajes de la
    lista GH, que coinciden con los bins REALES del AFS). Los bins de
    animacion/aura/efecto se descartan.
    """
    entries = swap_b1.read_afs_index(afs)
    os.makedirs(workdir, exist_ok=True)
    by_bin = {}
    for i, (addr, size) in enumerate(entries):
        nombre, variante, jugable, nota = lookup_b3_bin(i)
        if nombre is None:
            continue  # no es un bin de modelo conocido
        try:
            data = swap_b1.extract_afs_entry(afs, i)
        except Exception:
            continue
        d = swap_b1.decompress_entry(dec, data, workdir, 'b3bin%d' % i)
        if d is None or d[:4] != b'#AMB':
            continue
        lab = labels_amb(d)
        if not lab:
            continue
        awgs = verts = 0
        awo_off = d.find(b'#AWO')
        if awo_off >= 0:
            awo = d[awo_off:]
            if len(awo) >= 0x20:
                awgs = u32r(awo, 0x18)
                AWG0 = u32r(awo, u32r(awo, 0x1C))
                if AWG0 + 0x30 <= len(awo):
                    verts = u32r(awo, AWG0 + 0x2C) // 44
        by_bin[i] = {'label': lab, 'nombre': nombre, 'variante': variante,
                     'jugable': '1' if jugable else '0', 'nota': nota or '',
                     'verts': verts, 'awgs': awgs}
    return by_bin


def cmd_catalog(args):
    b1_afs = args.b1 or default_b1_afs()
    b3_afs = args.b3 or default_b3_afs()
    workdir = args.work or os.path.join(os.environ.get('TEMP', '/tmp'),
                                        'opencode', 'launcher_catalog')
    os.makedirs(workdir, exist_ok=True)
    dec = swap_b1.find_tools()[1]
    if dec is None:
        print('ERROR: no se encontraron xbcompress/xbdecompress')
        return 1
    lines = ['# Catalogo de personajes - DBZ Budokai HD Collection',
             '# juego|label|nombre|variante|jugable|nota|main|slot_geom|slot_tex|slot_acm|slot_csk|verts|awgs']
    n_b1 = n_b3 = 0
    if b1_afs:
        print('Escanear B1: %s' % b1_afs)
        for row in catalog_b1(b1_afs, workdir):
            lines.append('B1|%s' % '|'.join(str(x) for x in row))
            n_b1 += 1
    if b3_afs:
        print('Escanear B3: %s' % b3_afs)
        cat = catalog_b3(b3_afs, workdir, dec)
        for bin_idx, info in sorted(cat.items()):
            lines.append('B3|%s|%s|%s|%s|%s|1|%d|0|0|0|%d|%d' % (
                info['label'], info['nombre'], info['variante'],
                info['jugable'], info['nota'], bin_idx,
                info['verts'], info['awgs']))
            n_b3 += 1
    out = args.out or os.path.join(HERE, 'cache', 'characters.cat')
    os.makedirs(os.path.dirname(out), exist_ok=True)
    with open(out, 'w', encoding='utf-8') as f:
        f.write('\n'.join(lines) + '\n')
    print('OK: %d modelos B1, %d B3 -> %s' % (n_b1, n_b3, out))
    return 0


# ---------------------------------------------------------------------------
# Swap B1->B1
# ---------------------------------------------------------------------------
def cmd_swap(args):
    b1_afs = args.b1 or default_b1_afs()
    if not b1_afs:
        print('ERROR: no se encontro data_sp.afs del B1')
        return 1
    cmd = [sys.executable, os.path.join(SWAPS, 'swap_b1.py'),
           '--afs', b1_afs,
           '--origen', args.origen, '--dest', str(args.dest),
           '--mod', args.mod or 'swap_%s_on_%d' % (args.origen, args.dest)]
    if args.tex:
        cmd += ['--tex', str(args.tex)]
    if args.dest_label:
        pairs = pairs_for_label(args.dest_label)
        if pairs:
            cmd += ['--dest-pairs', pairs_arg(pairs)]
    if args.dry:
        cmd += ['--dry']
    print('>>> ' + ' '.join(cmd))
    if args.dry:
        return 0
    r = subprocess.run(cmd)
    return r.returncode


# ---------------------------------------------------------------------------
# Port B3->B1
# ---------------------------------------------------------------------------
def cmd_port(args):
    b3_afs = args.b3_afs or default_b3_afs()
    if not b3_afs:
        print('ERROR: no se encontro data_cmn.afs del B3')
        return 1
    workdir = args.work or os.path.join(os.environ.get('TEMP', '/tmp'),
                                        'opencode', 'launcher_port')
    os.makedirs(workdir, exist_ok=True)
    dec = swap_b1.find_tools()[1]

    # localizar el bin del personaje B3
    target = args.bin
    if target is None:
        cat = catalog_b3(b3_afs, workdir, dec)
        found = None
        for bin_idx, info in sorted(cat.items()):
            if info['label'] == args.b3_label or \
               info['label'].startswith(args.b3_label):
                found = bin_idx
                break
        if found is None:
            print('ERROR: personaje B3 "%s" no encontrado en el catalogo' % args.b3_label)
            return 1
        target = found
    print('B3 bin %d (comp) -> extraer AMB...' % target)
    data = swap_b1.extract_afs_entry(b3_afs, target)
    d = swap_b1.decompress_entry(dec, data, workdir, 'port_b3bin%d' % target)
    if d is None or d[:4] != b'#AMB':
        print('ERROR: el bin %d no es #AMB' % target)
        return 1
    awo_b3 = os.path.join(workdir, 'port_b3_%d.awo' % target)
    azt_b3 = os.path.join(workdir, 'port_b3_%d.azt' % target)
    raw = os.path.join(workdir, 'port_b3bin%d.dec' % target)
    with open(raw, 'wb') as f:
        f.write(d)
    prefix = os.path.join(workdir, 'port_b3_%d' % target)
    r = subprocess.run([sys.executable,
                        os.path.join(HERE, 'analizadores', 'extract_amb_awo.py'),
                        raw, prefix],
                       capture_output=True)
    if r.returncode != 0:
        print(r.stdout.decode('utf-8', 'ignore'))
        print(r.stderr.decode('utf-8', 'ignore'))
        return r.returncode
    # extract_amb_awo.py escribe <prefix>_awo.bin / <prefix>_azt.bin
    if not os.path.exists(prefix + '_awo.bin'):
        print('ERROR: no se genero %s_awo.bin' % prefix)
        return 1
    os.replace(prefix + '_awo.bin', awo_b3)
    os.replace(prefix + '_azt.bin', azt_b3)
    # nombre del mod
    mod = args.mod or 'port_%s_to_%d' % (args.b3_label, args.dest)
    cmd = [sys.executable,
           os.path.join(CONV, 'install_b3_to_b1.py'),
           awo_b3, azt_b3, '--mod', mod,
           '--dest', str(args.dest), '--tex', str(args.tex)]
    if args.dest_label:
        pairs = pairs_for_label(args.dest_label)
        if pairs:
            cmd += ['--dest-pairs', pairs_arg(pairs)]
    b1_afs = default_b1_afs()
    if b1_afs:
        cmd += ['--afs', b1_afs]
    print('>>> ' + ' '.join(cmd))
    if args.dry:
        return 0
    r = subprocess.run(cmd)
    return r.returncode


# ---------------------------------------------------------------------------
def main():
    ap = argparse.ArgumentParser(description='Launcher mod pipeline')
    sub = ap.add_subparsers(dest='cmd')

    p_cat = sub.add_parser('catalog')
    p_cat.add_argument('--b1', default=None)
    p_cat.add_argument('--b3', default=None)
    p_cat.add_argument('--out', default=None)
    p_cat.add_argument('--work', default=None)

    p_swap = sub.add_parser('swap')
    p_swap.add_argument('--origen', required=True)
    p_swap.add_argument('--dest', type=int, required=True)
    p_swap.add_argument('--tex', type=int, default=None)
    p_swap.add_argument('--dest-label', default=None,
                        help='label B1 del destino (se expande a TODOS sus trajes)')
    p_swap.add_argument('--mod', default=None)
    p_swap.add_argument('--b1', default=None)
    p_swap.add_argument('--dry', action='store_true')

    p_port = sub.add_parser('port')
    p_port.add_argument('--b3', dest='b3_label', required=True, help='label del personaje B3')
    p_port.add_argument('--bin', type=int, default=None, help='idx del bin B3')
    p_port.add_argument('--dest', type=int, required=True, help='slot geom B1')
    p_port.add_argument('--tex', type=int, required=True, help='slot tex B1')
    p_port.add_argument('--dest-label', default=None,
                        help='label B1 del destino (se expande a TODOS sus trajes)')
    p_port.add_argument('--mod', default=None)
    p_port.add_argument('--b3-afs', dest='b3_afs', default=None)
    p_port.add_argument('--work', default=None)
    p_port.add_argument('--dry', action='store_true')

    args = ap.parse_args()
    if args.cmd == 'catalog':
        return cmd_catalog(args)
    if args.cmd == 'swap':
        return cmd_swap(args)
    if args.cmd == 'port':
        return cmd_port(args)
    ap.print_help()
    return 1


if __name__ == '__main__':
    sys.exit(main())