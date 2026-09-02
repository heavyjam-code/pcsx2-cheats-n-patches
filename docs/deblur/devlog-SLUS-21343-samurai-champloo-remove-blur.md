# Devlog: Remove Blur for Samurai Champloo: Sidetracked (SLUS-21343)

Record of the `[Remove Blur]` group in
[`patches/SLUS-21343_7A5B4F80.pnach`](../../patches/SLUS-21343_7A5B4F80.pnach). Companion to
[the No-Interlacing devlog](../deinterlace/devlog-SLUS-21343-samurai-champloo-no-interlacing.md),
which covers the same build and the same session.

One line, and it is a data write rather than a code word — see [Why a data
patch](#why-a-data-patch) for why the code route was tried first and abandoned.

## What the effect is

A GS dump of a gameplay frame lays it out with no disassembly at all. After the 3D is drawn
and before the HUD goes on, the game runs a five-draw post-process:

```
GS local->local transfer  SBP=0000 SBW=8 PSM=00  ->  DBP=1500 DBW=8 PSM=00   512x224
SPRITE n=4  TEX0 TBP0=1500 TBW=8 PSM=00 TW=9 TH=8 TCC=0 TFX=0   TEX1 LINEAR
            ALPHA A=0 B=1 C=0 D=1        -> (Cs - Cd)*As + Cd, straight alpha over
            xy (0,0)..(512,224) on all four taps
   tap 1  RGBA (128,128,128, 64)   ST offset  t = -1/2560   (-0.1 texel)
   tap 2  RGBA (128,128,128, 56)   ST offset  t = +1/2560   (+0.1 texel)
   tap 3  RGBA (128,128,128, 48)   ST offset  s = -1/2560   (-0.2 texel)
   tap 4  RGBA (128,128,128, 40)   ST offset  s = +1/2560   (+0.2 texel)
```

The whole frame is copied out and then blended straight back over itself four times, at
64/56/48/40 of 128 — 50%, 44%, 37%, 31%. Composited in order, that leaves

```
0.121 original + 0.121 tap1 + 0.188 tap2 + 0.258 tap3 + 0.313 tap4
```

so **about an eighth of the original pixel survives** into the finished image and the rest
comes from the four offset copies. The offsets are only a fifth of a texel, but `TEX1` has
bilinear on, so each tap is itself a blend of neighbouring texels, and the taps carry
five-sixths of the weight. Every edge in the scene is pulled into its neighbours. On a
512x224 buffer, where one texel is a large fraction of what you can see, that is the softness.

The HUD, the minimap and all text are drawn *after* the pass and are untouched by it either
way — which is why the overlay stays crisp while the 3D behind it does not.

## The switch

The pass belongs to an effect object at `0x49e3d0`, built and queued by `0x220430`
(one caller, `0x30cc10`), which walks two packet copies 0x330 apart, one per frame buffer, and
fills them through `0x21e2d0` → `0x21ef40`. That builder writes the packet at
`object + 0x60` onward, and the register offsets line up exactly with the dump: DTHE at
`+0x10`, TEX0 at `+0x20`, TEST at `+0x30`, ZBUF `+0x40`, ALPHA `+0x50`, TEX1 `+0x60`, TEXA
`+0x70`, CLAMP `+0x80`, XYOFFSET `+0x90`.

The object carries three fields the game itself pokes:

| Address | Meaning |
|---|---|
| `0x49ea40` | `255` — written once by `0x220430` |
| **`0x49ea44`** | **flags; bit 0 is the pass's active bit** |
| `0x49ea48` | `1.0f` strength; `0x1d1470` zeroes it, `0x1d0b14` restores it |

Every writer of `0x49ea44` in the image does `flags & ~1` then `| 0` or `| 1`, so the word
only ever holds 0 or 1 and bit 0 is the whole story:

```
0x1cbde0   or with andi a0,zero,1  -> 0   (disable)
0x1cd624   or with daddiu a0,zero,1 -> 1  (enable)
0x1cdbc0   or with andi a3,zero,1  -> 0   (disable)
0x1d0bc8   setter, bit from its a1 argument; called from 0x31e4ac and 0x31ee40
```

`patch=1,EE,0049ea44,word,00000000` holds that bit clear.

## Verification

The measurement that settles it is the draw list, not a sharpness metric. Two GS dumps of the
same gameplay scene, four frames each:

| | flag = 1 | flag = 0 |
|---|---|---|
| full-screen taps from `TBP0=0x1500` | **16** (4 per frame) | **0** |
| framebuffer→`0x1500` transfers | present | gone |
| draws in frame 1 | 100 | 93 |

Seven draws per frame disappear — the copy, the four taps and their state — and nothing else
in the profile changes. Repeated from a cold boot with the pnach installed and the savestate
reloaded: 16 taps → 0.

Reported visually as a notable difference by the person looking at the screen, which is the
end the patch is for.

## Why a data patch

The tidier patch would be a code word, and two were tried and rejected:

- **`0x2204a4`, the queue push at the end of `0x220430`.** Reading it as "this is what links
  the pass into the per-frame render list" was wrong. The word was confirmed patched to
  `00000000` live and the pass still drew in all four frames of a dump.
- **The two enable paths, `0x1cd610` and `0x1d0bac`.** Both patched and confirmed applied on
  a cold boot; the flag still read `1`. Whatever sets it in a loaded level is not either of
  them, and an absolute-address scan cannot see the store that does — the same blind spot
  that hid the half-offset writer in the No-Interlacing job, where the store went through a
  pointer already in a register.

The flag itself is the one lever proven to work, so the patch writes it. The honest cost of
that choice: a `patch=1` line lands at vsync, so if the game sets the bit during a frame the
pass can survive for that single frame. The bit changes at scene boundaries, not per frame,
so this is at most one frame at a transition — and nothing has been seen.

## Harness notes

- **`F8` produces no new screenshot while emulation is paused.** Pausing on a fixed frame is
  the right idea for a frame-matched A/B, but the capture never lands and a glob for the
  newest PNG silently returns the *previous* run's file. Two "different" runs then compare
  byte-identical, MSE exactly 0.0 — which is what an alert reader should treat as a bug in
  the harness rather than a result.
- **A whole-frame mean-gradient is the wrong instrument for a soft-focus pass.** Most of a
  frame is flat or dark, so a real, visible softening moved the global number by well under a
  percent, and comparing two captures of an *animated* scene put noise of the same size on
  top. It read as "not worth patching", which was wrong. Count the draws instead, and believe
  the person looking at the screen.
- A custom group name is not auto-enabled. `[Remove Blur]` needs ticking in Game Properties →
  Patches, or a `gamesettings/SLUS-21343_7A5B4F80.ini` holding `[Patches]` and
  `Enable = Remove Blur`. A run that "did nothing" showed the target words still at their
  original values for exactly this reason.
