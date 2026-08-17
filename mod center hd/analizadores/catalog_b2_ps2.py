"""catalog_b2_ps2.py — Catálogo de personajes del Budokai 2 PS2.

Escanea un AFS PS2 (Budokai 2) y lista los bins de personajes por label
(X??_BODY / X??_HEAD) con sus entries, igual que el catálogo del launcher
B1 pero para el B2.

Uso:
  python catalog_b2_ps2.py [data_cmn.afs] [--all]

Salida:
  Personaje | Entries (#AMB grandes) | Mini-modelo (X??_HEAD)
"""
import struct
import os
import re
import sys


def read_afs_index(afs_path):
    with open(afs_path, 'rb') as f:
        magic = f.read(4)
        if magic[:3] != b'AFS':
            raise RuntimeError('no es un AFS: %s' % magic)
        count = struct.unpack('<I', f.read(4))[0]
        entries = []
        for _ in range(count):
            addr, size = struct.unpack('<II', f.read(8))
            entries.append((addr, size))
    return entries


def extract(afs_path, idx):
    entries = read_afs_index(afs_path)
    addr, size = entries[idx]
    with open(afs_path, 'rb') as f:
        f.seek(addr)
        return f.read(size)


def labels_of_amo(amo):
    """Labels X??_BODY/WAIST/HEAD escaneando el AMO completo."""
    out = []
    for m in re.finditer(rb'([A-Z0-9]{2,4})_(BODY|WAIST|CHEST|STMC|HEAD)', amo):
        s = m.group(0)
        if s not in out:
            out.append(s)
    return out


def main():
    afs = sys.argv[1] if len(sys.argv) > 1 else r'ps2_games\Budokai 2 (USA)\USR\data_cmn.afs'
    show_all = '--all' in sys.argv
    if not os.path.exists(afs):
        print('AFS no encontrado: %s' % afs)
        print('Uso: python catalog_b2_ps2.py <data_cmn.afs> [--all]')
        return
    entries = read_afs_index(afs)
    print('AFS: %s (%d entradas)' % (afs, len(entries)))

    chars = {}
    with open(afs, 'rb') as f:
        for i, (addr, size) in enumerate(entries):
            if size < 0x1000:
                continue
            f.seek(addr)
            hdr = f.read(0x20)
            if hdr[:4] != b'#AMB':
                continue
            n = struct.unpack('<I', hdr[0x0C:0x10])[0]
            f.seek(addr + 0x20)
            tbl = f.read(n * 16)
            if len(tbl) < 8:
                continue
            loc, sz = struct.unpack('<II', tbl[0:8])
            f.seek(addr + loc)
            amo = f.read(min(sz, 4000000))
            labels = labels_of_amo(amo)
            if not labels:
                continue
            code = None
            for l in labels:
                if l.endswith(b'_BODY'):
                    code = l[:-5].decode()
                    break
            if code is None and labels:
                code = labels[0][:-5].decode()
            is_head = any(l.endswith(b'_HEAD') and sz < 10000 for l in labels)
            chars.setdefault(code, {'main': [], 'heads': []})
            if is_head and sz < 10000:
                chars[code]['heads'].append(i)
            elif sz > 100000:
                chars[code]['main'].append(i)
            elif show_all:
                print('  [%d] sz=%d labels=%s' % (i, size, [l.decode() for l in labels[:4]]))

    print('\n=== PERSONAJES B2 PS2 (labels X??_BODY) ===')
    for code in sorted(chars):
        c = chars[code]
        main = c['main'] if c['main'] else '-'
        heads = c['heads'] if c['heads'] else '-'
        print('%-6s main=%s heads=%s' % (code, main, heads))


if __name__ == '__main__':
    main()