"""Port B3 HD -> B1 HD (pipeline COMPLETO validado en runtime, 16/08/2026).

VALIDADO 100%: Gero B3 HD -> slot TSH B1 HD (mod test_gero_b3_to_b1_v2)
renderiza perfecto en combate: rig OK, materiales/specular OK, texturas OK.

Descubrimiento clave (swap nativo B1->B1): el runtime dibuja el bin #AWO
COMPLETO tal cual (mesh group, IB, bones, UVs incluidos), usando la tabla de
bones del PROPIO bin, sin validar conteos del slot (X19G con 46 bones en slot
TSH de 42 funcionó). Por tanto el port B3->B1 NO reindexa bones ni aplana la
jerarquía: el bin conserva su tabla de bones B3 y sus vértices apuntan a ella.

Conversiones necesarias (todas validadas):
  1. Flag +0x0C del AWG: B3=0x4 -> B1=0x2
  2. Type2 de mesh part headers: B3=0x29BD (t3C) / 0x1B5 (t38) -> B1=0x1BD;
     sombra 0x1B4 -> 0x190
  3. u34 +0x34 del mesh part -> 0xFFFFFFFF (formato B1)
  4. MATERIALES B1 (crítico para el sombreado/specular):
     - Escala +00: 4x 128.0 (el B3 usa 1.0, da cuerpo negro/sin specular)
     - Weights +10: torso 0.85/0.80/0.70/1.0, extremidades 0.85/0.85/0.80/1.0
     - Type2 -> 0x11BD en partes no-sombra (shader B1 alternativo, specular)
  5. AZT: forzar alpha DXT3 a 0xFF (sin esto -> 'cuerpo negro')
     El runtime B1 espera DXT3 con alpha opaco (verificado en X19G nativo).
  6. (opcional --flatten) reindexar grp +0x30 a grupos secuenciales
  7. (opcional --remap <ref>) re-mapear bones de vertices (+16) y arms por labels

Uso:
  python port_b3_to_b1_v2.py <awo_b3.bin> <azt_b3.bin> <out.awo> <out_azt.bin> [--flatten] [--remap <awo_b1_ref.bin>]

Salidas:
  <out.awo>       AWO convertido (geom listo para slot 2450)
  <out_azt.bin>   AZT con alpha DXT3 forzado a 0xFF (listo para slot 2451)
"""
import struct
import sys

U32 = struct.Struct('>I')

ESCALA_B1 = struct.pack('>4f', 128.0, 128.0, 128.0, 128.0)
W_TORSO = struct.pack('>4f', 0.85, 0.80, 0.70, 1.0)
W_EXT = struct.pack('>4f', 0.85, 0.85, 0.80, 1.0)


def u32r(b, o):
    return U32.unpack_from(b, o)[0]


def labels_hd(b):
    n = u32r(b, 0x10)
    off = u32r(b, 0x24)
    out = {}
    for bi in range(n):
        s = b[off + bi * 32: off + bi * 32 + 32].split(b'\x00')[0].decode('latin1', 'ignore')
        if s:
            out[bi] = s
    return out


def build_map(b3_labels, b1_labels):
    b1_by_label = {l: i for i, l in b1_labels.items()}
    m = {}
    for b3i, lab in b3_labels.items():
        m[b3i] = b1_by_label.get(lab, -1)
    return m


