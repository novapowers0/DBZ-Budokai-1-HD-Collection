"""build_awg_hd_full.py — CORRECCIÓN DEFINITIVA (2026-08-15, RE verificada).

HALLAZGO QUE EXPLICA TODOS LOS FALLOS v1-v18: 
  - El sec34 NO es un "pool de posiciones stride 16" (error de la sesión 7).
  - El sec34 es el vértice de 44B del layout de la sesión 5, y su offset
    en el header AWG0 es RELATIVO al AWG0, no absoluto.

  AWG0 header (+0x50):
    +0x28 sec_off (REL AWG0) -> absolute = AWG0 + val   (ej 0xB20+0x24D0=0x2FF0)
    +0x2C sec_size          -> n_sec = sec_size//44
    +0x30 post_off (REL AWG0)-> absolute = AWG0 + val
    +0x34 post_size
    +0x38 siguiente zona (REL AWG0)
    +0x3C bones count
    +0x40 nombre

  VÉRTICE HD (44B, layout sesión 5, BONES VÁLIDOS 1-34 verificado):
    +00  pos.x +04 pos.y +08 pos.z
    +12  weight
    +16  BONE index (u32)   <- ES AQUÍ, no "en +16 del stride 16"
    +20  nrm.x +24 nrm.y +28 nrm.z
    +32  0xFFFFFFFF
    +36  blend/scale
    +40  uv

  El mesh group del bin nativo (labels + 12 headers + 42 ejes + 42 bloques
  + 42 arms + IB + zona post) se copia ÍNTEGRO: es la plantilla coherente
  del desarrollador. SOLO se sustituyen las posiciones por slot.

ESTRATEGIA (validada por v8 + estructura real):
  1. Copiar el bin HD nativo COMPLETO (mesh group + IB + UVs/normales).
  2. Construir el pool PS2: verts del skin transformados a WORLD con las
     matrices PS2 (para buscar el vecino en espacio mundial correcto).
  3. Por cada slot nativo: leer su bone real (+16) y su posición local;
     pasarlo a world con la mat HD del hueso; buscar en el pool el vertice
     PS2 world MAS CERCANO; transformar ese world a local del hueso con
     inv_rigid y escribirlo en +0..+12. Si el vecino queda > UMBRAL, se
     DEJAN las coords nativas.

Uso:
  python build_awg_hd_full.py <bin_hd_base_mismo_personaje.awo> <modelo_ps2.amb> <out.bin>
"""
import struct
import sys
import os as _os
import sys as _s

_here = _os.path.dirname(_os.path.abspath(__file__))
_s.path.insert(0, _here)
_s.path.insert(0, _os.path.join(_here, '..', 'parsers', 'lib_ps2'))

from obj_to_awg_hd import (u32r, f32r, build_world_mats_ps2,
                           build_hd_world_mats, parse_ps2_model,
                           apply_mat, inv_rigid, quat_to_mat, mat_mul)


def labels_hd(b):
    """Labels del bin HD (AWO)."""
    n = u32r(b, 0x10)
    off = u32r(b, 0x24)
    out = {}
    for bi in range(n):
        s = b[off + bi * 32: off + bi * 32 + 32].split(b'\x00')[0]
        s = s.decode('latin1', 'ignore')
        if s:
            out[bi] = s
    return out


