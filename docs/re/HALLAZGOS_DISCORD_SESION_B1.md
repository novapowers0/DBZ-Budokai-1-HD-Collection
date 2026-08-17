# HALLAZGOS DEL DISCORD "DRAGON BALL Z BUDOKAI MODDING COMMUNITY" — SESIÓN B1
> Copyright (c) NovaPowers. Released under the MIT License. Firmado por NovaPowers.
>

> Resumen consolidado del análisis de la comunidad por la sesión de Budokai 1.
> Fecha: 14/08/2026. Recursos en `modding resources discord\` (proyecto B1).

---

## 1. LA CONVERSIÓN B3/IW → B1 ES RE-LAYOUT DE HEADERS (NO RE-RIGGING)

**HALLAZGO MÁXIMO.** El conversor oficial de la comunidad (`B3-IW_to_Budokai1_AMO_FacialSplit_TEST.exe`)
descompilado (PyInstaller → bytecode 3.10 → xdis) demuestra que pasar un modelo
B3/IW a B1 **solo reescribe los headers de mesh part** con valores fijos:

```
B3/IW mesh part header:  B5 01 00 00 BD 29   (estándar)
                         B4 01 00 00 B4 01   (facial)
→ B1:                    BD 01 00 00 BD 01   (estándar)
                         B4 62 00 00 BD 29   (facial)
+ offset+12: FF FF FF FF
+ offset+14..24: STANDARD_FIELD_14/18 (0.8665 / -0.1838) o FACIAL (1.0559/0.2235)
+ offset+19: 0
+ offset+32..64: floats 0.8, 0.85, 1.0, 127.27, 128.0
```

Detalle completo en `docs\CONVERSOR_B3IW_A_B1_COMUNIDAD.md`.

**Implicación para el port HD**: el mesh part header del AWO HD es el mismo
que el PS2. Nuestros experimentos de re-rigging B3→B1 (remap de huesos,
poses, etc.) eran innecesarios para el paso básico de conversión. El paso
correcto es reescribir los headers — igual que hace la comunidad.

## 2. ESTRUCTURA AMO/AMG CONFIRMADA (SleepyZay, budokai_111616.ms)

El script de 3ds Max de SleepyZay documenta el formato PS2 (idéntico al HD):

- **AMO header**: `AMO`(4) + header_len + +0x10 count + +0x14 AmoData_Start
  + +0x18 AmgCount + +0x1C AmgOffsetTable + +0x20 Bonecount
  + +0x24 BoneNameTableOffset
- **Bone names**: tabla de 0x20 (32) bytes por nombre
- **AmoData** (bone table): entries de 32B: boneID, boneTable, tableOffset,
  tableOffset2, tableOffset3, +0xC
- **AMG header**: `AMG`(4) + header_len + unk + unkcount + BlockCount
  + BlockStart + unk + NameOffset
- **Mesh parts** (ModelNumber + 4 modelOffset):
  - z==1: mesh data (meshCount, meshOffsetTable, meshOffset)
  - z==20: **WEIGHTS (skinning)**: tableCount → por entry: ukw(float),
    weightCount, weightOffset; luego weightData(3 floats) + ukwOffset +
    wd2(3 floats) + null ← **el rig por hueso del PS2**
- **Submeshes**: FaceType (0=tripletes, 1=strips), VertCount, y los vértices
  según MeshType[1]:
  - 0xbd/0xfd/0x3d: pos3+null+nrm3+null+uv2+ukw+null (64B)
  - 0xb5/0xb6/0xf5: pos3+null+nrm3+null+uv2+null+4 (48B)
  - 0x199: pos3+null+nrm3+null (32B)
  - 0xb4/0xa4/0x99/0x92/0x19: pos3+null+uv2+8 (32B)
  - 0x90: pos3+null (16B)
- **Bones**: quaternion (c11..c14, c14*-1) + posición (c21..c23), +0x20

## 3. VÉRTICE CONFIRMADO (AMO.json de .aerithdevs)

El dump `00000002-00000002-b3.AMO.json` / `0001-0001.AMO._skel-1.json` muestra
el vértice en texto:

```
<$data00N, peso, $v:F[pos.xyz] $u:F[uv.xy] $n:F[normal.xyz] $c:B[color]>
```

- `$data00N` = **referencia al hueso** del vértice
- `peso` = weight (0..1)
- `$mtx:F[quat + pos]` = matriz del hueso
- Sello eje: `&6000020F`

## 4. TEMPLATE #AMB/#AWO/#AWG (B3_AMB_PS3.bt — 010 Editor)

Valida la estructura HD big-endian:
- `#AMB`: header + EntryCount + EntryStartPointer + entries (NextHeaderPointer)
- `#AWO`: numberOfBones, ptrtoConnections, numberOfAWGs, pointerAWGoffsets,
  ptrBoneNames, AWOunk_structure[numberOfBones] (0x20 c/u)
- `#AWG`: numberOfBones, rigging_data_ptr, unk_Count, ptrVertexBlock (vb2),
  VertexBlockSize, ptrFaceData (sec34), FaceDataSize
