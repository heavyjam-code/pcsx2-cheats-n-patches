# Devlog: Remove Blur for Cowboy Bebop - Tsuioku no Serenade, English v1.0.0 (SLPS-25550)

How the `[Remove Blur]` group in
[`patches/SLPS-25550_53DDC158.pnach`](../../patches/SLPS-25550_53DDC158.pnach) was made.
Same disc, ELF and CRC as the
[No-Interlacing devlog](../deinterlace/devlog-SLPS-25550-cowboy-bebop-no-interlacing.md);
the ELF map there (gp `0x504670`, `file_offset = va - 0x100000 + 0x1000`, libgraph at
`0x305A40+`) is assumed here.

Symptom: with No-Interlacing on and the game confirmed to be putting out 640x480 progressive
(`GParam interlace=0 omode=0x50`, 1280x960 at 2x), the picture is still soft. Every edge —
cel outlines, the subtitle font, the HUD — smears across about two native pixels in both
directions. The deinterlace patch was doing exactly what it claims; something else was
blurring the frame after it was drawn.

## What it is not

Two candidates got ruled out before the real one was found, and both are worth recording
because the strings in the ELF point straight at them.

**Not the mipmap "depth of field".** The event-script command table at `0x4906FC` has
`SetDof` (handler `0x2D0A88`) and a stub `SetDofOff` (`0x2D0D20` is just `jr ra`). `SetDof`
stores an int at `gp-0x130` (`0x504540`) and a float at `gp-0x138` (`0x504538`), and
`0x28FFB0` packs those into TEX1: the int into `L` (bits 19-20) and a value derived from the
float into `K` (bits 32-43), with `LCM = 0`. It is a per-object LOD bias, the classic PS2 fake
DoF. Hot-writing the int from 3 to 0, and toggling PCSX2's own mipmapping off, changed
nothing measurable (mean horizontal gradient 1.399 / 1.398 / 1.395). The GS dump explains why:
every model draw carries `MXL = 0`, so there are no mip levels for the bias to select. The
system is compiled in and inert.

**Not the combat motion blur.** `SetBlur` / `SetBlurOff` (`0x2D0AF0` / `0x2D0C58`) and the
`BLUR SCALE` / `BLUR ALPHA` / `OVERLAP FRAME` debug menu at `0x4CE3E8` belong to the
fighting system's hit effects. They are scene-triggered, not always on. The heavy ghost trails
visible for a second or two on the cutscene-to-gameplay transition are a crossfade, not the
steady-state softness.

## Finding it: a GS dump instead of a disassembler

Rather than guess, dump one frame and read the draw list. PCSX2 binds single-frame GS dumps
to Shift+F8, which cannot be posted to an unfocused window (Qt reads the modifier from the
real keyboard state), so `GSDumpSingleFrame` was rebound to plain F7 in `PCSX2.ini` for the
session. The `.gs.zst` is zstd; a ~250-line GIF-packet decoder (PACKED / REGLIST / IMAGE,
A+D, per-path continuation, vertex kicks) turns it into a per-draw register log.

Per frame the list is ~2,500 draws. The last one, every frame:

```
#2582 SPRITE  TME+ABE   xy = (-0.5 .. 639.5, -1.4 .. 446.6)
  FRAME  FBP=0000 FBW=10 PSM=00          <- drawing into frame buffer A
  TEX0   TBP0=0000 TBW=10 PSM=00 TW=10 TH=9   <- ...while texturing FROM frame buffer A
  TEX1   LCM=1 MXL=0 MMAG=0 MMIN=0 K=0
  CLAMP  region 0..639 x 0..447
  ALPHA  A=Cs B=Cd C=As D=Cd  (out = (Cs - Cd) * As + Cd)
  v0  xy=(-0.5, -1.375)   st=(0, 0)         rgba = 80 80 80 30
  v1  xy=(639.5, 446.6)   st=(0.625, 0.875)
```

