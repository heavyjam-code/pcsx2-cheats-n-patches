# Devlog: No-Interlacing (480p) for Dragon Quest VIII (SLUS-21207)

Record of how the `[No-Interlacing]` group in
[`patches/SLUS-21207_F4715852.pnach`](../../patches/SLUS-21207_F4715852.pnach) was made.

Target: Level-5 / Square Enix (2005), NTSC-U retail, boot ELF `SLUS_212.07` (2,960,032 bytes),
ELF CRC **`F4715852`**. PCSX2 2.8.1 bundles no pnach for this serial at any CRC. Compiler string
`MW MIPS C Compiler (2.4.1.01)`, `$gp = 0x003D9770`, the same SCE libgraph build as Samurai
Western: `sceGsResetGraph` at `0x00108398`, the `SetGsCrt` stub at `0x00116420`, the libgraph
state struct at `0x00390C50` (`+0` inter, `+2` omode, `+4` ffmd).

Four words. Three are data and reach a progressive mode the game shipped with and never used; the
fourth is the one instruction that stops that mode from working. Everything else in this document
is how the fourth word was found, because the first three took an hour and the fourth took the
rest of the day.

## What the game does stock

Live over PINE at gameplay: `inter=1, omode=2, ffmd=0` - interlaced NTSC, FIELD mode - over a
`512x448` frame buffer (`DISPFB` FBP 112, FBW 8, PSMCT24), which doubles to `1024x896` at 2x. There
is **no `sceGsSetHalfOffset` anywhere in the image** - not one `64420008` - so this engine has no
per-field `XYOFFSET` mechanism at all. Six screen-resolution frames at default settings all score
best at a vertical shift of 0 with comb energy flat at 1.32. On PCSX2 the stock picture is
already clean; what this patch buys is genuine progressive output with no deinterlacer involved.

The game runs two CRTC circuits, which matters later: libgraph's `sceGsPutDispEnv` (`0x001089C8`)
programs circuit 2, and the game's own display function at `0x00145690` then writes `PMODE`
(`0x7F23`, both circuits, ALP 127), `DISPFB1` with `DBY = 1` and `DISPLAY1` itself - a one-line
shifted copy blended 50/50 with the unshifted one, a deflicker filter for interlaced output. In
480p it is a one-line vertical blend and costs nothing measurable (see the sharpness figures
below).

## The mode table

`set_video_mode` at `0x00146750` stores its index into `*(obj+0x260)` - the video config struct,
live at **`0x003E4B00`** - and dispatches through a **15-entry jump table at `0x003B5C50`**:

| Mode | Target | `s2` (omode) | Size |
|---|---|---|---|
| 2, 3, 4 | `001467B0`, `001467C8`, `001467E0` | 2 (NTSC, the default from `li s2, 2` at `00146770`) | 512x448, 640x416, 640x448 |
| 6, 7, 8 | `001467AC`, `001467C4`, `001467DC` | **0x50 (`SCE_GS_DTV480P`)** | the same three |
| 9-14 | ... | 3 (PAL) | ... |

Each NTSC entry points exactly one instruction *past* its 480p twin - past the `li s2, 0x50`. So
three data words retarget them:

```
003B5C58  001467B0 -> 001467AC
003B5C5C  001467C8 -> 001467C4
003B5C60  001467E0 -> 001467DC
```

Cold boot: PCSX2 logs `UpdateVSyncRate: Mode Changed to SDTV 480p`, libgraph reads
`inter=0, omode=0x50, ffmd=1`, and the first-boot settings screen renders. Forced to
`AspectRatio = 4:3`, the patched frame matches stock to the pixel - `2175x1630`, content at rows
241-1534 and columns 106-2037 in both. On the default `Auto 4:3/3:2` the frame comes out 2446 wide
instead of 2175, exactly the 720/640 raster ratio, because PCSX2's auto rule picks 3:2 for a
progressive mode; every `480p Mode` group in the bundle behaves the same way and the description
says so.

Then, the moment the game leaves the settings screen, the picture goes black and stays black. A
stock control run driven by the identical key sequence reaches a picture; the patched one sits at
mean 0.0 for forty seconds with the log still reading SDTV 480p.

## Three wrong answers

**Not the game's `DISPLAY1` overwrite.** The obvious suspect was the display function's own
`sd v1, 0x80(t6)` at `0x0014590C` clobbering libgraph's 480p `DISPLAY`. NOPping it changed the
internal height from 896 to 898 and left the screen black - and reading the real privileged
registers out of the savestate showed why: that NOP simply zeroed `DISPLAY1`, so it was a worse
test, not a better one.

**Not the geometry at all.** The game's own copy of its display env (`config+0x40`) decoded to a
sane 480p `DISPLAY` - `DX 436, DY 51, MAGH 1, DW 1023, DH 447` - and the CRTC block in the
savestate agreed. The rect was fine.

