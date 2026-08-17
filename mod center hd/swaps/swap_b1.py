"""Model swap B1 HD automatizado — swap completo (geom+tex) de un personaje a otro.

Copyright (c) NovaPowers. Released under the MIT License.
Firmado por NovaPowers.

Basado en la metodologia validada (docs/tutoriales/MODEL_SWAPS_METODOLOGIA.md):
  el runtime exige que geom (2450) y tex (2451) sean del MISMO personaje.

Flujo:
  1. Escanear el AFS para catalogar personajes (label XXX_BODY por bin).
  2. Seleccionar personaje origen (por label/codigo) y slot destino (por
     personaje o por indice geom/tex).
  3. Extraer del AFS el par #AWO (geom) + #AZT (tex) del personaje origen.
  4. Comprimir ambos con xbcompress /N:2048.
  5. Paddear a tamanio de slot (por defecto 2450=290816, 2451=33504).
  6. Instalar en mods/<mod>/us/data_sp.afs/<slot>/geom.bin y tex.bin.
  7. Verificar round-trip.

Uso:
  python swap_b1.py [--afs <data_sp.afs>] [--list]
  python swap_b1.py [--afs <data_sp.afs>] --origen <label|bin> --dest <slot_geom> --tex <slot_tex> [--mod <nombre>] [--dir <dir_origen>]

  --list                          cataloga todos los personajes del AFS
  --origen <label|bin>            personaje a poner (p. ej. X19G, 19G, PIC, o "49")
  --dest <slot_geom>              slot destino del geom (p. ej. 2450 = TSH)
  --tex <slot_tex>                slot destino del tex (p. ej. 2451 = TSH)
  --dir <carpeta>                 si el par geom/tex son ARCHIVOS ya extraidos,
                                  usar <carpeta>/geom.bin y <carpeta>/tex.bin
                                  (por defecto se extrae del AFS)
  --mod <nombre>                  nombre del mod (default: swap_p<origen>_on_<dest>)
  --label <label>                 si --origen es un bin numerico, forzar label raiz
  --dry                           solo mostrar el plan, no instalar

Ejemplos:
  # Catalogar personajes del AFS
  python swap_b1.py --list

  # Swap Android 19 (X19G, bin 49 + AZT 48) -> Tenshinhan (2450/2451)
  python swap_b1.py --origen X19G --dest 2450 --tex 2451

  # Swap con archivos ya extraidos
  python swap_b1.py --dir b3_bins/par_x19g --dest 2450 --tex 2451
"""
import argparse
import os
import shutil
import struct
import subprocess
import sys

# ---------------------------------------------------------------------------
# Constantes
# ---------------------------------------------------------------------------
# Slot de textura por defecto por slot geom conocido (solo los que usamos).
SLOT_TEX_DEFAULT = {
    2450: 2451,   # Tenshinhan: geom 2450, tex 2451
    380: 381,     # Goku: geom 380/381/536
    536: 381,
}
PAD_GEOM = 290816
PAD_TEX = 33504

# Herramientas de compresion (buscar en varios sitios). El proyecto se entrega
# con xbcompress/xbdecompress en "tools/" (o en el dir del script). Tambien se
# acepta la variable de entorno DBZ1_XBCOMP_DIR y el proyecto hermano B3.
_COMP_DIR = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
sys.path.insert(0, _COMP_DIR)
import paths  # noqa: E402

COMP_CANDIDATES = [
    os.environ.get('DBZ1_XBCOMP_DIR', ''),
    os.path.join(_COMP_DIR, '..', 'tools'),
    os.path.join(_COMP_DIR, '..', '..', 'DBZ Budokai 3 HD Collection', 'mod center',
                 'Xbox 360 Compression - Decompression tool from the XBOX Development Kit'),
]

# ---------------------------------------------------------------------------
# Utilidades
# ---------------------------------------------------------------------------
U32 = struct.Struct('>I')


def u32r(b, o):
    return U32.unpack_from(b, o)[0]


def find_tools():
    # 1) tools/ del repo (portable)
    comp = paths.find_tool("xbcompress.exe")
    dec = paths.find_tool("xbdecompress.exe")
    if comp and dec:
        return comp, dec
    # 2) candidatos legacy
    for d in COMP_CANDIDATES:
        comp = os.path.join(d, "xbcompress.exe")
        dec = os.path.join(d, "xbdecompress.exe")
        if os.path.isfile(comp) and os.path.isfile(dec):
            return comp, dec
    return None, None


