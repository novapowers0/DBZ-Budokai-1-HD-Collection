# Investigación: Blackout de entrada al modo Duelo (~4.5s)
> Copyright (c) NovaPowers. Released under the MIT License. Firmado por NovaPowers.
>

> **ESTADO: CERRADA (13/08/2026)** — diagnosticado y documentado. No bloquea la
> jugabilidad. El fix de frustum clipping NO se aplicó (riesgo de regresión); pasa
> a mejoras pendientes.
> Log analizado: `docs/logs/dbz1_gpu_diag_2100_backup.log` (run 21:00 del 10/08/2026).

---

## 1. Síntoma

Entrada a batalla (duelo) = blackout de **240 frames (~4.5s)** en negro puro
(los menús solo 60). Tras el blackout TODO se renderiza bien; solo molesta la
duración. Confirmado por el usuario. En **Xenia el clash SÍ muestra animaciones**
(personajes entrando, aura) → el recompilador falla en reproducir esa animación.

## 2. Hechos duros (del log)

- **45 fps y 180-181 draws/frame en AMBAS fases** — descartado doble-presente/100Hz.
- **Los comandos del frame son byte-idénticos** en blackout y fight.
- **HostTexContent** (RTs):
  - Blackout: RT personaje msaa2 (`0x1F35F000`) y feed del presente (`0x1EFC7000`)
    = **0%** (negro puro). Fondo (`0x1DA29000`) = 99% en ambas fases.
  - Fight: RT personaje 99%.
- **Cada píxel negro = `0xFF000000` exacto** (alpha=1 + RGB=0), 921600 px = 1280×720
  → **uniforme de negro opaco**, no contenido parcial. Alpha intacto en ambas fases.
- El draw del personaje del intro corre **~1000 veces** con `vs=54728E4E/ps=4DFCBC49`
  (bloom/glow) + `20E1ADA4/F7D7B271` (mesh skinned) + `929B371C/BCB144D5` (aura) +
  `D0D07B29/054DB27F`, a **pitch=1280 msaa=0**. El shader del combate es
  `1E6883FC/A4A965C1` (passthrough) a pitch=640 msaa=2, que solo aparece tras el blackout.
- **vsM (matriz de transformación)** durante blackout: `[0]=(1.78,-0.0035,0.0023,0.0023)`
  = **casi-identidad diagonal**. En combate: rotación+traslación completas.
- **clip_disable=0 (frustum ACTIVO)** en los shaders del intro (F7D7=475, BCB1=1428,
  4DFC=33...); **clip_disable=1** en los que se ven (A4A9=33, F5F4=33, 6E57=34).
- Constantes de pixel shader (psC[3]/[249]/[20]) **idénticas** en blackout y combate.
- `FrontbufferRtReadback` solo captura cada 60 presents (~1.4s) → valores stale; el
  presente sigue a las texturas en tiempo real (descartado el desfase de 0.4s).

## 3. Hipótesis descartadas (con datos)

| Hipótesis | Por qué se descartó |
|---|---|
| Double-present / 100Hz | 45 fps + 180 draws en ambas fases |
| Presente no se resuelve / RT sin dueño | ResolveSrc + DumpRT encuentran RT base=0 msaa=0 siempre |
| Fade por constantes de shader | psC idénticas blackout vs fight |
| Compilación async de shaders | Blackout de 240f en **CADA duelo** (seq=3 y seq=4) → determinista |
| Matrices cero → fade-in guionado | El diag capturaba un **quad fullscreen** `(-0.5,-0.5,1.0)`, no el mesh 3D |
| Bug de traducción DXBC→DXIL / blend / alpha | ucode correcto, blend/alpha idénticos al combate |

## 4. CAUSA RAÍZ (confirmada 13/08/2026)

**El blackout es la animación de entrada del duelo: el personaje comienza con `vsM`
casi-identidad (diagonal), que lo deja en posición/escala degenerada en el origen.
Con `clip_disable=0` (frustum recorte ACTIVO), D3D12 recorta la geometría fuera de
[-w,w] → el personaje NO rasteriza píxeles → RT con alpha=1 RGB=0 (negro opaco).
La animación transiciona `vsM` a la matriz real en 240 frames.**

- El shader del personaje del intro opera a `cbase=0 pitch=1280 msaa=0`; el del
  combate (`A4A965C1` passthrough) a `pitch=640 msaa=2`. El contenido 1280/msaa0 no
  se resuelve al RT que se presenta.
- En Xenia el mismo juego muestra la animación (personajes entrando) porque resuelve
  ambos RTs correctamente y/o no recorta igual.

## 5. Fix candidato (NO aplicado — pendiente)

En `GetHostViewportInfo` (draw.cpp:341): forzar `clip_disable=true` (viewport gigante +
offset en VS) para todos los draws, o tratar específicamente los draws con
`clip_disable=0` + posición degenerada. **Riesgo**: romper recortes legítimos en todo
el juego. Requiere pruebas de regresión.

Otras reversiones ya aplicadas durante la investigación (dejar como están):
- `async_shader_compilation` restaurado a default `true`.
- Spin-wait revertido (causaba bajones de FPS).

## 6. Próximos pasos si se retoma

1. Instrumentar `RexDiagLogResolveSource` (render_target_cache.cpp:72-81) + quitar
   throttle del DumpRT para correlacionar el 2º `ResolveSrc→0x1EFC7000` con su contenido.
2. Volcar el contenido host de `0x1EFC7000` justo tras cada 2ª ResolveSrc (alineado a frame).
3. Volcar `0x1F35F000` justo después del draw del personaje en Fase A (¿escribe o no?).
4. Probar `draw_resolution_scale=1` (720p nativo) para ver si el resolve msaa0↔msaa2 desaparece.

## 7. Notas operativas

- El binario ejecutado es `build/Release/dbz1.exe` (10/08 21:24); la raíz `dbz1.exe`
  es el original sin tocar. Build: `cmake --build build --config Release`.
- Código de diag ya existente: `command_processor.cpp:4029-4082` (SceneVIdx/SceneConst).
- Los logs históricos (148MB), crash dump y .bmp/.png de diagnóstico se eliminaron en la
  reorganización (11/08); usar `build/Release/dbz1_gpu_diag.log` fresco para nuevos análisis.