The next frame does the same with `TBP0=1400` onto `FBP=00A0`, the other buffer. `ST`
(0.625, 0.875) over a 1024x512 texture is 640x448; `rgba` alpha `0x30` is 48/128 = 37.5%.
So: once the frame is finished, the game draws the frame over itself, shifted half a pixel
right and 1.375 lines up, at 37.5% opacity. That is a flicker filter. On an interlaced CRT a
copy offset by roughly one line averages adjacent fields and kills the 30 Hz shimmer on thin
horizontals; on a progressive display it is a blur and nothing else. It is also drawn after
the subtitles, which is why the text is soft too.

Raw packet, as found in EE RAM (REGLIST, tag `8400000000008001` / regs `f4242810` =
PRIM, RGBAQ, CLAMP_1, ST, XYZF2, ST, XYZF2, NOP):

```
0000000000000056   PRIM   sprite | TME | ABE
3f80000030808080   RGBAQ
000006fc009fc00a   CLAMP  WMS=WMT=region, MAXU=639, MAXV=447
0000000000000000   ST
0000fff070ea6bf8   XYZF2  x=0x6bf8 y=0x70ea z=0xfff0   (XYOFFSET is 0x6c00,0x7100)
3f6000003f200000   ST     s=0.625 t=0.875
0000fff08cea93f8   XYZF2
```

## Finding the emitter: stack residue, not xrefs

None of those constants exist in the ELF. The tag template does (`0x4E14C0`, `0x4E3270`,
`0x4E32D0`, `0x4E32E0`, all `8400000000008000 / f4242810`), but every code reference to
those four is a world-space billboard drawer. The colour bytes `80 80 80 30` turn up once in
`.sdata` at `0x50353A` and that is a HUD colour table, a coincidence. The packet is re-emitted
into a moving ring-buffer slot every frame (57 stale copies in one savestate), so hot-patching
a copy proves nothing.

What worked: the packet is assembled on the stack, and a savestate's `eeMemory.bin` still
holds the residue. At `0x1FFF950` the regs qword `f4242810`, the ST pair `3f200000 3f600000`
and the ALPHA value `0x44` sit next to each other, and the saved return addresses above them
give the frame-end call chain:

```
0x100D10  main loop
  0x100F80   <- jal 0x2AE7B0   frame end / flip
    0x2AE874  <- jal 0x266938  vsync wait  -> 0x266898 -> 0x33F020
```

Searching for the ST pair in RAM rather than in the ELF found it in `.data` at `0x463BB8`,
inside a 32-byte block that is zero in the file and filled at init. That block is named by
the game: `0x2B5010` builds it with `0x2B5420(name="FRAMETEX" (0x4E21F0), w=640, h=448, ...)`
into `0x463BA0`, next to `FRAMETEX2` at `0x463BC0`. It is the "frame buffer as a texture"
descriptor, and it has exactly two users.

| User | What it does |
|---|---|
| `0x2B95A8` | copies the descriptor into a caller-supplied struct and calls the sprite drawer `0x2A15D0` — a screen-transition helper, left alone |
| **`0x1013F0`** | **the flicker filter** |

`0x1013F0(ctx, alpha, x, y)` reads the current mode entry via `0x2AEDF8`, checks two gates,
copies the descriptor to its stack, calls `0x2A15D0` to set up the sprite, writes `alpha`
into the colour byte at `sp+0x27`, scales the offsets by the mode entry's projection terms
(`+0x10`, `+0x14`) and hands the packet to `0x2A20F0` to be appended to the display list.
Its one caller is the main loop:

```
00100f20  lui   t7, 0x50
00100f28  addiu t7, t7, -0x3910     ; 0x4FC6F0
00100f30  lwc1  f12, 0(t7)          ; x = -0.5
00100f38  addiu a1, zero, 0x30      ; alpha = 48/128
00100f44  addiu t7, t7, -0x390c     ; 0x4FC6F4
00100f48  jal   0x1013f0
00100f4c  lwc1  f13, 0(t7)          ; y = -1.25
```