def lzx_compress(comp, src, dst):
    r = subprocess.run([comp, "/N:2048", src, dst], input=b"A\n", capture_output=True)
    if not os.path.isfile(dst) or os.path.getsize(dst) == 0:
        raise RuntimeError("xbcompress fallo: %s" % r.stdout)
    return os.path.getsize(dst)


def lzx_decompress(dec, src, dst):
    r = subprocess.run([dec, src, dst], input=b"A\n", capture_output=True)
    if not os.path.isfile(dst) or os.path.getsize(dst) == 0:
        raise RuntimeError("xbdecompress fallo: %s" % r.stdout)
    return os.path.getsize(dst)


def pad_to(path, size):
    """Padding a `size` bytes con 0x00 in-place."""
    b = open(path, "rb").read()
    if len(b) > size:
        raise RuntimeError("archivo %d B no cabe en slot de %d B" % (len(b), size))
    open(path, "wb").write(b + b"\x00" * (size - len(b)))
    return size


# ---------------------------------------------------------------------------
# AFS
# ---------------------------------------------------------------------------
def read_afs_index(afs_path):
    """Devuelve lista de (addr, size) de cada entrada del AFS."""
    with open(afs_path, "rb") as f:
        magic = f.read(4)
        if magic[:3] != b"AFS":
            raise RuntimeError("no es un AFS: %s" % magic)
        count = struct.unpack("<I", f.read(4))[0]
        entries = []
        for _ in range(count):
            addr, size = struct.unpack("<II", f.read(8))
            entries.append((addr, size))
    return entries


def extract_afs_entry(afs_path, idx):
    entries = read_afs_index(afs_path)
    addr, size = entries[idx]
    with open(afs_path, "rb") as f:
        f.seek(addr)
        return f.read(size)


def decompress_entry(dec, data, workdir, name):
    lzx = os.path.join(workdir, name + ".lzx")
    out = os.path.join(workdir, name + ".bin")
    open(lzx, "wb").write(data)
    try:
        lzx_decompress(dec, lzx, out)
    except RuntimeError:
        return None
    return open(out, "rb").read()


# ---------------------------------------------------------------------------
# Catalogo de personajes
# ---------------------------------------------------------------------------
def labels_hd(b):
    """Bones labels del #AWO."""
    try:
        n = u32r(b, 0x10)
        off = u32r(b, 0x24)
        out = {}
        for bi in range(n):
            s = b[off + bi * 32: off + bi * 32 + 32].split(b"\x00")[0].decode("latin1", "ignore")
            if s:
                out[bi] = s
        return out
    except Exception:
        return {}


