"""Rutas portables para las herramientas de DBZ Budokai HD Collection.

Copyright (c) NovaPowers. Released under the MIT License.
Firmado por NovaPowers.

Evita rutas absolutas de usuario (C:\\Users\\...): todo se deriva del propio
repo o de variables de entorno. Reglas:
  - assets/          directorio de assets del B1 (region us/eu)
  - tools/           xbcompress/xbdecompress
  - DBZ3_ROOT        variable de entorno con la raiz del proyecto B3
  - B3 por defecto:  carpeta hermana "DBZ Budokai 3 HD Collection"
"""
import os

HERE = os.path.dirname(os.path.abspath(__file__))
# 'mod center hd' -> raiz del repo
REPO = os.path.dirname(HERE)
ASSETS = os.path.join(REPO, 'assets')
TOOLS = os.path.join(REPO, 'tools')

B1_AFS_NAMES = ('data_us.afs', 'data_sp.afs', 'data_fr.afs',
                'data_en.afs', 'data_ge.afs', 'data_it.afs')


def find_b1_afs(region_dir=None):
    """Primer data_*.afs de personaje existente (region us/eu)."""
    dirs = [region_dir] if region_dir else [
        os.path.join(ASSETS, 'us'), os.path.join(ASSETS, 'eu')]
    for d in dirs:
        for name in B1_AFS_NAMES:
            p = os.path.join(d, name)
            if os.path.isfile(p):
                return p
    return None


def b3_root():
    """Raiz del proyecto B3: DBZ3_ROOT si existe, si no la carpeta hermana."""
    env = os.environ.get('DBZ3_ROOT')
    if env and os.path.isdir(env):
        return env
    sibling = os.path.join(os.path.dirname(REPO), 'DBZ Budokai 3 HD Collection')
    if os.path.isdir(sibling):
        return sibling
    return None


def find_b3_afs():
    """data_cmn.afs del B3 (us/eu)."""
    root = b3_root()
    if not root:
        return None
    for region in ('us', 'eu'):
        p = os.path.join(root, region, 'data_cmn.afs')
        if os.path.isfile(p):
            return p
    return None


def find_tool(name):
    """Busca una herramienta (xbcompress.exe / xbdecompress.exe) en:
    tools/, DBZ1_XBCOMP_DIR, o junto al proyecto B3."""
    candidates = [
        os.path.join(TOOLS, name),
    ]
    env = os.environ.get('DBZ1_XBCOMP_DIR')
    if env:
        candidates.append(os.path.join(env, name))
    root = b3_root()
    if root:
        candidates.append(os.path.join(
            root, 'mod center',
            'Xbox 360 Compression - Decompression tool from the XBOX Development Kit',
            name))
    for c in candidates:
        if os.path.isfile(c):
            return c
    return None
