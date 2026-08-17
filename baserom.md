# Required game files

Provide these files locally from your **legally obtained** copy of *Dragon Ball
Z: Budokai HD Collection* (Xbox 360). **None of them are distributed by this
project.** This document lets you verify that you have the exact files the
recompile expects, the same way other static-recompilation projects do
(e.g. `baserom.md` in mstan's recomp projects).

## Game executable (`.xex`)

The Xbox 360 game executable. The USA and EU (PAL) `.xex` are **byte-identical**
(one binary; region is decided by the data), so either copy works.

- Expected path: `assets/default.xex`
- Size: **4,464,640 bytes** (4.26 MB)
- MD5: `5A6AB28A4911851FCA955B5925CDFEBB`
- SHA-256: `52BCE2009C62DF9A5419CA449E57D174B452B77B2E0BB1CA487D462E184C8DA1`

> A second copy named `assets/xex_eur/default_eur.xex` is kept for parity in
> the reference tree; it is the same binary.

## Game data archives (`.afs`)

These are the region/audio data archives. You only need the ones for the
region you play. They all share the same internal bin numbering.

### USA region (`assets/us/`)

| File | Size (bytes) | SHA-256 |
|---|---|---|
| `data_us.afs` | 296,587,264 | `8C9D84312884B15130BE980F5C7DF3BA44076A0BEE95020DC9E62143203AD976` |
| `data_sp.afs` | 296,654,848 | `5E156EFAB2485BBA669BFF587FB093C3AD41DE87D900E524E941972B08C1B636` |
| `data_fr.afs` | 296,314,880 | `CD9E2A5BE44A773AF58501E622E0CDBB4D3F48B5C4E14751D3A2F346DB01091C` |
| `adx_us.afs` | 567,705,600 | `6AF1F9D248FFC8C7D83A8D94F372408B2F681344DDC319F1166DF35C9CD0BA48` |
| `data_yah.afs` | 964,608 | `27610E6B3DD0A91D3DBB32542820BC1CAB9E2B639D6D75F8D46460CE78B5011D` |

### EU (PAL) region (`assets/eu/`)

| File | Size (bytes) | SHA-256 |
|---|---|---|
| `data_en.afs` | 286,384,128 | `C8B5C71699D529E8781792C3B0874594ED25922120FF6975756D34473726256F` |
| `data_fr.afs` | 296,151,040 | `E060487BBB19F7AA913D15EF653033492D6B4EFB9C2C0C85472595F9B3BDCBD8` |
| `data_ge.afs` | 286,806,016 | `FBA8FC84607B1899BA82C92F1274136B153A513E7954B7AAAB32FBDEBB4B60AF` |
| `data_it.afs` | 286,941,184 | `D770A931C239025EDBDCCF8BDAEC2E78889AD69B9C93BA4AA9C5B686AF4905B0` |
| `data_sp.afs` | 296,491,008 | `3B36FA28FB17BD2E72B0D6933549A8E150538622A5C7C86A1D8281A6285108EC` |
| `adx_jp.afs` | 565,891,072 | `070AD39F9A12F1CF2E468A2C6DA648A65D20ACBB31355C7143AD7626C805676F` |
| `data_yah.afs` | 964,608 | `72B9D35433F773CDD0BDEAA9EEB23264202BEB8450D538C8494C2AD89699B88A` |

> The `.xex` and the `.afs` archives are **copyrighted** and are **not
> distributed** by this project. You must extract them yourself from the
> original Xbox 360 disc (ISO) or digital copy you own.

## How to extract the files from the ISO

The Xbox 360 disc image (`.iso` / `.xiso`) contains the game data in an Xbox
FATX filesystem. Tools to read it (all third-party, not affiliated with this
project):

1. **`extract-xiso`** — reads Xbox/Xbox 360 ISO images on Windows/Linux/macOS.
2. **Xbox 360 HDD/DVD extraction tools** from the modding community.

Once the FATX volume is mounted/extracted, the files you need live under the
game's `Partition1\` layout:
- The `.xex` (executable) at the game root.
- The `us/` and `eu/` folders containing the `data_*.afs` and `adx_*.afs`
  archives.

Copy those into the `assets/` layout described above. You do **not** need the
whole ISO — only the executable and the data archives.

## Why this matters

This project follows the standard "copyright-friendly" convention of the
static-recompilation community (see `mstan/DragonBallZBuusFuryRecomp`): the
recompile logic ships as source and as a runnable launcher, but **no game
content is distributed**. You bring your own legally obtained files, verify
them against this document, and play.