def fix_azt_alpha(azt):
    """Fuerza el alpha DXT3 a 0xFF en todos los bloques (evita cuerpo negro)."""
    b = bytearray(azt)
    n = 0
    idx = 0
    while True:
        i = b.find(b'DDS ', idx)
        if i == -1:
            break
        fourcc = b[i + 84:i + 88]
        w = struct.unpack_from('<I', b, i + 16)[0]
        h = struct.unpack_from('<I', b, i + 12)[0]
        if fourcc == b'DXT3':
            data_off = i + 128
            n_blk = (w // 4) * (h // 4)
            for blk in range(n_blk):
                pos = data_off + blk * 16
                b[pos:pos + 8] = b'\xFF' * 8
                n += 1
        idx = i + 4
    return bytes(b), n


def main():
    args = sys.argv[1:]
    if len(args) < 4:
        print('Uso: port_b3_to_b1_v2.py <awo_b3.bin> <azt_b3.bin> <out.awo> <out_azt.bin> [--flatten] [--remap <awo_b1_ref.bin>]')
        return
    do_flatten = '--flatten' in args
    do_remap = '--remap' in args
    remap_ref = None
    if do_remap:
        ri = args.index('--remap')
        if ri + 1 < len(args):
            remap_ref = args[ri + 1]
            args = args[:ri] + args[ri + 2:]

    awo_path, azt_path, out, out_azt = args[0], args[1], args[2], args[3]
    awo = bytearray(open(awo_path, 'rb').read())
    azt = open(azt_path, 'rb').read()

    amg_am = u32r(awo, 0x18)
    amg_tbl = u32r(awo, 0x1C)
    print('AWO: %d bytes, %d AWGs | AZT: %d bytes (%d slots)' % (
        len(awo), amg_am, len(azt), u32r(azt, 0x10)))

    m = None
    if do_remap and remap_ref:
        b3l = labels_hd(awo)
        b1l = labels_hd(open(remap_ref, 'rb').read())
        m = build_map(b3l, b1l)
        n_unmapped = sum(1 for v in m.values() if v < 0)
        print('Labels B3: %d | B1: %d | mapa: %d (unmapped: %d)' % (
            len(b3l), len(b1l), len(m), n_unmapped))

    bone_to_grp = {}
    if do_flatten:
        next_grp = 0
        for i in range(amg_am):
            awg = u32r(awo, amg_tbl + i * 4)
            if awg + 0x40 > len(awo):
                continue
            hdr_off = u32r(awo, awg + 0x20)
            hdr_count = u32r(awo, awg + 0x24)
            hdr_abs = awg + hdr_off
            for p in range(hdr_count):
                pos = hdr_abs + p * 0x50
                t38 = u32r(awo, pos + 0x38)
                t3c = u32r(awo, pos + 0x3C)
                if t38 == 0x1B4 or t3c == 0x1B4:
                    continue
                g = u32r(awo, pos + 0x30)
                if g not in bone_to_grp:
                    bone_to_grp[g] = next_grp
                    next_grp += 1
        print('Flatten: %d bones -> %d grupos secuenciales' % (len(bone_to_grp), next_grp))

    tot_flag = tot_type = tot_grp = tot_u34 = tot_vert = tot_arm = tot_mat = 0
    for i in range(amg_am):
        awg = u32r(awo, amg_tbl + i * 4)
        if awg + 0x40 > len(awo):
            continue

        # 1. Flag +0x0C -> 0x2
        if u32r(awo, awg + 0x0C) != 0x2:
            struct.pack_into('>I', awo, awg + 0x0C, 0x2)
            tot_flag += 1

        # 2. Type2 + materiales + grp + u34
        hdr_off = u32r(awo, awg + 0x20)
        hdr_count = u32r(awo, awg + 0x24)
        hdr_abs = awg + hdr_off
        for p in range(hdr_count):
            pos = hdr_abs + p * 0x50
            t38 = u32r(awo, pos + 0x38)
            t3c = u32r(awo, pos + 0x3C)
            shadow = (t38 == 0x1B4 or t3c == 0x1B4)
            # type2 -> B1
            if t38 == 0x1B5:
                struct.pack_into('>I', awo, pos + 0x38, 0x1BD)
                tot_type += 1
            elif t38 == 0x1B4:
                struct.pack_into('>I', awo, pos + 0x38, 0x190)
                tot_type += 1
            if t3c == 0x29BD:
                struct.pack_into('>I', awo, pos + 0x3C, 0x1BD)
                tot_type += 1
            elif t3c == 0x1B4:
                struct.pack_into('>I', awo, pos + 0x3C, 0x190)
                tot_type += 1
            # materiales B1 (NO tocar sombras)
            if not shadow:
                awo[pos:pos + 16] = ESCALA_B1
                awo[pos + 16:pos + 32] = W_TORSO if i == 0 else W_EXT
                tot_mat += 1
                # shader B1 alternativo con specular
                if u32r(awo, pos + 0x38) == 0x1BD and u32r(awo, pos + 0x3C) == 0x1BD:
                    struct.pack_into('>I', awo, pos + 0x38, 0x11BD)
                    struct.pack_into('>I', awo, pos + 0x3C, 0x11BD)
            # grp: opcional flatten
            if do_flatten:
                g = u32r(awo, pos + 0x30)
                if shadow:
                    if g != 0xFFFFFFFF:
                        struct.pack_into('>I', awo, pos + 0x30, 0xFFFFFFFF)
                        tot_grp += 1
                else:
                    ng = bone_to_grp[g]
                    if ng != g:
                        struct.pack_into('>I', awo, pos + 0x30, ng)
                        tot_grp += 1
            # u34: B1 siempre 0xFFFFFFFF
            u = u32r(awo, pos + 0x34)
            if u != 0xFFFFFFFF:
                struct.pack_into('>I', awo, pos + 0x34, 0xFFFFFFFF)
                tot_u34 += 1

        # 3. (opcional) remap bones de vertices +16 y arms
        sec_rel = u32r(awo, awg + 0x28)
        sec_sz = u32r(awo, awg + 0x2C)
        sec = awg + sec_rel
        if m:
            for v in range(sec_sz // 44):
                q = sec + v * 44
                bone = u32r(awo, q + 16)
                if bone in m and m[bone] >= 0 and m[bone] != bone:
                    struct.pack_into('>I', awo, q + 16, m[bone])
                    tot_vert += 1
            for off in range(awg, sec, 4):
                v = u32r(awo, off)
                if v in (0x9000020C, 0x8000020C):
                    arm_ptr = u32r(awo, off + 4)
                    arm_abs = awg + arm_ptr
                    if arm_abs + 4 <= len(awo):
                        bone = u32r(awo, arm_abs)
                        if bone in m and m[bone] >= 0 and m[bone] != bone:
                            struct.pack_into('>I', awo, arm_abs, m[bone])
                            tot_arm += 1

    open(out, 'wb').write(bytes(awo))

    # 4. AZT: alpha DXT3 -> 0xFF
    azt_fixed, n_alpha = fix_azt_alpha(azt)
    open(out_azt, 'wb').write(azt_fixed)

    print('TOTAL: flag=%d type2=%d mat=%d grp=%d u34=%d verts=%d arms=%d. Guardado %s (%d bytes)' % (
        tot_flag, tot_type, tot_mat, tot_grp, tot_u34, tot_vert, tot_arm, out, len(awo)))
    print('AZT: alpha DXT3 forzado a 0xFF en %d bloques. Guardado %s (%d bytes)' % (
        n_alpha, out_azt, len(azt_fixed)))


if __name__ == '__main__':
    main()
