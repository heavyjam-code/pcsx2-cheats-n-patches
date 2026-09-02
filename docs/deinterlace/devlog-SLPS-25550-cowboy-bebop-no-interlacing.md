# Devlog: No-Interlacing for Cowboy Bebop - Tsuioku no Serenade, English v1.0.0 (SLPS-25550)

Record of how [`patches/SLPS-25550_53DDC158.pnach`](../../patches/SLPS-25550_53DDC158.pnach)
was made. The game was on the greenfield list in
[the candidates notes](no-interlacing-candidates.md#ntsc-j-fan-translations) — no pnach on
any serial or CRC, nothing to copy from. It turned out to be the cheapest class of job on
the platform and the best outcome available: the game already contains a complete,
developer-written **DTV480P** mode that it never selects. The patch is six words of table
data and no code at all.

Target: Bandai / Sunrise Interactive (2005), NTSC-J, **First Limited Edition** disc plus the
English fan translation v1.0.0. Boot ELF `SLPS_255.50` (4,587,520 bytes), ELF CRC
**`53DDC158`**. Tested on PCSX2 2.8.1.

## Serial correction

The candidates notes list this game as `SLPS-25551`. That is the standard edition. The
translated disc here reports **`SLPS-25550`** — *Tsuioku no Serenade [First Limited
Edition]* in `GameIndex.yaml` — and PCSX2's `patches.zip` has **nothing** for it. The only
bundled file for either serial is `SLPS-25551_C162A768.pnach`, a widescreen hack for the
untranslated standard edition, so it would not load here under any circumstances. Both the
edition and the translation change the CRC; check the serial off the disc, not off a wiki.

## Tier measurement

Unpatched, 2x internal, deinterlacing None:

```
attract intro   1280x896   -> 640x448, vertical doubles
3D cutscene     1280x896   -> same
```

`sceGsGParam` at `0x496E80` reads `interlace=1, outmode=2 (NTSC), ffmd=0, GS rev 0x1b`.
FIELD mode over a full-height buffer, same shape as
[Ys VI](devlog-SLUS-20980-ys-vi-no-interlacing.md): **TIER-B on paper**, a two-word
SMODE2 + DY job.

Two things argued for looking further before writing that patch:

- the image contains **two byte-identical copies of `sceGsSetHalfOffset`** (the `+8`
  half-pixel add at `0x306FBC` and `0x307044`) with **four call sites in game code**, which
  a pure full-frame renderer has no use for; and
- `0x1007F4`'s equivalent in this build — the `omode == 0x50` arm of
  `sceGsSetDefDispEnv` — is fully compiled in.

Both pointed at a video-mode system with more than one setting. There is.

## How the game does video (map of the ELF)

EE virtual addresses; the first loadable segment maps `file_offset = va - 0x100000 + 0x1000`.
`gp = 0x504670`, read out of the `.reginfo` section (offset 20 of the 24-byte struct) rather
than guessed.

Sony's libgraph is linked high in this image but is byte-for-byte the same library as in
Ys VI, relocated by `+0x206F48`; every offset in the Ys VI map transfers directly.

| Address | What it is |
|---|---|
| `0x305A40` | `sceGsResetGraph(mode, interlace, omode, ffmd)` |
| `0x305BD0` | GParam getter → `0x496E80` |
| `0x307478` | `sceGsSetDefDispEnv` (= Ys VI `0x100530` + `0x206F48`) |
| `0x307538` / `0x307544` / `0x307548` | SMODE2 constants 2 / 3 / 1 |
| `0x3075B4` / `0x307624` | NTSC `DISPLAY.DY` bases, interlaced `0x32` and progressive `0x19` |
| `0x3075EC` | NTSC FRAME `DH = 2h-1`; `0x3076A0` is the byte-identical PAL twin |
| `0x306028` | the field helper: returns live CSR.FIELD **only** while `GParam.interlace == 1` |
| `0x306F50`, `0x306FD8` | the two copies of `sceGsSetHalfOffset`; `+8` adds at `0x306FBC` / `0x307044` |
| **`0x461E98`** | **the video-mode table** — 10 entries of 0x54 bytes |
| `0x47E808` | the developers' name strings for those 10 entries, still in the retail image |
| `0x2AEDF8` | `mode_entry(i) = 0x461E98 + i*0x54` |
| `0x504EC4` | the live mode index (`= gp+0x854`), set to **1** at `0x100B54` during early init |
| `gp+0x860`, `gp+0x85c` | requested mode + dirty flag, consumed by the apply routine at `0x2ADB68` |
| `0x2ADA48` | `setVideoMode(i)`, reached only from the debug cycler below |
| `0x2ADA60` | a **developer** mode cycler, gated on `gp+0x864` and a pad combo read at `0x504628`/`0x50462C` |
| `gp+0x84c` | per-frame half-offset gate, loaded from mode entry `+0x44` |
| `0x2AE8EC` | the per-frame block that applies `sceGsSetHalfOffset` to the four draw envs, skipped entirely when that gate is 0 |

There are no display-register writes from game code: every `lui r,0x1200` outside libgraph
(`0x2668C8`, `0x2869D0`, `0x286A84`, `0x2B4328`, `0x2B4340`) resolves to CSR `0x12001000` or
`0x12001080`, never to SMODE2 or DISPLAY. Unlike Ys VI, libgraph is authoritative here.

## The mode table

`0x461E98`, ten entries. The fields that matter: `+0x0C` buffer height, `+0x14`/`+0x1C`/`+0x24`
projection scale terms, `+0x44` half-offset flag, and `+0x48`/`+0x4C`/`+0x50` fed straight
into `sceGsResetGraph` as `interlace`, `omode`, `ffmd` at `0x2ADBD0`.

| # | buffer | +0x44 half-offset | interlace | omode | ffmd | what it is |
|---|---|---|---|---|---|---|
| 0 | 640x224 | **1** | 1 | 2 | 1 | NTSC field-rendered |
| **1** | 640x448 | 0 | 1 | 2 | 0 | **NTSC full-frame — the shipped mode** |
| 2 | 640x256 | 1 | 1 | 3 | 1 | PAL field-rendered |
| 3 | 640x512 | 0 | 1 | 3 | 0 | PAL full-frame |
| **4** | **640x480** | 0 | **0** | **0x50** | 0 | **DTV480P — complete, never selected** |
| 5 | 640x480 | 0 | 0 | 0x1a | 0 | a VESA mode |
| 6-9 | 448/512 variants | 0 | 1 | 2 or 3 | 0 | alternate widths and pixel formats |

No guesswork was needed on that last column: the developers' own names for the ten entries
are still in the retail image, as a pointer table at `0x47E808`, next to the format string
`frame_mode=[%s]`.

```
[ 0] 640x224 NTSC              [ 5] 640x480 VESA
[ 1] 640x448 NTSC              [ 6] 640x448 NTSC(PSMCT16S)
[ 2] 640x256 PAL               [ 7] 640x512 PAL (PSMCT16S)
[ 3] 640x512 PAL               [ 8] 512x448 NTSC
[ 4] 640x480 DTV480            [ 9] 512x512 PAL
```

So the two half-offset copies exist for mode 0, which this disc never uses, and mode 4 is a
finished 480p path with its own projection constants. The only thing standing between the
game and progressive output is that early init hardwires the index to 1 and nothing in a
retail run ever moves it — see the writer audit below, which is where that claim is earned.

## Forcing it: the live test first

Before writing anything, two PINE writes — `gp+0x860 = 4`, `gp+0x85c = 1` — to let the
game's own apply routine do the work:

```
mode index        1  ->  4
GParam            interlace=1 omode=2  ffmd=0   ->   interlace=0 omode=0x50 ffmd=0
output (2x)       1280x896             ->            1280x960
```

640x480 progressive, in gameplay, first try, with the HUD, minimap, subtitles and the
translation's text all intact. That is the whole answer; everything after this is about
making it happen from boot without touching engine code.

## Why `interlace = 0` does not deadlock this game

This is the failure that killed [Ys V attempt 1](devlog-SLPM-66360-ys-v-no-interlacing.md)
and it is the first thing to check whenever GParam changes. Here it is provably safe rather
than empirically lucky.

`0x306028` is the field helper. Its interlaced path reads CSR bit 13; the other path returns
early — but look at where `v0` is set:

```
00306054  lh    v1, 0(s0)      ; GParam.interlace
00306058  addiu v0, zero, 1    ; v0 = 1, BEFORE the branch
0030605c  bne   v1, v0, 0x3060b0   ; interlace != 1 -> return, v0 still 1
```

It returns a hard **1**, not 0 and not garbage. All five callers:

| Caller | Shape | With `interlace = 0` |
|---|---|---|
| `0x266978` | tail-call wrapper | no loop |
| `0x26BFD8` | `field = v0 ^ 1` into `sceGsSetHalfOffset` | field = 0, no offset |
| `0x26C054` | same | field = 0, no offset |
| `0x2ABEBC` | plain call | — |
| `0x2AD3E0` | `do { v = syncV(0) } while (v == 0)` | v = 1, **exits on the first iteration** |

There is no `while (v == 1)` anywhere in the image, which is the polarity that would hang.
And the two half-offset argument sites fall to zero on their own, so the field bob cannot
reappear. Confirmed by cold boot: the game reaches the attract intro, cutscenes and gameplay
with `interlace = 0` and no black screen.

## The patch: six words of table, no code

Forcing the index would mean either patching a function whose only caller is a pointer
(`0x2AEDE0`) or rewriting the table lookup so *every* mode resolves to 4 — which would also
redirect the 512-wide modes and change buffer widths nobody asked for. Rewriting mode 1's
entry in place is more surgical, and mode 1 differs from mode 4 in exactly six words:

| Address | Mode 1 | Mode 4 | Field |
|---|---|---|---|
| `0x461EF8` | `000001C0` | `000001E0` | buffer height 448 → 480 |
| `0x461F00` | `3F800000` | `3F891687` | vertical scale, 1.0 → 1.071 (a rounded 480/448 = 1.0714) |
| `0x461F08` | `BF70A3D7` | `BF800000` | its negative partner, -0.94 → -1.0 |
| `0x461F10` | `43600000` | `43700000` | projection half-height 224.0 → 240.0 |
| `0x461F34` | `00000001` | `00000000` | `sceGsResetGraph` interlace |
| `0x461F38` | `00000002` | `00000050` | `sceGsResetGraph` omode → `SCE_GS_DTV480P` |

Everything else in the two entries is already identical. No engine instruction is modified,
and modes 0 and 2-9 keep their real values in case anything ever asks for one.

**Scanning for the index by `gp` displacement alone is not enough here, and it did hide a
writer for a while.** Half the code reaches the index as `gp+0x854` and half as an absolute
`lui 0x50` / `0x4EC4(t7)`. The `gp`-relative scan finds 21 accesses and 2 writers; adding a
base-resolved scan brings it to **41 accesses and 4 writers**, and the two it had missed
include the only one that actually runs.

| Writer | Reachable in a retail run? |
|---|---|
| `0x100B54` | **Yes** — early init, stores 1. The shipped mode comes from here, and the `gp` scan misses it |
| `0x2ADBA4` | Only if the dirty flag `gp+0x85c` is set, which only the debug cycler does |
| `0x2AEDE0` | No — zero callers and its address appears nowhere as data. Dead code |
| `0x2C0A48` | **Runs, finds nothing.** It is the `frame_mode=[%s]` handler in a key/handler table at `0x47E7C4`, driven by a loader that opens a disc file literally named **`config.txt`** (string at `0x4E2E20`, log prefix `LoadConfig---` at `0x4E2E30`) at `0x100BE0` — after the index store and before graphics init. There is no `config.txt` anywhere on this disc: the ISO9660 tree is `SYSTEM.CNF`, `DI.`, the ELF, and `MODULES/` + `DATA/`, nothing else. So the parser bails and the index stays 1 |

**And of the 37 readers, not one compares the index to a constant.** Every single one loads
it straight into `a0` and calls a table accessor, `0x2AEDF8` or `0x2B4200`. Nothing in the
image decides interlaced-versus-progressive behaviour from the index itself, so leaving it at
1 while the entry it points at describes 480p is consistent.

*This is the [displacement-only match](devlog-SLUS-20487-mega-man-x7-no-interlacing.md)
lesson in its other form. Last time a bare displacement produced a false positive; here it
produced a false negative — a "this variable has one writer" conclusion that was wrong.
Resolve the base, then count.*

## Results

Frame-locked A/B: two cold boots driven by an identical scripted key sequence, five captures
each. Per-frame mean brightness matches to within 0.3 across the pair, so the two runs are
on the same emulated frames.

| | Unpatched | Patched |
|---|---|---|
| GParam | `interlace=1 omode=2 ffmd=0` | `interlace=0 omode=0x50 ffmd=0` |
| Output at 2x | 1280x**896** (640x448 interlaced) | 1280x**960** (640x480 progressive) |
| Mode index | 1 | 1 (entry rewritten) |
| Same scene, rescaled to a common height | — | MSE **13.35**, best vertical shift **0** |

That last row is the one that matters: after scaling the 448-line capture up to 480, the two
frames land on top of each other. The camera, the field of view and the letterbox framing are
unchanged — this is the same picture with 32 more real scanlines, not a zoom or a crop.

Stability: cold boot through the attract sequence, the comic-panel intro, a full 3D cutscene
and free-roaming gameplay with combat, roughly two and a half minutes of scripted input, with
the mode index and GParam polled once a second. No hang, no mode change, no glitch —
`mode=1 interlace=0 omode=80 ffmd=0` for the entire session, output 1280x960 throughout.

## Rejected: the conservative patch

An independent blind static pass over this ELF proposed the expected TIER-B answer —
`0x307548: 24020001 → 24020002` and `0x3075B4: 24420032 → 24420019`, the Ys VI recipe
transplanted. It is correct and it would work. It is also strictly worse: it leaves the game
rendering 448 lines and leaves GParam claiming the console is interlaced, so the engine keeps
sampling CSR.FIELD and libgraph keeps taking the interlaced arm everywhere. Given a finished
480p mode sitting in the ELF, hand-forging a progressive signal out of the interlaced one is
the wrong trade.

## Deliberately left alone

- **Modes 0 and 2-9.** Unused on this disc. Mode 0 is the only one with the half-offset flag
  set, and if anything ever selected it the two `sceGsSetHalfOffset` copies would come back —
  but early init sets index 1 and nothing reachable in a retail build ever changes it.
- **The debug mode cycler** at `0x2ADA60`. Enabling it (`gp+0x864`) would expose all ten modes
  through a pad combo, which is a different feature and an untested one.
- **The memory-card format screen** at `0x26BE08`, and this one is a real limitation rather
  than a technicality. It is the only place in the image that goes round the mode table:
  `0x26BE5C` calls `sceGsResetGraph(0, 1, 2, 1)` with the arguments hardcoded — interlaced
  **FRAME** — and then builds its own 320x224 double buffer at `0x305D30`. Nothing the patch
  touches reaches it, so that screen stays interlaced. Dragging it along would mean
  hand-forging progressive output for a 224-line buffer (SMODE2 3→2 *and* the `0x3075EC` DH
  doubling *and* both `64420008` half-offset adds), which is precisely the work this patch
  exists to avoid, on a screen you only see when a memory card needs formatting. Checked all
  seven `sceGsResetGraph` call sites to be sure it is the only one: three take their
  arguments from the mode table (`0x2ABE8C`, `0x2ADBD0`, `0x2AD6D8`), `0x26BE40` and
  `0x2AD81C` pass `mode = 1` which is GS-reset-only and leaves GParam alone, `0x2B9A60`
  passes all zeros on a teardown path, and `0x26BE5C` is this one.
- **PAL paths.** Unreachable; this is an NTSC-J disc and `omode` never comes from anywhere but
  the table.
- **The bundled `SLPS-25551` widescreen hack.** Different edition, different CRC, and its
  matrix addresses (`0x30D4AC`) were not verified against this build. Out of scope for a
  no-interlacing patch.

## Final patch summary

| Patch | Purpose |
|---|---|
| `00461EF8: 000001C0 → 000001E0` | mode 1 buffer height 448 → 480 |
| `00461F00: 3F800000 → 3F891687` | vertical scale for 480 lines |
| `00461F08: BF70A3D7 → BF800000` | matching negative scale term |
| `00461F10: 43600000 → 43700000` | projection half-height 224.0 → 240.0 |
| `00461F34: 00000001 → 00000000` | `sceGsResetGraph` interlace = 0 |
| `00461F38: 00000002 → 00000050` | `sceGsResetGraph` omode = `SCE_GS_DTV480P` |

Plus `gsinterlacemode=1`, which at this point is belt and braces — there is no interlaced
signal left to deinterlace.

## Follow-up: the picture is still soft

Progressive output did not make the game sharp, and that is not this patch's fault. The
engine blends a 37% copy of every finished frame back over itself, offset by half a pixel
and 1.25 lines — a CRT flicker filter that has nothing left to do once the signal is 480p.
It is a separate group, `[Remove Blur]`, in the same file; see the
[Remove Blur devlog](../deblur/devlog-SLPS-25550-cowboy-bebop-remove-blur.md).