**Not the second `sceGsResetGraph`.** There is one at `0x00160C48` hardcoded to
`(0, inter=1, omode=2, ffmd=1)` at 640x448, which would reset the mode to NTSC if it ran
in-game. The log never showed a second mode change after SDTV 480p, so it is boot-time only.

What settled it was comparing VRAM between the working and the black savestates: everything below
`0x2C0000` byte-identical, and the two 256 KB regions at `0x340000-0x3C0000` that hold the drawn
frame **full in the working state and empty in the black one**. The game was not drawing. And
over PINE: vblanks 60.0/s, presented frames **0.0/s**. It was not rendering black; it was stopped.

## The fourth word

The black savestate's `PCSX2 Internal Structures.dat` carries the EE registers. `pc` read
**`0x00116DA0`**, inside a libgraph poll loop that reads `INTC_STAT` (`0x1000F000`) waiting for bit
2, the vblank-start flag, and `ra`/the stack gave the chain: `0x00116D40` (the poll) from
`0x00109280` inside **`sceGsSyncV` (`0x00109220`)**, from **`0x001A0DC4` in the main frame loop**.
That caller is a two-instruction loop:

```
001A0DC0  jal  sceGsSyncV          ; a0 = 0
001A0DC8  li   v1, 1
001A0DD4  beq  v0, v1, 001A0DC0    ; repeat while it returned 1
```

`do { r = sceGsSyncV(0); } while (r == 1);` - wait until the field is even before starting the
scene. And this is what `sceGsSyncV` returns, from its own tail:

```
0010928C  lh   v1, 0(s0)           ; libgraph state: inter
00109294  li   v0, 1
00109298  bne  v1, v0, 001092A8    ; inter != 1 -> straight to the epilogue with v0 still 1
001092A0  dsll32/dsra32 v0, a0     ; inter == 1: return the field bit
001092A8  ld   s0 ; jr ra
```

When the display is interlaced it returns the field, which alternates, and the loop exits on the
next even one. When the display is progressive it skips the field read and **returns the literal 1
it loaded for the comparison**, every call, forever. The game's own field-flag global at
`0x003D26B4` confirmed it from the other side: 24,910 samples, all 0, which after the vsync
handler's inversion means CSR.FIELD pinned at 1. This is the CSR.FIELD trap the candidates doc
describes, in the game's code rather than the library's.

Eleven sites call `sceGsSyncV`; nine ignore the return, one (`0x003164F0`) loops on a counter to
300, and exactly one loops on the value. So:

```
001A0DD4  1043FFFA  beq v0, v1, 001A0DC0  ->  00000000  nop
```

The frame loop syncs once and proceeds. With that word in, presented frames come back at 30.0/s
in SDTV 480p and the same key sequence that blanked now walks through the settings screen, the
title, the adventure-log menu, the attract flyover, the opening and into the first playable scene.

## Verification

All on PCSX2 2.8.1 at 2x, `[No-Interlacing]` on, `AspectRatio = 4:3`, `ScreenshotSize = 0`.

| Scene | vs stock | Frames | Best shift | Comb |
|---|---|---|---|---|
| title screen | bbox `(0,1628,0,2172)` both; mean 117.4 / 117.7; sharpness **2.74 / 2.75** | - | - | - |
| attract flyover | - | 6 | all 0 | 2.33-2.34 |
| gameplay, first playable scene, hero idle | bbox full-frame | 8 | all 0 | 2.47 flat |

The sharpness figure is the mean absolute Laplacian of the screen-resolution capture, and it is
the number the two-circuit blend would have moved if it cost anything in 480p. It did not. The
game ran a continuous 4-minute session at 30 fps in 480p before the gameplay burst, and PCSX2's
own status bar read `FPS: 30 VPS: 60` throughout.

What was not exercised: battles, the in-game menu, and the movie player. The fix removes the only
return-value loop on `sceGsSyncV` in the image, so another stall of this shape would have to come
from a different mechanism.

## Notes for next time

- **A black screen with a valid CRTC rect is a stalled game until proven otherwise.** Read the
  presented-frame rate before touching a display register; here it was 0.0/s and every register
  was correct.
- **Diff VRAM between a working and a broken savestate.** `GS.bin` is 509 bytes of state and then
  the flat 4 MB; the drawn-frame region emptying out is a one-line diagnosis.
- **The EE registers are in `PCSX2 Internal Structures.dat`.** Find `GPR[28]` by searching for the
  `$gp` value as a 64-bit slot with sixteen zero bytes 28 slots earlier; `pc` is at
  `base + 680`. That plus return addresses on the stack turns "it hangs" into a line number.
- **The GS privileged registers are there too**, at 16-byte stride: find `DISPFB1` by its FBP/FBW
  pattern and subtract `0x70` for the base.
- **Dragon Quest VIII uses Circle to confirm and Cross to cancel.** Every menu that "ignored input"
  for a day was being cancelled.