def scan_catalog(afs_path, workdir, max_bins=None):
    """Escanea el AFS y agrupa bins por personaje (label raiz del #AWO).

    Devuelve {label: {"pares": [(geom_idx, tex_idx), ...], "awgs": int,
                       "verts": int, "bloque": (min_idx, max_idx)}}
    Los pares se construyen por contiguidad: cada #AWO se empareja con el
    siguiente #AZT del mismo bloque (el #ACM marca el inicio del bloque).
    """
    dec = find_tools()[1]
    if dec is None:
        raise RuntimeError("no se encontraron xbcompress/xbdecompress")
    entries = read_afs_index(afs_path)
    by_idx = {}       # idx -> {"kind", "label", "n_tex"}
    os.makedirs(workdir, exist_ok=True)

    # Paso 1: tipo y label de cada bin descomprimible
    for i, (addr, size) in enumerate(entries):
        if max_bins is not None and i >= max_bins:
            break
        if size < 1000:
            continue
        try:
            data = extract_afs_entry(afs_path, i)
        except Exception:
            continue
        d = decompress_entry(dec, data, workdir, "bin%d" % i)
        if d is None or len(d) < 16:
            continue
        magic = d[:4]
        kind = None
        if magic == b"#AWO":
            kind = "geom"
        elif magic == b"#AZT":
            kind = "tex"
        elif magic in (b"#ACM", b"#AMB", b"#CCM", b"#CSK", b"#SPX", b"#ACA", b"#CFC"):
            kind = "block"
        if kind:
            lab = None
            if magic == b"#AWO":
                lab = labels_hd(d).get(0)
            by_idx[i] = {"kind": kind, "label": lab, "n_tex": 0}

    # Paso 2: los #AZT no tienen label; asignar a la etiqueta del #ACM/#AWO del bloque.
    # Un bloque = una racha de #AWO/#AZT con el mismo label (los #AWO consecutivos
    # del mismo personaje comparten label; los #AZT sin label se asignan al actual).
    owner = {}
    current_label = None
    current_block_start = None
    for i, info in sorted(by_idx.items()):
        if info["kind"] == "geom" and info.get("label"):
            # nuevo bloque si el label cambia respecto al actual
            if info["label"] != current_label:
                current_label = info["label"]
                current_block_start = i
        elif info["kind"] == "block" and info.get("label"):
            current_label = info["label"]
            current_block_start = i
        owner[i] = (current_label, current_block_start)

    # Paso 3: agrupar AWO y AZT por bloque.
    # Los AZT se asignan a pares contiguos: (AWO_i, AZT_j) con j>i, j el primero libre.
    geom_by_block = {}   # (label, block_start) -> [idx AWO]
    tex_by_block = {}    # (label, block_start) -> [idx AZT]
    for i, info in sorted(by_idx.items()):
        label, bs = owner.get(i, (None, None))
        if not label:
            continue
        key = (label, bs)
        if info["kind"] == "geom":
            geom_by_block.setdefault(key, []).append(i)
        elif info["kind"] == "tex":
            tex_by_block.setdefault(key, []).append(i)

    catalog = {}
    for (label, bs), geoms in sorted(geom_by_block.items()):
        texs = tex_by_block.get((label, bs), [])
        pares = []
        ti = 0
        for gi in geoms:
            # AZT mas cercano despues de gi (o el primer AZT del bloque como fallback)
            cand = [t for t in texs if t > gi]
            if not cand:
                cand = texs[ti:ti + 1] if ti < len(texs) else []
                if cand:
                    ti += 1
            else:
                t_sel = min(cand)
                if t_sel in texs:
                    texs = [t for t in texs if t != t_sel]
                cand = [t_sel]
            if cand:
                pares.append((gi, cand[0]))
        # enriquecer con verts/awgs del primer AWO
        awgs = verts = 0
        if pares:
            try:
                d = decompress_entry(dec, extract_afs_entry(afs_path, pares[0][0]), workdir, "c_%s" % label)
                if d and d[:4] == b"#AWO":
                    awgs = u32r(d, 0x18)
                    AWG0 = u32r(d, u32r(d, 0x1C))
                    verts = u32r(d, AWG0 + 0x2C) // 44
            except Exception:
                pass
        catalog[label] = {"pares": pares, "awgs": awgs, "verts": verts,
                          "bloque": (bs, max([p[0] for p in pares] + [bs]))}
    return catalog


# ---------------------------------------------------------------------------
# Busqueda de origen
# ---------------------------------------------------------------------------
def resolve_origen(catalog, origen, workdir, dec, afs_path):
    """Devuelve (geom_idx, tex_idx) del personaje origen.

    Prefiere el primer par; si el origen es un bin numerico, usa ese bin como
    geom y busca el AZT mas cercano posterior.
    """
    if origen.isdigit():
        gi = int(origen)
        for lab, info in sorted(catalog.items()):
            for g, t in info.get("pares", []):
                if g == gi:
                    return g, t
        # no esta en un par catalogado: buscar el AZT posterior mas cercano
        ti = None
        for lab, info in sorted(catalog.items()):
            for g, t in info.get("pares", []):
                if g > gi and (ti is None or t < ti):
                    ti = t
        if ti is None:
            raise RuntimeError("no se encontro el AZT para el bin geom %d" % gi)
        return gi, ti
    # por label
    for lab, info in catalog.items():
        if lab == origen or lab.startswith(origen) or origen in lab or lab.startswith("X" + origen):
            if info["pares"]:
                return info["pares"][0]
    # por sufijo (X19G -> 19G)
    for lab, info in catalog.items():
        if lab.split("_")[0].endswith(origen) or ("_" in lab and lab.split("_", 1)[1].startswith(origen)):
            if info["pares"]:
                return info["pares"][0]
    raise RuntimeError("personaje '%s' no encontrado. Usa --list" % origen)


# ---------------------------------------------------------------------------
# Instalacion
# ---------------------------------------------------------------------------
def manage_mods(mods_root, keep_name):
    """Desactiva todos los mods menos `keep_name` (archivo .disabled interno)."""
    if not os.path.isdir(mods_root):
        return
    for m in sorted(os.listdir(mods_root)):
        d = os.path.join(mods_root, m)
        if not os.path.isdir(d) or m == keep_name:
            continue
        marker = os.path.join(d, ".disabled")
        if not os.path.exists(marker):
            try:
                open(marker, "w").write("disabled\n")
                print("Desactivado: %s" % m)
            except OSError:
                pass
    # asegurar que el mod a activar no tenga marcador
    keep = os.path.join(mods_root, keep_name, ".disabled")
    if os.path.exists(keep):
        os.remove(keep)


