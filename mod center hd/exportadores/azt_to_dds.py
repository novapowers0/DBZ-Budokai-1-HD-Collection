"""Extractor de texturas #AZT -> DDS (DBZ Budokai HD).

El #AZT es un contenedor de texturas DDS (DXT1/3/5). Extrae cada DDS
a un archivo individual.

Uso:
  python azt_to_dds.py <textura.azt> <carpeta_salida>
"""
import struct
import os
import sys


def main():
    azt_path = sys.argv[1]
    out_dir = sys.argv[2] if len(sys.argv) > 2 else os.path.splitext(azt_path)[0] + '_dds'
    b = open(azt_path, 'rb').read()

    os.makedirs(out_dir, exist_ok=True)
    idx = 0
    count = 0
    while True:
        i = b.find(b'DDS ', idx)
        if i == -1:
            break
        # tamano del DDS: la siguiente cabecera o el final del archivo
        nxt = b.find(b'DDS ', i + 4)
        end = nxt if nxt != -1 else len(b)
        dds = b[i:end]
        # verificar que tiene header completo
        if len(dds) < 128:
            idx = i + 4
            continue
        w = struct.unpack_from('<I', dds, 16)[0]
        h = struct.unpack_from('<I', dds, 12)[0]
        pf = struct.unpack_from('<I', dds, 84)[0]
        fmt = {0x31545844: 'DXT1', 0x33545844: 'DXT3', 0x33545845: 'DXT3',
               0x35545844: 'DXT5'}.get(pf, hex(pf))
        out = os.path.join(out_dir, 'tex_%02d_%dx%d_%s.dds' % (count, w, h, fmt))
        with open(out, 'wb') as f:
            f.write(dds)
        print('%s: %dx%d %s (%d bytes)' % (out, w, h, fmt, len(dds)))
        count += 1
        idx = i + 4
    print('Extraidas %d texturas a %s' % (count, out_dir))


if __name__ == '__main__':
    main()
