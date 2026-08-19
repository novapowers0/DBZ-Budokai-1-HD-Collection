"""Escaneo de la casuistica 'piel sin color' en los modelos B3 HD.

Copyright (c) NovaPowers. Released under the MIT License.
Firmado por NovaPowers.

Hallazgo (20/08, leccion 35): algunos personajes del B3 (Dabura, Buu) modelan
la piel con un MATERIAL (mesh part +0x34==5) sobre una textura base GRIS, no
con una textura del color de la piel. Al portar a B1 (que no tiene material de
tintado) la piel sale del color gris de su textura -> descolorida.

Este script escanea TODOS los modelos del catálogo B3 para:
  1. Detectar las partes de piel (AWG label FACE/HAND o material +0x34==5) y
     el indice de textura (grp +0x30) que usan.
  2. Para cada textura de piel, medir si es GRIS (casuistica del bug) o si ya
     tiene color (piel real en la textura -> no necesita tintado).
  3. Cuando es gris, buscar en el resto del AZT la textura con mas color de
     piel para proponer el color objetivo del --tint-skin (el que el B3
     aplicaria por material).

Uso:
  python scan_skin_tint.py [--bins 176,177,...] [--b3 <data_cmn.afs>] [--work <dir>]
  python scan_skin_tint.py --all          # todos los bins del catalogo B3
  python scan_skin_tint.py --save <json>  # guarda el reporte (resultado del analisis)

Salida: reporte por bin con skin_grps, si son grises, y el color objetivo propuesto.
"""
import argparse
import json
import os
import struct
import subprocess
import sys

HERE = os.path.dirname(os.path.abspath(__file__))
ROOT = os.path.abspath(os.path.join(HERE, '..', '..'))
sys.path.insert(0, os.path.join(ROOT, 'mod center hd', 'swaps'))
sys.path.insert(0, os.path.join(ROOT, 'mod center hd'))
sys.path.insert(0, os.path.join(ROOT, 'mod center hd', 'analizadores'))

import swap_b1  # noqa: E402
import paths  # noqa: E402
import characters_db  # noqa: E402

U32 = struct.Struct('>I')
U16 = struct.Struct('<H')


def u32r(b, o):
    return U32.unpack_from(b, o)[0]


def _c565(v):
    r = ((v >> 11) & 0x1F) << 3
    g = ((v >> 5) & 0x3F) << 2
    b = (v & 0x1F) << 3
    return (r | (r >> 5), g | (g >> 6), b | (b >> 5))


def is_grey(c, thresh=40):
    return abs(c[0] - c[1]) < thresh and abs(c[1] - c[2]) < thresh


