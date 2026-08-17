"""Port B3 HD -> B1 HD (pipeline COMPLETO).

El formato HD de B1 y B3 es casi idéntico, pero difieren en varios "sellos":
  1. Flag +0x0C del AWG: B1=0x2, B3=0x4
  2. Type2 de mesh part headers: B3=0x29BD (t3C) / 0x1B5 (t38), B1=0x1BD/0x11BD
     (ambos campos). Sombra B3=0x1B4 -> B1=0x190
  3. Orden de bones (por labels) — re-mapear vertices y arms
  4. Jerarquia del mesh group: B3 usa grp (+0x30) = INDICE DE BONE (0,2,3,4,6,8...),
     B1 usa grp = indice de grupo secuencial (0-3) o 0xFFFFFFFF (sombra).
     Hay que APLANAR reindexando los valores. Tambien u34 (+0x34): B3=1/5/7,
     B1=0xFFFFFFFF siempre.

Este script aplica TODOS los re-mapeos:
  - Cambia flag +0x0C a 0x2 en todos los AWG
  - Convierte type2 0x29BD->0x1BD y 0x1B5->0x1BD en +0x38 y +0x3C
  - Convierte sombras 0x1B4 -> 0x190 en +0x38 y +0x3C
  - Aplana la jerarquia: reindexa grp (+0x30) de bone index a grupos
    secuenciales (las sombras -> 0xFFFFFFFF)
  - Pone u34 (+0x34) = 0xFFFFFFFF
  - Re-mapea bones de vertices (bone en +16) por labels
  - Re-mapea bones de arms (mesh-ref blocks)

Uso:
  python port_b3_to_b1.py <awo_b3.bin> <azt_b3.bin> <awo_b1_ref.bin> <out.awo>
"""
import struct
import sys

U32 = struct.Struct('>I')


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
        if lab in b1_by_label:
            m[b3i] = b1_by_label[lab]
        else:
            m[b3i] = -1
    return m


def main():
    if len(sys.argv) < 5:
        print('Uso: port_b3_to_b1.py <awo_b3.bin> <azt_b3.bin> <awo_b1_ref.bin> <out.awo>')
        return
    awo = bytearray(open(sys.argv[1], 'rb').read())
    azt_b3 = open(sys.argv[2], 'rb').read()
    b1_ref = open(sys.argv[3], 'rb').read()
    out = sys.argv[4]

    # 1. Mapa de bones B3 -> B1 por labels
    b3l = labels_hd(awo)
    b1l = labels_hd(b1_ref)
    m = build_map(b3l, b1l)
    n_unmapped = sum(1 for v in m.values() if v < 0)
    print('Labels B3: %d | B1: %d | mapa: %d (unmapped: %d)' % (
        len(b3l), len(b1l), len(m), n_unmapped))

    amg_am = u32r(awo, 0x18)
    amg_tbl = u32r(awo, 0x1C)

    # 1b. Coleccionar todos los mesh part headers para aplanar la jerarquia.
    #   B3: grp (+0x30) = indice de bone (0,2,3,4,6,8...). B1: grp = indice de
    #   grupo secuencial (0-3) o 0xFFFFFFFF (sombra). Reindexar.
    #   Sombra B3 = t38/t3C == 0x1B4 -> grp 0xFFFFFFFF en B1.
    parts = []  # (awg_idx, hdr_pos_abs, grp, t38, t3c)
    for i in range(amg_am):
        awg = u32r(awo, amg_tbl + i * 4)
        if awg + 0x40 > len(awo):
            continue
        hdr_off = u32r(awo, awg + 0x20)
        hdr_count = u32r(awo, awg + 0x24)
        hdr_abs = awg + hdr_off
        for p in range(hdr_count):
            pos = hdr_abs + p * 0x50
            parts.append((i, pos, u32r(awo, pos + 0x30), u32r(awo, pos + 0x38), u32r(awo, pos + 0x3C)))

    bone_to_grp = {}
    next_grp = 0
    for i, pos, grp, t38, t3c in parts:
        if t38 == 0x1B4 or t3c == 0x1B4:
            continue  # sombra -> 0xFFFFFFFF
        if grp not in bone_to_grp:
            bone_to_grp[grp] = next_grp
            next_grp += 1
    print('Aplanado: %d bones -> %d grupos secuenciales' % (len(bone_to_grp), next_grp))

    tot_flag = tot_type = tot_grp = tot_u34 = tot_vert = tot_arm = 0
    for i in range(amg_am):
        awg = u32r(awo, amg_tbl + i * 4)
        if awg + 0x40 > len(awo):
            continue

        # 2. Flag +0x0C -> 0x2
        if u32r(awo, awg + 0x0C) != 0x2:
            struct.pack_into('>I', awo, awg + 0x0C, 0x2)
            tot_flag += 1

        # 3. Type2 de mesh part headers: B3 -> B1
        #    +0x38: 0x1B5 -> 0x1BD, 0x1B4 (sombra) -> 0x190
        #    +0x3C: 0x29BD -> 0x1BD, 0x1B4 (sombra) -> 0x190
        hdr_off = u32r(awo, awg + 0x20)
        hdr_count = u32r(awo, awg + 0x24)
        hdr_abs = awg + hdr_off
        for p in range(hdr_count):
            pos = hdr_abs + p * 0x50
            t38 = u32r(awo, pos + 0x38)
            t3c = u32r(awo, pos + 0x3C)
            shadow = (t38 == 0x1B4 or t3c == 0x1B4)
            # +0x38 type2
            if t38 == 0x1B5:
                struct.pack_into('>I', awo, pos + 0x38, 0x1BD)
                tot_type += 1
            elif t38 == 0x1B4:
                struct.pack_into('>I', awo, pos + 0x38, 0x190)
                tot_type += 1
            # +0x3C type2
            if t3c == 0x29BD:
                struct.pack_into('>I', awo, pos + 0x3C, 0x1BD)
                tot_type += 1
            elif t3c == 0x1B4:
                struct.pack_into('>I', awo, pos + 0x3C, 0x190)
                tot_type += 1
            # grp (+0x30): aplanar jerarquia. Sombra -> 0xFFFFFFFF
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
            # u34 (+0x34): B1 siempre 0xFFFFFFFF
            u = u32r(awo, pos + 0x34)
            if u != 0xFFFFFFFF:
                struct.pack_into('>I', awo, pos + 0x34, 0xFFFFFFFF)
                tot_u34 += 1

        # 4. Re-mapear bones de vertices (bone en +16)
        sec_rel = u32r(awo, awg + 0x28)
        sec_sz = u32r(awo, awg + 0x2C)
        sec = awg + sec_rel
        for v in range(sec_sz // 44):
            q = sec + v * 44
            bone = u32r(awo, q + 16)
            if bone in m and m[bone] >= 0 and m[bone] != bone:
                struct.pack_into('>I', awo, q + 16, m[bone])
                tot_vert += 1

        # 5. Re-mapear bones de arms (mesh-ref blocks)
        sec = awg + sec_rel
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
    print('TOTAL: flag=%d type2=%d grp=%d u34=%d verts=%d arms=%d. Guardado %s (%d bytes)' % (
        tot_flag, tot_type, tot_grp, tot_u34, tot_vert, tot_arm, out, len(awo)))
    print('AZT B3: %d bytes (copiar a 2451 si cabe, sino usar el del B1)' % len(azt_b3))


if __name__ == '__main__':
    main()
