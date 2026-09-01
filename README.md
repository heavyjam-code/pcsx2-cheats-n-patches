# pcsx2-cheats-n-patches

Hand-made patches and cheats for PS2 games, in the `.pnach` format used by the [PCSX2](https://pcsx2.net/) emulator. The patches here focus on quality-of-life improvements such as:

- **No-Interlacing / deinterlacing** — stable, shake-free image instead of the PS2's interlaced output
- **60 FPS** — unlock games capped at 30 FPS
- **Anti-blur** — remove blur/ghosting filters some games apply

## Repository layout

| Folder | Contents | Goes into PCSX2's... |
|---|---|---|
| [`patches/`](patches/) | Quality-of-life patches (60 FPS, No-Interlacing, Remove Blur, ...) | `patches` folder |
| [`cheats/`](cheats/) | Gameplay-altering cheats (infinite health, unlocks, ...) | `cheats` folder |
| [`docs/pnach-format.md`](docs/pnach-format.md) | Reference for the pnach 2.0 file format | — |
| [`docs/no-interlacing-candidates.md`](docs/no-interlacing-candidates.md) | Which games still need a No-Interlacing patch, and how to grade one | — |
| [`tools/`](tools/) | Scripts for surveying PCSX2's patch coverage | — |
| [`templates/template.pnach`](templates/template.pnach) | Starting point for making a new patch file | — |

Files are stored flat (no per-game subfolders), one file per game release, exactly like the official [PCSX2/pcsx2_patches](https://github.com/PCSX2/pcsx2_patches) repo — so you can copy them straight into your PCSX2 folders.

## Installing a patch

1. Find the `.pnach` file for your exact game release (see [Matching your disc](#matching-your-disc) below).
2. Copy it into the right PCSX2 folder:
   - **Default Windows install:** `Documents\PCSX2\patches` (or `Documents\PCSX2\cheats` for files from `cheats/`)
   - **Portable install:** the `patches` / `cheats` folder next to `pcsx2-qt.exe`
3. In PCSX2, right-click the game → **Properties** → **Patches** tab and tick the patches you want. Files from the `cheats` folder appear on the **Cheats** tab instead and additionally require **Enable Cheats** (per-game on that tab, or globally under Settings → Emulation).
4. Restart the game if it was running.

## Matching your disc

Every file is named `SERIAL_CRC.pnach` (for example `SCES-50916_6A8F18B9.pnach`) and targets **one specific release** of a game. To find your game's serial and CRC, right-click it in the PCSX2 game list and open **Properties** — both are shown on the Summary page. If the serial or CRC doesn't match, the patch will not load, and even a renamed copy is unlikely to work because memory addresses usually differ between regions and revisions.

## Making your own patches

Start from [`templates/template.pnach`](templates/template.pnach) and read [`docs/pnach-format.md`](docs/pnach-format.md) for the full file-format reference, including the standard group names the PCSX2 community uses (`[60 FPS]`, `[No-Interlacing]`, `[Remove Blur]`, ...).