def texture_stats(b, start, end):
    """Mide el color de una textura DXT3: % gris, color medio, saturacion."""
    if end - start < 128:
        return None
    fourcc = bytes(b[start + 84:start + 88])
    if fourcc != b'DXT3':
        return None
    w = struct.unpack_from('<I', b, start + 16)[0]
    h = struct.unpack_from('<I', b, start + 12)[0]
    data_off = start + 128
    n_blk = (w // 4) * (h // 4)
    grey = 0
    n = 0
    sum_r = sum_g = sum_b = 0
    sat_sum = 0
    for blk in range(n_blk):
        pos = data_off + blk * 16
        v0 = U16.unpack_from(b, pos + 8)[0]
        v1 = U16.unpack_from(b, pos + 10)[0]
        c0 = _c565(v0)
        c1 = _c565(v1)
        for c in (c0, c1):
            if max(c) < 25:  # negro puro / sin uso
                continue
            n += 1
            sum_r += c[0]
            sum_g += c[1]
            sum_b += c[2]
            sat = max(c) - min(c)
            sat_sum += sat
            if is_grey(c):
                grey += 1
    if n == 0:
        return {'w': w, 'h': h, 'grey_pct': 100.0, 'rgb': [0, 0, 0], 'sat': 0.0}
    pct_grey = 100.0 * grey / n
    return {
        'w': w, 'h': h,
        'grey_pct': round(pct_grey, 1),
        'rgb': [round(sum_r / n), round(sum_g / n), round(sum_b / n)],
        'sat': round(sat_sum / n, 1),
    }


def split_dds(azt):
    offsets = []
    idx = 0
    while True:
        i = azt.find(b'DDS ', idx)
        if i == -1:
            break
        nxt = azt.find(b'DDS ', i + 4)
        end = nxt if nxt != -1 else len(azt)
        offsets.append((i, end))
        idx = i + 4
    return offsets


def analyze_awo_azt(awo, azt):
    """Devuelve: skin_grps (indices de textura de piel), y stats por textura."""
    amg_am = u32r(awo, 0x18)
    amg_tbl = u32r(awo, 0x1C)
    skin_grps = set()
    for i in range(amg_am):
        awg = u32r(awo, amg_tbl + i * 4)
        if awg + 0x40 > len(awo):
            continue
        awg_label = awo[awg + 0x40: awg + 0x50].split(b'\x00')[0].decode('latin1', 'ignore')
        is_skin_awg = ('FACE' in awg_label or 'HAND' in awg_label)
        hdr_off = u32r(awo, awg + 0x20)
        hdr_count = u32r(awo, awg + 0x24)
        hdr_abs = awg + hdr_off
        for p in range(hdr_count):
            pos = hdr_abs + p * 0x50
            t38 = u32r(awo, pos + 0x38)
            t3c = u32r(awo, pos + 0x3C)
            shadow = (t38 == 0x1B4 or t3c == 0x1B4)
            if shadow:
                continue
            mat34 = u32r(awo, pos + 0x34)
            if is_skin_awg or mat34 == 5:
                skin_grps.add(u32r(awo, pos + 0x30))
    dds = split_dds(azt)
    stats = [texture_stats(azt, s, e) for s, e in dds]
    return skin_grps, stats


def is_grey_tex(s, thresh=60):
    """Una textura de piel se considera 'gris' (casuistica del bug) si la
    mayoria de sus bloques son grises (sin color de piel real)."""
    return s is not None and s['grey_pct'] >= thresh


def propose_skin_color(stats, skin_grps):
    """Dado el color de las texturas de piel, proponer el color objetivo.

    Estrategia:
      1. Si hay alguna textura de piel GRANDE (>=128px) con color real (no
         gris), usar su color medio (es la piel real del personaje en la
         textura; p. ej. Piccolo verde, Cell, Gero, Freeza).
      2. Si no, buscar en TODO el AZT una textura con color de piel (saturada,
         tono calido) que el B3 aplicaria por material y que no sea ropa.
      3. Si nada, devolver None (sin color inferible -> usar tabla/estandar).
    """
    # 1. textura de piel GRANDE con color real (la mas fiable)
    best = None
    for gi in sorted(skin_grps):
        if gi < len(stats) and stats[gi]:
            s = stats[gi]
            if is_grey_tex(s):
                continue
            if s['sat'] < 25:
                continue
            area = (s['w'] or 0) * (s['h'] or 0)
            if area < 128 * 128:
                continue
            score = s['sat'] + area
            if best is None or score > best[0]:
                best = (score, gi, tuple(s['rgb']))
    if best:
        return ('skin_tex', best[1], best[2])
    # 1b. textura de piel pequena con color real
    best = None
    for gi in sorted(skin_grps):
        if gi < len(stats) and stats[gi]:
            s = stats[gi]
            if is_grey_tex(s) or s['sat'] < 25:
                continue
            score = s['sat']
            if best is None or score > best[0]:
                best = (score, gi, tuple(s['rgb']))
    if best:
        return ('skin_tex', best[1], best[2])
    # 2. buscar textura calida saturada en todo el AZT (no gris, tono piel)
    best = None
    for gi, s in enumerate(stats):
        if not s or s['sat'] < 30 or s['grey_pct'] > 40:
            continue
        r, g, b = s['rgb']
        warm = (r > b + 15) and (r - g) > -10
        if warm:
            score = s['sat'] + min(r, 255)
            if best is None or score > best[0]:
                best = (score, gi, tuple(s['rgb']))
    if best:
        return ('warm_tex', best[1], best[2])
    return None


def get_awo_azt(afs, bin_idx, workdir):
    os.makedirs(workdir, exist_ok=True)
    comp, dec = swap_b1.find_tools()
    if not dec:
        raise RuntimeError('no se encontraron xbcompress/xbdecompress')
    data = swap_b1.extract_afs_entry(afs, bin_idx)
    amb = swap_b1.decompress_entry(dec, data, workdir, 'skin_bin%d' % bin_idx)
    if amb is None or amb[:4] != b'#AMB':
        return None, None
    raw = os.path.join(workdir, 'skin_%d.amb' % bin_idx)
    open(raw, 'wb').write(amb)
    prefix = os.path.join(workdir, 'skin_%d' % bin_idx)
    subprocess.run(
        [sys.executable, os.path.join(HERE, 'extract_amb_awo.py'), raw, prefix],
        capture_output=True)
    awo_p = prefix + '_awo.bin'
    azt_p = prefix + '_azt.bin'
    if not (os.path.isfile(awo_p) and os.path.isfile(azt_p)):
        return None, None
    return open(awo_p, 'rb').read(), open(azt_p, 'rb').read()


def main():
    ap = argparse.ArgumentParser(description='Escaneo de piel B3')
    ap.add_argument('--bins', default=None, help='bins concretos (csv)')
    ap.add_argument('--all', action='store_true', help='todos los bins del catalogo B3')
    ap.add_argument('--b3', default=None, help='data_cmn.afs del B3')
    ap.add_argument('--work', default=None, help='workdir')
    ap.add_argument('--save', default=None, help='guarda el reporte JSON')
    args = ap.parse_args()

    b3_afs = args.b3 or paths.find_b3_afs()
    if not b3_afs or not os.path.isfile(b3_afs):
        print('ERROR: no se encontro data_cmn.afs del B3')
        return 1
    work = args.work or os.path.join(os.environ.get('TEMP', '/tmp'), 'opencode', 'skin_scan')
    os.makedirs(work, exist_ok=True)

    if args.bins:
        bins = [int(x) for x in args.bins.split(',')]
    elif args.all:
        bins = sorted(characters_db.B3.keys())
    else:
        bins = sorted(characters_db.B3.keys())

    report = {}
    for bi in bins:
        name = characters_db.B3.get(bi, ('??', '', None, ''))[0]
        try:
            awo, azt = get_awo_azt(b3_afs, bi, work)
        except Exception as e:
            print('bin %d (%s): ERROR %s' % (bi, name, e))
            continue
        if awo is None:
            print('bin %d (%s): no #AMB' % (bi, name))
            continue
        skin_grps, stats = analyze_awo_azt(awo, azt)
        if not skin_grps:
            print('bin %d (%s): sin partes de piel detectadas' % (bi, name))
            continue
        # resumen de las texturas de piel
        skin_info = {}
        all_grey = True
        grey_area = 0
        total_area = 0
        for gi in sorted(skin_grps):
            if gi < len(stats) and stats[gi]:
                skin_info[gi] = stats[gi]
                if stats[gi]['grey_pct'] < 60:
                    all_grey = False
                area = (stats[gi]['w'] or 0) * (stats[gi]['h'] or 0)
                total_area += area
                if stats[gi]['grey_pct'] >= 60:
                    grey_area += area
            else:
                skin_info[gi] = None
        # piel dominante gris (ponderada por tamano de textura) = caso real del bug
        skin_grey_majority = total_area > 0 and (grey_area / total_area) > 0.6
        prop = propose_skin_color(stats, skin_grps)
        entry = {
            'bin': bi, 'name': name,
            'skin_grps': sorted(skin_grps),
            'skin_tex': skin_info,
            'all_grey': all_grey,
            'skin_grey_majority': bool(skin_grey_majority),
            'proposal': prop,
        }
        report[bi] = entry
        flag = 'BUG-GRIS' if skin_grey_majority else ('TINT?    ' if prop else 'OK       ')
        print('%s bin %d (%s) grps=%s grey_maj=%s prop=%s' % (
            flag, bi, name, sorted(skin_grps), bool(skin_grey_majority),
            prop if prop else 'n/a'))

    if args.save:
        with open(args.save, 'w') as f:
            json.dump(report, f, indent=2)
        print('\nReporte guardado en %s' % args.save)
    return 0


if __name__ == '__main__':
    sys.exit(main())
