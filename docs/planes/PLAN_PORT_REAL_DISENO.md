# PLAN: PORT REAL DE PERSONAJES AL B1 HD (diseño sesión 6-7)
> Copyright (c) NovaPowers. Released under the MIT License. Firmado por NovaPowers.
>

> 2026-08-15. Diseño para portar personajes DISTINTOS (Goku SS2, Gohan Kai) al
> B1 HD, tras confirmar el bloqueador del mesh group.
> ⚠️ La sección 4b/c contiene RE PRE-v10 (stride 16) ya CORREGIDA en AGENTS.md:
> el sec34 real es **44B stride** (`pos+weight+BONE u32+nrm+FFFF+uv`) y los
> offsets AWG0 son **RELATIVOS al AWG0**. Mantener AGENTS.md como fuente.

---

## 1. EL PROBLEMA (bloqueador confirmado)

El runtime B1 HD dibuja con el **mesh group/IB nativo del bin anfitrión**, nunca
con la geometría inyectada. Inyectar coords solo funciona cuando la geometría es
casi idéntica (mismo personaje, v8/v12). Reconstruir el mesh group a mano falló
3 veces (caos, deforme, crash) por no conocer la relación EXACTA entre mesh part
headers ↔ ejes ↔ arms.

## 2. 🔴 HALLAZGO CLAVE: EL JSON DE .aerithdevs DOCUMENTA EL FORMATO

`modding resources discord\research\00000002-00000002-b3.AMO.json` revela la
estructura jerárquica del AMG/AMO HD (parseado por la herramienta de .aerithdevs):

```
$AMO:{ $AMG000:{ $flag,
  $data000:{                      <- HUESO (eje/mesh-ref block)
    $ref: [hijos...],  $flag: &6000020F,  $mtx: quat+pos,
    $grp00:{                      <- MESH PART HEADER
      $data00: [type1/type2],     <- 0x1B5/0x29BD (B3)
      $sub00: <sub-mesh: índices + vértices <bone, peso, pos, uv, nrm, color>>,
      $sub01: ...                 <- más sub-meshes
    }
  }
}
```

**Conclusión**: el formato HD NO es "sec34 + IB plano" — es **jerárquico**
`$data(hueso) → $grp(mesh part) → $sub(sub-meshes) → verts con bone+peso`.
Eso explica por qué el mesh group reconstruido no funcionaba: faltaba la
estructura de sub-meshes y la relación exacta hueso↔submesh.

## 3. LA VÍA CORRECTA (3 opciones)

- **Opción A — Adaptar OBJ to AMG v0.92 → generador HD (RECOMENDADA):** OBJ to
  AMG YA genera el AMG con `$data/$grp/$sub` correcto desde un OBJ. Solo falta
  re-layout PS2→HD: type2 0x29BD→0x1BD/0x11BD, LE→BE, verts 48B→44B.
- **Opción B — Parser de .aerithdevs (FBX/JSON):** AMO/AMB → JSON+FBX → editar
  en Blender → re-importar. El pipeline de la comunidad para modelos externos.
  ⚠️ Herramienta NO disponible local ni pública (los JSON de research/ son muestra).
- **Opción C — RE profunda del mesh group HD:** comparar bin nativo con el JSON
  para deducir la estructura binaria exacta de `$data/$grp/$sub`. Más lento.

## 4. PLAN DE IMPLEMENTACIÓN

### Fase 1 — Validar el formato
- [x] Analizar los JSON de .aerithdevs (2 formatos: `$AMO` b3 y `$model` XGOK B1)
- [ ] Mapear la estructura `$data→$sub→verts` del JSON al binario del sec34

### Fase 2 — Re-layout PS2→HD con sub-meshes
- [ ] Adaptar OBJ to AMG v0.92 (Python) para generar `$data/$grp/$sub` en HD
- [ ] Generar un AWG0 de prueba (TSH B2) con sub-meshes → probar en juego

### Fase 3 — Port real
- [ ] Portar Gohan Kai (B2) → slot TSH; Goku SS2 (B2) → slot Gohan
- [ ] Validar geometría + animaciones (mapeo de bones)

### Fase 4 — Traductor universal
- [ ] B1/B2 PS2 → HD directo (re-layout); B3 PS2 → HD (vía b3iw_to_b1_ps2.py);
      modelos externos (EMD/FBX) → HD (vía EMD to AMG / .aerithdevs)