def install(comp, dec, geom_data, tex_data, dest_slots, mod_name, mods_root,
            pads=(PAD_GEOM, PAD_TEX)):
    """Instala geom+tex comprimidos+padded en el mod.

    El override se escribe en TODOS los data_*.afs de personaje (data_sp, us,
    fr, en, ge, it): comparten la misma numeracion de bins y el runtime puede
    leer cualquiera segun region/idioma. Asi el mod funciona sin depender del
    AFS concreto que elija el juego.
    """
    geom_slot, tex_slot = dest_slots
    data_afs_names = ("data_sp.afs", "data_us.afs", "data_fr.afs",
                      "data_en.afs", "data_ge.afs", "data_it.afs")
    work = os.path.join(mods_root, mod_name, "us", ".work")
    os.makedirs(work, exist_ok=True)
    g_raw = os.path.join(work, "geom_raw.bin")
    t_raw = os.path.join(work, "tex_raw.bin")
    open(g_raw, "wb").write(geom_data)
    open(t_raw, "wb").write(tex_data)
    g_lzx = os.path.join(work, "geom.lzx")
    t_lzx = os.path.join(work, "tex.lzx")
    g_sz = lzx_compress(comp, g_raw, g_lzx)
    t_sz = lzx_compress(comp, t_raw, t_lzx)
    print("Comprimido: geom %d -> %d B | tex %d -> %d B" % (len(geom_data), g_sz, len(tex_data), t_sz))

    # padding al tamano de slot
    g_pad = os.path.join(work, "geom_pad.bin")
    t_pad = os.path.join(work, "tex_pad.bin")
    shutil.copy(g_lzx, g_pad)
    shutil.copy(t_lzx, t_pad)
    g_final = pad_to(g_pad, pads[0])
    t_final = pad_to(t_pad, pads[1])

    # verificar round-trip
    g_rt = os.path.join(work, "geom_rt.bin")
    t_rt = os.path.join(work, "tex_rt.bin")
    lzx_decompress(dec, g_pad, g_rt)
    lzx_decompress(dec, t_pad, t_rt)
    ok_g = open(g_rt, "rb").read() == geom_data
    ok_t = open(t_rt, "rb").read() == tex_data
    print("Round-trip: geom %s | tex %s" % ("OK" if ok_g else "FAIL", "OK" if ok_t else "FAIL"))
    if not (ok_g and ok_t):
        raise RuntimeError("round-trip fallo, no se instala")

    # instalar en todos los data_*.afs de personaje
    installed = []
    for afs_name in data_afs_names:
        out_dir = os.path.join(mods_root, mod_name, "us", afs_name)
        geom_path = os.path.join(out_dir, str(geom_slot), "geom.bin")
        tex_path = os.path.join(out_dir, str(tex_slot), "tex.bin")
        os.makedirs(os.path.dirname(geom_path), exist_ok=True)
        os.makedirs(os.path.dirname(tex_path), exist_ok=True)
        shutil.copy(g_pad, geom_path)
        shutil.copy(t_pad, tex_path)
        installed.append((geom_path, tex_path))
    for geom_path, tex_path in installed:
        print("Instalado:")
        print("  %s" % geom_path)
        print("  %s" % tex_path)
    # gestion de mods: activar este, desactivar el resto
    manage_mods(mods_root, mod_name)
    return installed[0]


