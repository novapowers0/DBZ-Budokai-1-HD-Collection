"""Colores de piel por personaje B3 para el --tint-skin automatico.

Copyright (c) NovaPowers. Released under the MIT License.
Firmado por NovaPowers.

Hallazgo (20/08, leccion 35): algunos personajes del B3 (Dabura, Buu) modelan
la piel con un MATERIAL (mesh part +0x34==5) sobre una textura base GRIS, no
con una textura del color de la piel. Al portar a B1 (que no tiene material de
tintado) la piel sale del color gris de su textura -> descolorida.

El escaneo (analizadores/scan_skin_tint.py) detecta QUE personajes sufren esto
(texturas de piel predominantemente grises, skin_grey_majority=True), pero el
color real de piel NO se puede inferir de forma fiable del AZT (el color lo
aplica el material del B3, no la textura). Por eso se usa una TABLA curada con
el color de piel caracteristico de cada personaje.

Claves: codigo de personaje B3 (prefijo del label SIN la 'X' inicial), igual
que characters_db.py. Cada entrada es (r,g,b) del color de piel.

Para personajes no listados se usa SKIN_DEFAULT (piel humana estandar).
"""
import os

# Color de piel estandar (piel humana caucasica) para personajes no listados.
SKIN_DEFAULT = (235, 195, 165)

# Codigo de personaje B3 -> color de piel (r,g,b)
SKIN_COLORS = {
    # --- Buu (todos rosa) ---
    'BUL': (247, 150, 165),   # Majin Buu (gordo)
    'BUM': (247, 150, 165),   # Super Buu
    'BUS': (247, 150, 165),   # Kid Buu
    'BGH': (247, 150, 165),   # Buu Gohan (Buuhan)
    'BGX': (247, 150, 165),   # Buu Gotenks (Buutenks)
    'BPC': (247, 150, 165),   # Buu Piccolo (Buucolo)
    'BMG': (245, 165, 175),   # Buu Ghost (Kamikaze)
    'GXL': (247, 150, 165),   # Fat Gotenks (rosa)

    # --- Demonios / magos ---
    'DBR': (142, 8, 41),      # Dabura (rojo oscuro, validado en runtime)
    'BAB': (206, 123, 62),    # Babidi (amarillo-anaranjado)

    # --- Androides (piel clara/caucasica) ---
    '16G': (235, 195, 165),   # Android 16
    '17G': (235, 195, 165),   # Android 17
    '18G': (235, 195, 165),   # Android 18
    '20G': (230, 201, 109),   # Dr. Gero (piel en textura real)

    # --- Saiyans (piel caucasica) ---
    'GOK': (235, 195, 165),   # Goku
    'GHL': (235, 195, 165),   # Gohan adulto
    'GHM': (235, 195, 165),   # Gohan saga Cell
    'GHS': (235, 195, 165),   # Gohan nino
    'GKS': (235, 195, 165),   # Goku nino
    'VGT': (235, 195, 165),   # Vegeta
    'MVG': (235, 195, 165),   # Majin Vegeta
    'TRS': (235, 195, 165),   # Trunks
    'TRX': (235, 195, 165),   # Trunks futuro
    'GTN': (235, 195, 165),   # Goten
    'GTX': (235, 195, 165),   # Gotenks
    'GGT': (235, 195, 165),   # Gogeta
    'VTO': (235, 195, 165),   # Vegito
    'GGL': (235, 195, 165),   # Veku (Gogeta gordo)
    'BDK': (235, 195, 165),   # Bardock
    'NAP': (235, 195, 165),   # Nappa
    'RAD': (235, 195, 165),   # Raditz
    'BRL': (235, 195, 165),   # Broly
    'GNY': (235, 195, 165),   # Ginyu
    'STN': (235, 195, 165),   # Mr. Satan
    'GSM': (235, 195, 165),   # Great Saiyaman
    'KLL': (235, 195, 165),   # Krillin
    'TSH': (235, 195, 165),   # Tenshinhan
    'YMC': (235, 195, 165),   # Yamcha
    'VDL': (235, 195, 165),   # Videl
    'BLM': (235, 195, 165),   # Bulma

    # --- Kais / shinjin (piel caucasica) ---
    'KBT': (235, 195, 165),   # Kibito
    'KOK': (235, 195, 165),   # Kibito Kai
    'KOS': (235, 195, 165),   # Kaio-Shin

    # --- Uub (piel oscura) ---
    'UUB': (205, 160, 130),   # Uub

    # --- Freeza (blanco/palido) ---
    'FRZ': (238, 235, 235),   # Freeza (todas las formas)

    # --- Cell / Piccolo (verde) ---
    'CEL': (127, 177, 63),    # Cell
    'CLJ': (72, 167, 201),    # Cell Jr. (azul/negro, NO verde - es Saibaman lo verde)
    'PIC': (127, 177, 63),    # Piccolo
    'PCD': (127, 177, 63),    # Piccolo Daimao

    # --- Cooler (violeta/azul) ---
    'COO': (146, 89, 151),    # Cooler (y Metal Cooler)

    # --- Syn Shenron (gris oscuro) ---
    'SD': (140, 140, 145),    # Syn/Omega Shenron

    # --- Raditz/otros grises sin piel notable ---
    'REC': (235, 195, 165),   # Recoome
    'KAM': (235, 195, 165),   # Kami
}


def skin_color_for(code, default=SKIN_DEFAULT):
    """Devuelve el color de piel (r,g,b) para un codigo de personaje B3.

    code: prefijo del label SIN la 'X' inicial (ej. 'DBR' para XDBR_BODY).
    Busca el codigo exacto y tambien los prefijos conocidos (los labels B3
    pueden tener sufijos como 'XDBR_BODY' -> 'DBR'). Si no se encuentra,
    devuelve default.
    """
    c = code.upper().lstrip('X')
    if c in SKIN_COLORS:
        return SKIN_COLORS[c]
    # intentar el prefijo mas largo posible de la clave
    for k in SKIN_COLORS:
        if c.startswith(k):
            return SKIN_COLORS[k]
    return default


def skin_code_from_label(label):
    """Extrae el codigo de personaje de un label B3 (ej. 'XDBR_BODY' -> 'DBR')."""
    if not label:
        return ''
    lab = label.split('\x00')[0]
    # labels tipicos: XDBR_BODY, X16G_BODY, XGOK_BODY, 1SD_BODY, TSH_BODY...
    for sep in ('_', '\x00'):
        head = lab.split(sep)[0]
        if head:
            break
    else:
        head = lab
    return head.lstrip('X')