The stored y offset is -1.25 lines; the -1.375 seen on the wire is that value scaled by the
480/448 vertical term the No-Interlacing patch put into mode entry 1. Unpatched, the
filter lands at (-0.5, -1.25).

The two gates inside `0x1013F0`:

```
00101440  lw    t7, 0x550(t5)       ; some "screen busy" state at 0x504F98-struct+0x550
00101444  bnez  t7, skip
0010144c  lw    t7, -0x7f70(gp)     ; 0x4FC700, initialised to 1 in .sdata
00101450  beqz  t7, skip            ; <- the patch point
```

`0x4FC700` looked like the obvious data patch, and it is not one. It has ten writers, in
three gameplay functions (`0x178D98`, `0x181C48`, `0x1D7AE4` — the strings around them are
`follow_pc`, `combat`, `damage`), and the game flips it on its own: a PINE write of 0 was
back to 1 within the seconds it took to take a screenshot. It is engine state, not an option,
and there is no user-facing toggle anywhere in the menus.

## The patch

```
00101450: 11E0002A -> 1000002A      beqz t7, skip  ->  b skip
```

One word. It turns the flag test into an unconditional branch to the same `skip` label the
game uses when the flag is 0, so the function runs its prologue, the mode lookup, and its
epilogue, and appends nothing. Nothing else calls `0x1013F0`; `FRAMETEX2` and the transition
helper at `0x2B95A8` are untouched. `patch=1` is right for a per-frame branch.

Alternatives considered: NOP the `jal` at `0x100F48` (equivalent, but leaves the delay-slot
load dangling); zero the alpha at `0x100F38` (still burns a full-screen sprite's fill rate
per frame for nothing); zero `0x4FC700` in `.sdata` (overwritten by the game, see above).

## Results

All captures at 2x internal on the same savestate, gameplay in the aquarium, stock flag
value 1 written back before each capture. Gradient magnitudes are of the 8-bit luma at
internal resolution; p99.9 is the strength of the hardest edges in the frame.

| | mean frame diff vs stock | horizontal p99 / p99.9 | vertical p99 / p99.9 |
|---|---|---|---|
| Stock | — | 23 / 60 | 25 / 68 |
| Flag hot-written to 0 (PINE) | 2.20 | 26 / 80 | 32 / 90 |
| **Cold boot with the pnach** | 2.56 | 26 / 81 | 32 / 89 |

The pnach run differs from the hot-written run by 0.67 mean levels — same picture — and
from stock by 2.56. Hardest edges gain 30-35% contrast; in the cutscene close-up used for
the first A/B (Jet, `s_stock`) the max horizontal gradient went 98 → 136. Visually: the
aquarium sign text becomes legible, the bandana pattern resolves, cel outlines are one pixel
wide again, and the subtitle font is crisp. PCSX2's log confirms both groups load from the
one file (`Found 2 game patches ... Enabled patch: No-Interlacing / Remove Blur`).

## Notes for the next person

- `[Remove Blur]` is not one of PCSX2's auto-enable names. The file being found is not the
  group being on: the first cold-boot test loaded the file, enabled only `No-Interlacing`, and
  read `11E0002A` back. It needs ticking in Game Properties → Patches (or
  `gamesettings/SLPS-25550_53DDC158.ini` with `[Patches]` / `Enable = Remove Blur`).
- The filter is a good idea on an interlaced CRT and this group removes it unconditionally.
  Anyone playing with real interlaced output and no deinterlacer should leave it off.
- Screenshot-based A/B on this game's cutscenes is unreliable: shots cut every few seconds,
  and two captures 10 s apart after the same state load are different camera angles. Use a
  gameplay state with no input, and compare frame-mean difference before trusting a sharpness
  number.