# ---------------------------------------------------------------------------
# Main
# ---------------------------------------------------------------------------
def main():
    ap = argparse.ArgumentParser(description="Model swap B1 HD (geom+tex)")
    ap.add_argument("--afs", default=None,
                    help="ruta al data_sp.afs (default: assets/eu o assets/us)")
    ap.add_argument("--list", action="store_true", help="catalogar personajes")
    ap.add_argument("--info", default=None, help="mostrar pares de un personaje (label o bin)")
    ap.add_argument("--origen", default=None, help="personaje origen (label o bin)")
    ap.add_argument("--dest", type=int, default=None, help="slot geom destino (2450=TSH)")
    ap.add_argument("--tex", type=int, default=None, help="slot tex destino (2451=TSH)")
    ap.add_argument("--dir", default=None, help="carpeta con geom.bin/tex.bin ya extraidos")
    ap.add_argument("--mod", default=None, help="nombre del mod (default auto)")
    ap.add_argument("--dry", action="store_true", help="solo plan, no instalar")
    ap.add_argument("--max-bins", type=int, default=None, help="limitar escaneo (debug)")
    args = ap.parse_args()

    comp, dec = find_tools()
    if dec is None:
        print("ERROR: no se encontraron xbcompress/xbdecompress")
        return 1

    # ubicar AFS (cualquier data_*.afs de personaje: sp/us/fr/en/ge/it)
    if args.afs is None:
        root = os.path.join(os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__)))), "assets")
        for name in ("data_sp.afs", "data_us.afs", "data_fr.afs",
                     "data_en.afs", "data_ge.afs", "data_it.afs"):
            for region in ("eu", "us"):
                p = os.path.join(root, region, name)
                if os.path.isfile(p):
                    args.afs = p
                    break
            if args.afs:
                break
    if not args.afs or not os.path.isfile(args.afs):
        print("ERROR: AFS no encontrado. Usa --afs <ruta>")
        return 1

    workdir = os.path.join(os.path.dirname(os.path.dirname(os.path.abspath(__file__))), "swaps", ".work")
    os.makedirs(workdir, exist_ok=True)

    # catalogar
    print("Escaneando %s ..." % os.path.basename(args.afs))
    catalog = scan_catalog(args.afs, workdir, max_bins=args.max_bins)

    if args.info:
        origen = args.info
        for lab, info in sorted(catalog.items()):
            if (lab == origen or lab.startswith(origen) or origen in lab
                    or lab.startswith("X" + origen) or lab.split("_")[0].endswith(origen)):
                print("\n%s (bloque %s-%d):" % (lab, info["bloque"][0], info["bloque"][1]))
                print("  awgs=%d verts=%d" % (info["awgs"], info["verts"]))
                for g, t in info["pares"]:
                    print("    par: geom=%-5d tex=%-5d" % (g, t))
                return 0
        print("no encontrado: %s" % origen)
        return 1

    if args.list or (args.origen is None and args.dir is None):
        print("\n=== PERSONAJES DETECTADOS ===")
        for lab in sorted(catalog.keys()):
            info = catalog[lab]
            pares = info["pares"]
            if not pares:
                continue
            g0, t0 = pares[0]
            extra = " (+%d pares)" % (len(pares) - 1) if len(pares) > 1 else ""
            print("  %-24s geom=%-5d tex=%-5d awgs=%-3d verts=%d%s" % (
                lab, g0, t0, info["awgs"], info["verts"], extra))
        print("\nUso: python swap_b1.py --origen <label> --dest <slot_geom> --tex <slot_tex>")
        return 0

    # resolver origen
    if args.dir:
        g = os.path.join(args.dir, "geom.bin")
        t = os.path.join(args.dir, "tex.bin")
        if not (os.path.isfile(g) and os.path.isfile(t)):
            print("ERROR: no hay geom.bin/tex.bin en %s" % args.dir)
            return 1
        geom_data = open(g, "rb").read()
        tex_data = open(t, "rb").read()
        print("Origen: archivos de %s (%d B geom, %d B tex)" % (args.dir, len(geom_data), len(tex_data)))
    else:
        gi, ti = resolve_origen(catalog, args.origen, workdir, dec, args.afs)
        geom_data = decompress_entry(dec, extract_afs_entry(args.afs, gi), workdir, "src_geom")
        tex_data = decompress_entry(dec, extract_afs_entry(args.afs, ti), workdir, "src_tex")
        if geom_data is None or tex_data is None:
            print("ERROR: no se pudieron extraer geom(%d)/tex(%d) del AFS" % (gi, ti))
            return 1
        print("Origen: bin %d (#AWO %d B) + bin %d (#AZT %d B)" % (
            gi, len(geom_data), ti, len(tex_data)))

    # resolver destino
    geom_slot = args.dest
    tex_slot = args.tex if args.tex is not None else SLOT_TEX_DEFAULT.get(geom_slot)
    if geom_slot is None or tex_slot is None:
        print("ERROR: necesitas --dest <slot_geom> (y --tex si no es conocido)")
        return 1
    print("Destino: slot %d (geom) + slot %d (tex)" % (geom_slot, tex_slot))

    if args.dry:
        print("DRY: no se instala")
        return 0

    # nombre del mod
    mod_name = args.mod
    if not mod_name:
        origen_name = args.origen or os.path.basename(os.path.dirname(args.dir))
        mod_name = "swap_%s_on_%d" % (origen_name, geom_slot)

    # instalar
    mods_root = os.path.join(os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__)))), "mods")
    geom_path, tex_path = install(comp, dec, geom_data, tex_data, (geom_slot, tex_slot),
                                  mod_name, mods_root)
    print("\nMod activo: %s" % mod_name)
    print("Overrides instalados (2450/2451); el resto de mods desactivado.")
    print("Probar en combate; si algo falla, borra la carpeta del mod.")
    return 0


if __name__ == "__main__":
    sys.exit(main())