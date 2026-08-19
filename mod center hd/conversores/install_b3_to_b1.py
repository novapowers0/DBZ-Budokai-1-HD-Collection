"""Instalador automático B3 HD -> B1 HD (pipeline completo validado 16/08/2026).

Automatiza el port Gero B3->B1 (100% funcional):
  1. Convierte AWO B3 -> B1 (flag 0x2, type2 0x1BD/0x11BD, materiales B1)
  2. Fuerza alpha DXT3 a 0xFF en el AZT (evita cuerpo negro)
  3. Comprime /N:2048 + padding a slot + round-trip verificado
  4. Instala el mod y gestiona activación (.disabled)

Uso:
  python install_b3_to_b1.py <awo_b3.bin> <azt_b3.bin> --mod <nombre> [--dest 2450 --tex 2451] [--flatten] [--remap <ref.b1>]

Requiere que port_b3_to_b1_v2.py y swaps/swap_b1.py estén en el mismo árbol.
"""
import argparse
import os
import subprocess
import sys

HERE = os.path.dirname(os.path.abspath(__file__))
sys.path.insert(0, HERE)
sys.path.insert(0, os.path.join(HERE, '..', 'swaps'))
sys.path.insert(0, HERE)

from port_b3_to_b1_v2 import fix_azt_alpha  # noqa: E402


def main():
    ap = argparse.ArgumentParser(description='Port e instalación B3 HD -> B1 HD')
    ap.add_argument('awo_b3', help='AWO B3 (geom)')
    ap.add_argument('azt_b3', help='AZT B3 (tex)')
    ap.add_argument('--mod', default='test_b3_to_b1', help='nombre del mod')
    ap.add_argument('--dest', type=int, default=2450, help='slot geom destino')
    ap.add_argument('--tex', type=int, default=2451, help='slot tex destino')
    ap.add_argument('--dest-pairs', default=None,
                    help='pares (geom:tex,...) del destino; si se da, se instala '
                         'en TODOS (todos los trajes del personaje)')
    ap.add_argument('--flatten', action='store_true', help='aplanar grp (opcional)')
    ap.add_argument('--remap', default=None, help='ref B1 para remap de bones (opcional)')
    ap.add_argument('--mods-root', default=None, help='raiz de mods (default: <repo>/mods)')
    ap.add_argument('--work', default=None, help='carpeta de trabajo temporal')
    ap.add_argument('--afs', default=None,
                    help='data_*.afs del B1 destino (para padding al tamanio real del slot)')
    args = ap.parse_args()

    # localizar mods root y swap_b1
    repo = os.path.abspath(os.path.join(HERE, '..', '..'))
    if args.mods_root:
        mods_root = args.mods_root
    else:
        mods_root = os.path.join(repo, 'mods')
    swap_dir = os.path.join(repo, 'mod center hd', 'swaps')
    sys.path.insert(0, swap_dir)
    sys.path.insert(0, os.path.join(repo, 'mod center hd'))
    import swap_b1
    import paths

    work = args.work or os.path.join(os.environ.get('TEMP', '/tmp'), 'opencode', 'b3_to_b1_work')
    os.makedirs(work, exist_ok=True)
    comp, dec = swap_b1.find_tools()
    if not comp:
        print('ERROR: no se encontraron xbcompress/xbdecompress')
        return 1

    # 1. Port B3 -> B1 (geom + azt con alpha)
    out_awo = os.path.join(work, 'port.awo')
    out_azt = os.path.join(work, 'port.azt')
    cmd = [sys.executable, os.path.join(HERE, 'port_b3_to_b1_v2.py'),
           args.awo_b3, args.azt_b3, out_awo, out_azt]
    if args.flatten:
        cmd.append('--flatten')
    if args.remap:
        cmd += ['--remap', args.remap]
    print('>>> Port B3->B1...')
    r = subprocess.run(cmd, capture_output=True)
    print(r.stdout.decode('utf-8', 'ignore'))
    if r.returncode != 0:
        print('ERROR port:', r.stderr.decode('utf-8', 'ignore'))
        return 1

    geom_data = open(out_awo, 'rb').read()
    tex_data = open(out_azt, 'rb').read()

    # 2. Instalar (comprimir + padding + round-trip + gestion mods)
    print('>>> Instalando mod %s...' % args.mod)
    # padding al tamanio REAL del slot destino (--afs B1); sin AFS usa el
    # default de Tenshinhan (puede quedar corto en otros slots -> tex rota)
    afs_b1 = args.afs or paths.find_b1_afs()
    dest_pairs = None
    if args.dest_pairs:
        import swap_b1 as _sb
        dest_pairs = _sb.parse_dest_pairs(args.dest_pairs)
        print('Destino expandido a %d pares (todos los trajes): %s' % (
            len(dest_pairs), dest_pairs))
    geom_path, tex_path = swap_b1.install(
        comp, dec, geom_data, tex_data, (args.dest, args.tex), args.mod,
        mods_root, afs_path=afs_b1, dest_pairs=dest_pairs,
        manifest={
            'name': 'Port B3 -> B1 (%s)' % os.path.basename(args.awo_b3),
            'description': 'Port de modelo B3 HD a slot B1 HD (geom %d / tex %d).' % (args.dest, args.tex),
            'author': 'NovaPowers',
            'version': '1.0',
            'type': 'port_b3',
            'source': os.path.basename(args.awo_b3),
            'target': '%d/%d' % (args.dest, args.tex),
        })
    print('Mod instalado y ACTIVO: %s' % args.mod)
    print('  %s' % geom_path)
    print('  %s' % tex_path)
    return 0


if __name__ == '__main__':
    sys.exit(main())
