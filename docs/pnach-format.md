# The pnach file format (PCSX2 2.x)

Everything below applies to the modern "pnach 2.0" format introduced in PCSX2 v1.7.4546 and used by all 2.x releases. Primary sources: the official [Writing patches](https://pcsx2.net/docs/advanced/writing-patches/) documentation and the conventions used across the official [PCSX2/pcsx2_patches](https://github.com/PCSX2/pcsx2_patches) repository.

## File naming

Name files **`SERIAL_CRC.pnach`**:

- `SERIAL` — the game's product code, e.g. `SLUS-20915`, `SCES-50916`
- `CRC` — the 8-hex-digit uppercase CRC of the game's ELF, e.g. `6A8F18B9`

Example: `SCES-50916_6A8F18B9.pnach` (Ratchet & Clank, PAL).

PCSX2 also accepts two variants for loose files on disk:

- A descriptive suffix between the CRC and the extension, e.g. `SCUS-97316_07652DD9.no_motion_blur.pnach`
- A legacy CRC-only name, e.g. `9A81F5F1.pnach`

Prefer the plain `SERIAL_CRC.pnach` form — it's what the official repo uses almost exclusively. One file per release: multi-region or multi-revision games get one file per serial+CRC combination, each with addresses for that build.

## Where files load from

PCSX2 has three tiers of patches:

1. **GameDB patches** — essential compatibility fixes baked into PCSX2 itself, on by default.
2. **`patches` folder** (plus the `patches.zip` bundled with PCSX2) — quality-of-life patches: widescreen, no-interlacing, 60 FPS, anti-blur. Toggled per-group on the **Patches** tab of Game Properties. A loose file on disk takes precedence over the bundled zip entry for that game.
3. **`cheats` folder** — gameplay-altering cheats. Toggled per-group on the **Cheats** tab of Game Properties, and only applied when **Enable Cheats** is on (globally under Settings → Emulation, or per-game on the Cheats tab).

Default Windows locations: `Documents\PCSX2\patches` and `Documents\PCSX2\cheats`. In portable mode the folders sit next to `pcsx2-qt.exe`. Only loose `.pnach` files are read from these folders — user-supplied zips are not.

## File structure

Plain text. `//` starts an end-of-line comment — but the files in this repo ship without a single one; see [Comments](#comments) below.

```pnach
gametitle=Game Title (NTSC-U) SLUS-12345 DEADBEEF

[60 FPS]
author=YourName
description=Unlocks the 30fps cap. May need EE Overclock.
patch=0,EE,00123456,word,00000001

[Cheats\Infinite Health]
author=YourName
description=Health never drops.
patch=1,EE,00234567,word,00000063
```

- `gametitle=` — free-form informational text at the top of the file. No fixed convention in the official repo — typically the title, usually plus region and/or serial, occasionally the CRC.
- `[Group Name]` — starts a patch group. **Each group is an individually toggleable checkbox** in the Patches/Cheats tab. A backslash nests groups in the UI tree (`[Cheats\Infinite Health]`).
- `author=` and `description=` — shown in the UI for the group they appear in.
- Files with no group labels still load (legacy pnach 1.0) as a single always-on patch, but write new files with groups.

## Comments

The format allows `//` comments. **This repo does not use them.** A finished
`.pnach` here contains only `gametitle=`, `[Group]`, `author=`, `description=`,
`gsinterlacemode=` and `patch=` — no header block, no note beside a `patch=`
line explaining what the address does.

That explanation is wanted, just not here. It goes in one of two places:

| What you want to record | Where it goes |
|---|---|
| What the patch does and what it costs — the text PCSX2 displays in the Patches tab | `description=` in that group |
| Addresses, disassembly, why each value, what was tried and ruled out | `docs/<category>/devlog-SERIAL-<slug>.md` |

`description=` is the one field that should read like prose: it is what someone
sees when choosing between two mutually exclusive groups in the UI. The devlog
carries everything else, at whatever length the work deserves.

## The `patch=` line

```
patch=place,cpu,address,type,data
```

`address` and `data` are hex **without** a `0x` prefix.

### place — when the write happens

| place | Meaning |
|---|---|
| `0` | Once, at game startup (entry point first executed) |
| `1` | Every frame, during vsync — the most common choice |
| `2` | Both: startup and every frame (v1.7.618+) |
| `3` | At startup and immediately when the patch is enabled (v2.5.385+) |

### cpu

| cpu | Meaning |
|---|---|
| `EE` | Emotion Engine — main CPU, used for nearly all patches |
| `IOP` | I/O processor — rarely needed |

### type — size and interpretation of `data`

| type | Meaning |
|---|---|
| `byte` | 8-bit write |
| `short` | 16-bit write |
| `word` | 32-bit write — the workhorse |
| `double` | 64-bit write |
| `beshort` / `beword` / `bedouble` | Big-endian variants (v1.7.4534+) |
| `bytes` | Variable-length byte array, data is a hex string (v1.7.4551+) |
| `extended` | CodeBreaker/RAW-style code: the leftmost digit of the address selects the operation (0/1/2 = 8/16/32-bit write, 3 = increment/decrement, 4 = fill, 5 = copy, 6 = pointer chain, 7 = bitwise op, D/E = conditional skips). See the [official docs](https://pcsx2.net/docs/advanced/writing-patches/) before using the exotic ones. |

## Setting-override keys

Two special keys can appear inside a group and change PCSX2 settings while that group is enabled:

- `gsaspectratio=16:9` — auto-switches the aspect ratio (used by widescreen patches)
- `gsinterlacemode=1` — forces the deinterlacing mode; `1` = Off/None, which is what No-Interlacing patches use so PCSX2 stops deinterlacing an image the patch already made progressive

These keys work in any group. Separately, **the group names `[Widescreen 16:9]` and `[No-Interlacing]` must be spelled exactly like that** for PCSX2's global "Apply Widescreen Patches" / "Apply No-Interlacing Patches" settings to auto-enable them.

## Dynamic patches

`dpatch=` lines pattern-scan recompiled code instead of writing fixed addresses (recompiler required). They're rarely needed — see the official docs for syntax.

## Standard group names

Most-used labels across the official patch repo — reuse these instead of inventing new ones:

| Label | Purpose |
|---|---|
| `[Widescreen 16:9]` | Widescreen hack (exact name required) |
| `[No-Interlacing]` | Disable interlaced rendering (exact name required) |
| `[60 FPS]` | Unlock to 60 FPS (NTSC) |
| `[50 FPS]` / `[50/60 FPS]` | PAL framerate unlocks |
| `[NTSC Mode]` | Force NTSC timings on a PAL release |
| `[480p Mode]` / `[Progressive Scan]` | Force progressive output |
| `[Remove Blackbars]` | Remove letterboxing |
| `[Remove Blur]` / `[Remove Blur/Bloom]` / `[No Motion Blur]` | Anti-blur |

## Realistic complete example

The shape of a typical single-purpose file (addresses/values here are placeholders — a real file's come from reverse-engineering that specific build):

```pnach
gametitle=Example Game (NTSC-U) SLUS-12345 DEADBEEF

[60 FPS]
author=YourName
description=Might need EE Overclock (130%).
patch=0,EE,001F4090,word,24020001

[No-Interlacing]
author=YourName
description=Disables interlaced offset rendering.
gsinterlacemode=1
patch=1,EE,2025A3C8,extended,34020001
```