def main():
    if len(sys.argv) < 4:
        print('Uso: build_awg_hd_full.py <bin_hd_base_mismo_personaje.awo> <modelo_ps2.amb> <out.bin>')
        return
    base = bytearray(open(sys.argv[1], 'rb').read())
    ps2 = open(sys.argv[2], 'rb').read()
    out = sys.argv[3]

    if ps2[0:4] == b'#AMB':
        ps2 = ps2[0x40:]

    # ---- 1. Modelo PS2 ----
    model, amgs = parse_ps2_model(ps2)
    a = amgs[0]
    print('PS2 AMG0 %s: bone_am=%d nv=%d parts=%d' % (
        a['label'], a['bone_am'], a['nv'], len(a['parts'])))
    mats_src, _ = build_world_mats_ps2(ps2, amo0=model.amo0)

    # ---- 2. Labels y bone_map PS2 -> HD por label ----
    base_labels = labels_hd(base)
    base_by_label = {l: i for i, l in base_labels.items()}
    ps2_labels = {}
    for off in model.amg_offsets():
        amg0 = model.amo0 + off
        bone_am = struct.unpack('<I', ps2[amg0 + 0x10:amg0 + 0x14])[0]
        lo = struct.unpack('<I', ps2[amg0 + 0x1C:amg0 + 0x20])[0]
        for bi in range(bone_am):
            s = ps2[amg0 + lo + bi * 16: amg0 + lo + bi * 16 + 16]
            s = s.split(b'\x00')[0].decode('latin1', 'ignore')
            if s and bi not in ps2_labels:
                ps2_labels[bi] = s
    bone_map = {}
    for ps2i, lab in ps2_labels.items():
        suf = lab.split('_', 1)[1] if '_' in lab else lab
        matched = 0
        for blab, bidx in base_by_label.items():
            if blab.endswith(suf) or blab.replace('XTSH_', 'TSH_').endswith(suf):
                bone_map[ps2i] = bidx
                matched = 1
                break
        if not matched:
            bone_map[ps2i] = 0
    for bi in range(1, 50):
        if bi in bone_map:
            continue
        for cand in (bi - 1, bi + 1, bi - 2, bi + 2):
            if cand in bone_map:
                bone_map[bi] = bone_map[cand]
                break
        if bi not in bone_map:
            bone_map[bi] = 0
    print('Mapa bones PS2->HD: %d' % len(bone_map))

    # ---- 3. World mats del HD (ejes) ----
    AWG0 = u32r(base, u32r(base, 0x1C))
    mats_dst = build_hd_world_mats(base, AWG0)
    print('Mats dst=%d' % len(mats_dst))

    # ---- 4. Skin del PS2 (bone, weight, coords locales) por vertice ----
    skin_map = {}
    for amg_idx, am in enumerate(amgs):
        amg0 = am['amg0']
        axes_loc = struct.unpack('<I', ps2[amg0 + 0x14:amg0 + 0x18])[0]
        parts = am['parts']
        part_ranges = []
        for pi, p in enumerate(parts):
            md = p['po'] + 0xA0
            vstart = md + 0x20
            part_ranges.append((pi, vstart, len(p['verts']) * 48))
        for bi in range(am['bone_am']):
            e0 = amg0 + axes_loc + bi * 80
            p34 = struct.unpack('<I', ps2[e0 + 0x34:e0 + 0x38])[0]
            if not p34:
                continue
            arm = amg0 + p34
            rig_ptr = struct.unpack('<I', ps2[arm + 8:arm + 12])[0]
            if not rig_ptr:
                continue
            r = amg0 + rig_ptr
            chunk_amnt = struct.unpack('<I', ps2[r + 12:r + 16])[0]
            for i in range(chunk_amnt):
                c = r + 16 + i * 32
                weight = struct.unpack('<f', ps2[c:c + 4])[0]
                ch_len = struct.unpack('<I', ps2[c + 4:c + 8])[0]
                ch_loc = struct.unpack('<I', ps2[c + 8:c + 12])[0]
                if not ch_loc:
                    continue
                for e in range(ch_len):
                    entry = amg0 + ch_loc + e * 32
                    coords = struct.unpack('<fff', ps2[entry:entry + 12])
                    voff = struct.unpack('<I', ps2[entry + 12:entry + 16])[0]
                    abs_off = amg0 + voff
                    for pi, vstart, vlen in part_ranges:
                        if vstart <= abs_off < vstart + vlen:
                            vi = (abs_off - vstart) // 48
                            skin_map[(amg_idx, pi, vi)] = (bi, weight, coords)
                            break
    print('Skin PS2: %d verts' % len(skin_map))

    # ---- 5. Pool PS2 world por bone (SOLO AMG0, como v8) ----
    import math
    ps2_by_bone = {}   # bone_dst -> (wx,wy,wz,weight)
    all_ps2_world = []
    for pi, p in enumerate(a['parts']):
        for vi, v in enumerate(p['verts']):
            sk = skin_map.get((0, pi, vi))
            if not sk:
                continue
            bone_ps2, weight, coords = sk
            bone_dst = bone_map.get(bone_ps2, 0)
            Ms, ps_ = mats_src.get(bone_ps2, (None, None))
            if Ms is not None:
                wx, wy, wz = apply_mat(Ms, ps_, coords)
            else:
                wx, wy, wz = coords
            if math.isnan(wx) or math.isnan(wy) or math.isnan(wz):
                continue
            item = (wx, wy, wz, weight, bone_dst)
            ps2_by_bone.setdefault(bone_dst, []).append(item)
            all_ps2_world.append(item)
    print('Verts PS2 por bone: %d (pool global: %d)' % (
        sum(len(v) for v in ps2_by_bone.values()), len(all_ps2_world)))

    # decimacion voxel
    VOXEL = 0.08
    cell = VOXEL
    seen = set()
    pool_global = []
    for (wx, wy, wz, weight, pb) in all_ps2_world:
        key = (int(wx / cell), int(wy / cell), int(wz / cell), pb)
        if key in seen:
            continue
        seen.add(key)
        pool_global.append((wx, wy, wz, weight, pb))
    pool_by_bone = {}
    for item in pool_global:
        pool_by_bone.setdefault(item[4], []).append(item)
    print('Pool global decimado: %d' % len(pool_global))

    # ---- 6. Rellenar sec34 slot a slot (VÉRTICE 44B, offset REL AWG0) ----
    # sec_off es RELATIVO al AWG0 (la RE de la sesión 7 decía "absoluto" y
    # eso ROMPIA todo: el body real está en AWG0+0x24D0 = 0x2FF0).
    sec_rel = u32r(base, AWG0 + 0x28)
    sec_abs = AWG0 + sec_rel
    sec_sz = u32r(base, AWG0 + 0x2C)
    n_sec = sec_sz // 44
    VERT_LEN = 44
    print('sec34 base: %d verts (stride 44, abs 0x%X)' % (n_sec, sec_abs))

    UMBRAL = 1.5
    n_replaced = 0
    n_native = 0
    n_skip = 0
    for i in range(n_sec):
        o = sec_abs + i * VERT_LEN
        if o + VERT_LEN > len(base):
            break
        # layout sesión 5: pos@+0, weight@+12, BONE@+16
        w_native = struct.unpack('>f', base[o + 12:o + 16])[0]
        if w_native == 0.0:
            n_skip += 1
            continue
        bone_dst = struct.unpack('>I', base[o + 16:o + 20])[0]
        if bone_dst > 63:
            # dato basura? mantener nativo
            n_native += 1
            continue
        # POOL GLOBAL puro (validado por v8): el bone_map por labels del B1
        # PS2 no coincide con los bone indices del sec34 HD, y restringir por
        # bone empeora la cobertura (47% vs 95% del pool global).
        pool = pool_global
        if not pool:
            n_native += 1
            continue
        # world del slot nativo (coords locales nativas + mat del hueso)
        M, p = mats_dst.get(bone_dst, (None, None))
        nx, ny, nz = struct.unpack('>3f', base[o:o + 12])
        if M is not None:
            swx, swy, swz = apply_mat(M, p, (nx, ny, nz))
        else:
            swx, swy, swz = nx, ny, nz
        # vecino PS2 world mas cercano
        best = None
        bd = 1e18
        for (wx, wy, wz, weight, pb) in pool:
            dd = (swx - wx) ** 2 + (swy - wy) ** 2 + (swz - wz) ** 2
            if dd < bd:
                bd = dd
                best = (wx, wy, wz)
        if best is None:
            n_native += 1
            continue
        dist = math.sqrt(bd)
        if dist > UMBRAL:
            n_native += 1
            continue
        wx, wy, wz = best
        # world PS2 -> local del hueso destino (inv_rigid)
        if M is not None:
            iM, ip = inv_rigid(M, p)
            lx, ly, lz = apply_mat(iM, ip, (wx, wy, wz))
        else:
            lx, ly, lz = wx, wy, wz
        # escribir SOLO las 3 coords (mantener weight/bone/uv/nrm)
        base[o:o + 12] = struct.pack('>3f', lx, ly, lz)
        n_replaced += 1
    print('Verts: reemplazados=%d nativos=%d skip=%d (total %d)' % (
        n_replaced, n_native, n_skip, n_sec))

    open(out, 'wb').write(bytes(base))
    print('Guardado: %s (%d bytes)' % (out, len(base)))


if __name__ == '__main__':
    main()