## 4b/4c. 🔴 MAPEO DEFINITIVO DEL AWG0 (SESIÓN 7) — VÁLIDO salvo el stride

**Verificado en TSH nativo slot_2450 (AWG0@0xB20):**

```
#AWG0 header (0x50):
  +0x1C rel nombre (XTSH_BODY@0xB60)  +0x28 sec_off (REL AWG0)
  +0x2C sec_size → n_sec = sec_size//44
  +0x30 post_off (REL)  +0x34 post_size (IB u16)  +0x38 siguiente zona
  +0x3C bones count  +0x40 nombre (16B)

Zona mesh group (0xB60..0x24D0):
  [0xB60..0x10A0] label XTSH_BODY + 48 labels de huesos (0x20 c/u)
  [0x10A0..0x1410] 12 mesh part headers (0x50B c/u): grp_idx 0/1/2 + type2
                   0x1BD/0x11BD (malla); grp 0xFFFFFFFF + type2 0x190/0x199 (sombra)
  [0x1460..0x2180] 42 ejes (0x50B c/u)
  [0x2180..0x24C8] 42 arms (0x14 c/u)
sec34 (stride 44, 4272 slots): 0x2FF0..0x30E30  (AWG0 + 0x24D0)
zona post (IB u16 + sub-mesh): 0x30E30..0x36B6A
bones: 0x36B6A..0x36C00
```

**Eje (0x50B)**: quat(x,y,z,w)@+0 + pos@+10 + 4×1.0@+20 + sello@+30
(0x6000020F raíz, 0x9000020C/0x8000020C mesh, 0x1000020C transición, 0x204/0x205
shadow, 0x9000020E/0x9800020E/0x90000208/0x80000208/0x10000208) + arm_ptr@+34
(REL AWG0) + child/sibling/parent@+38/+3C/+40.
⚠️ Leer desfasado +0x10 da falsa impresión de sello en +0x20 (19 ejes fantasma).

**Arm (0x14)**: `[bone, fin, 0, ini, 0]` — ini/fin = byte offsets DENTRO del IB
(zona post). Ranges se solapan. Solo 8 bones con mesh: 0[6576..7088], 9[6640..7968],
16[6704..8080], 20[6768..8192], 24[6832..8496], 27[6896..8704], 31[6960..8816],
37[7024..9120]. El arm del bone 20 existe pero su eje es "oculto" (sin sello) →
leer los 42 arms como zona contigua desde el arm_ptr del eje raíz.

**Lo que build_awg_hd_full.py tenía mal (pre-v10)**: sec34 como stride 16 + IB
separado en +0x30 + mesh group desordenado. La versión v12 usa sec34 44B nativo +
pool world PS2 (ver AGENTS.md).

## 5. RECURSOS DISPONIBLES

| Recurso | Ubicación | Uso |
|---|---|---|
| OBJ to AMG v0.92 | `src_comunidad/` + `modding resources/tools` | Generar AMG desde OBJ |
| AMG to OBJ V2 | `modding resources/tools` | Convertir HD→OBJ |
| EMD to AMG v0.90 | `modding resources/tools` | Modelos EMD |
| AMBStudio | `modding resources/tools` | Empaquetar AMB |
| JSON .aerithdevs | `modding resources/research/` | Formato HD documentado |
| Tutorial_Custom_Character | `modding resources/tutorials` | Proceso de la comunidad |
| AMO Compiler/Decompiler | `src_comunidad/` | Parseo/build AMO |
| B3-IW Converter | `modding resources/tools` | B3/IW→B1 |

## 6. PRÓXIMO PASO INMEDIATO

1. **Completar el mapa del mesh group**: relación exacta mesh part header
   (grp_idx + patrón de sub-meshes $data→$sub→verts) ↔ ejes ↔ arms.
2. **Corregir build_awg_hd_full.py** con el layout v12 (sec34 44B + offsets REL
   + IB en zona post + arms apuntando a rangos del IB + ejes a +0x30/+0x34).
   → Con eso se valida la retopología completa.
3. Alternativa validada para mismo personaje: **v12** (sec34 nativo + pool world
   PS2), ya instalado en `mods/test_tsh_b2_stride16` (95% de slots, deformidades
   en extremidades).