- `riggingData` = RotationX/Y/Z + unk + PositionX/Y/Z + unk + ScaleX/Y/Z + unk
  (**las matrices de pose de hueso SÍ existen**, en la zona del hueso)
- BoneNames[32] por hueso

## 5. PIPELINE DE .aerithdevs (PORT DE MODELOS EXTERNOS A BUDOKAI)

`port_test.zip` muestra el flujo:
```
AMO/AMB (B3) → .json (formato intermedio $model/$MO) + .fbx (para Blender)
             → editar en Blender → re-importar → AMO
```
Incluye `amo from DBH.json` (un modelo de Dragon Ball Heroes portado) y
`0001-0001.AMO.fbx`. Es la herramienta que permitirá portar modelos de
cualquier juego a Budokai — relevante para el futuro port HD.

## 6. RECURSOS DESCARGADOS PARA B1

- **381 archivos** descargados del Discord al `modding resources discord\` del
  proyecto B1 (research/tools/tutorials/models/rb2_reference).
- Claves:
  - `tools\B3-IW_AMO_Converter__Shadows.zip` (v1.5, conversor B3/IW→B1)
  - `tools\Model-Rig_Extractor.py` / `_v0.9.py` (rig PS2)
  - `tools\axis_data.py` (ejes/bones)
  - `tools\AMG_to_OBJ_V2.zip`, `OBJ_to_AMG_v0.92.zip` (edición Blender)
  - `tools\Budokai_B3_IW_B1_AMO_Converter.zip`
  - `research\B3_AMB_PS3.bt` (template 010)
  - `research\budokai_111616.ms`, `budokai_updated.ms` (3ds Max)
  - `research\00000002-00000002-b3.AMO.json`, `0001-0001.AMO._skel-1.json`
  - `research\Yamcha.AMO`, `BCGOKB00.a3b`, `bc18gb10.esk-amo.json`
  - `research\B1_Capsules`, `B1_Potraits_2.zip`
  - `tutorials\DBZ_B3_X360_-_Lesson_1...zip` (compresión X360)
  - `tutorials\DBZ_B3HD_-_Lesson_2_Texture_Edition.zip` (AZT/A3T)

## 7. PERSONAS CLAVE DE LA COMUNIDAD

- **.aerithdevs** — conversor de modelos externos a Budokai (Java,
  multi-plataforma). Header AWG del 360. port_test.zip + JSONs de esqueleto.
- **samueldoesstuff** — documenta el rig HD (ID hueso, inicio rig, chunks,
  weight, puntos, sub-puntos) y el port de modelos. Tutoriales YouTube.
- **SleepyZay** — script de 3ds Max del formato AMO/AMG completo.
- **gibzthekingofnothing** — bug de bone index del Zero Devs' Tool.
- **nexusthemodder** (Nexus-sama) — creador de herramientas (Budokai Modding
  Tool, Nexus shaders).

## 8. PRÓXIMOS PASOS SUGERIDOS PARA B1

1. **Aplicar la conversión de headers B3→B1 al pipeline HD** (script que
   reescriba los mesh part headers del bin HD B3 con las constantes de la
   comunidad) y probar en combate.
2. **Comparar el header B3 HD vs B1 HD real** (Krillin B3 vs Tenshinhan B1)
   para confirmar que los mesh part headers son idénticos en HD.
3. **Usar el pipeline de .aerithdevs** (FBX/JSON) si se decide portar un
   modelo externo o re-riggear correctamente.
4. **Extraer rig del PS2 con Model-Rig_Extractor.py** para entender los
   weights y sub-puntos en el formato que el HD necesita.

## 9. VERIFICACIÓN EN HD (14/08/2026) — LOS HEADERS HD DIFIEREN DEL PS2

Se intentó aplicar el hallazgo del conversor (re-layout de headers) al HD:

- **B1 Tenshinhan HD**: 71 mesh part headers con type1=0x1BD (`BD 01`), p.ej.
  @0x29249: `BD 01 F5 3F 4F 47 87 3F 80 00 00 00 ...` → **formato B1**.
- **B3 Gero HD**: NO tiene headers type1=0x1BD. Los candidatos `BD 29`
  (0x29BD) encontrados (@0x251F8) resultaron ser index data, no headers.
- Los mesh part headers del B3 Gero HD usan un formato distinto al B1
  (posiblemente por la distinta organización de AWGs).

**CONCLUSIÓN**: el re-layout de headers del conversor de la comunidad es para
PS2 (AMO). En HD, la diferencia entre mesh parts B3 y B1 no es solo el header
type1/type2 — requiere verificar la estructura del mesh part HD del B3
(organización de AWGs, campos +14/+18/+19, matriz). Esto se documenta como
**pendiente de RE** para el port B3→B1 HD.

El hallazgo principal sigue siendo válido: la conversión PS2 es re-layout de
headers, y las herramientas de la comunidad (Model-Rig_Extractor, AMG_to_OBJ,
B3-IW converter) están disponibles en `modding resources discord\`.
