# Devlog: Remove Blur for Global Defence Force (SLES-54464)

Record of how the `[Remove Blur]` group in
[`patches/SLES-54464_DD35AC9F.pnach`](../../patches/SLES-54464_DD35AC9F.pnach) was made. The
build, the tools and the frame loop are described in
[the 60 FPS devlog](../60fps/devlog-SLES-54464-global-defence-force-60fps.md); this one only
covers the post-process.

The report was "vaseline smearing on distant objects, the player character looks fine", right
after the 60 FPS patch went in. The first thing to settle was whether the patch had caused it:
from one NTSC savestate, the far buildings measured the same sharpness at a locked 60 with the
`[60 FPS]` group and at 30 with `[NTSC Mode]` alone (Laplacian variance 33.9 against 33.7), and
a stock PAL boot showed the same haze on the same building. So it is the game's own effect. It
is not the depth-of-field PCSX2's GameDB carries three hardware fixes for, either, or rather
that entry names the same pass by another name: nothing in the frame tests depth.

## What the pass does

A single-frame GS dump (`Shift+F8` in stock PCSX2, rebound to `F7` for the session because
PostMessage cannot hold a modifier) parsed with the dump reader from earlier sessions shows the
end of every frame as an eleven-draw cascade before the HUD:

| Draw | From | To | Size | Blend |
|---|---|---|---|---|
| 1 | frame buffer (640x448) | buffer A, bw 256 | 257x257 | copy |
| 2-6 | A / B alternating | B / A | 129, 65, 33, 17, 11 | copy |
| 7-10 | B | B, shifted 1 px in each direction | 11x11 | 50/50 (`FIX` 64) |
| 11 | B, sampled as a 256x256 texture | frame buffer | 641x449 | **additive**, vertex colour `0x5A5A5A`, `FIX` 128, no depth test |

The final sprite adds 70 percent (`0x5A/0x80`) of an 11x11 blurred copy of the screen back
over the whole screen. Each texel of that copy covers about 58x41 screen pixels, so what gets
added is the local average brightness: a haze. It lifts the fog-coloured distant city toward
white and barely touches the dark soldier in the foreground, which is exactly the report.

It is emitted by one function, `0x0012F5D0`, called from the post-effect dispatcher
`0x00111B70` when the byte at `0x00279ED4` is set:

```
00111B8C  lbu  v1, -0x612c(v1)      ; 0x00279ED4, haze enabled
00111B90  bnez v1, 0x111bb8
00111BC0  lw   a2, -0x6138(v0)      ; 0x00279EC8, "intensity"
00111BC8  addiu a0, a0, -0x6134     ; 0x00279ECC, colour A (rgb)
00111BCC  jal  0x12f5d0
00111BD0  addiu a1, a1, -0x6130     ; 0x00279ED0, colour B (rgb) - the sprite colour
```

The parameters come from a small API at `0x00111C80` (`(colourA, colourB, intensity)`, called
with `intensity = 10` from engine init at `0x00111C08` and from two mission-side sites at
`0x0018FD78` and `0x001F2794`), and the intensity is not a strength at all: inside the pass it is
the size the cascade stops at. `s4` starts at 256 and halves while it is above `s2`
(`0x0012F9A8`-`0x0012FB2C`), so 10 gives the 11-pixel final copy. The enable byte is set once
per mission, not per frame.

## What was tried

All from the same mission savestate, hot-written over PINE, measured on 1280x896 captures as
mean luma over the frame, the top 45 percent (sky and far city) and the bottom 40 percent
(road and soldier), plus Laplacian variance on the far-building crop as a sharpness figure:

| Variant | mean | sky | ground | far sharpness |
|---|---|---|---|---|
| stock | 102.2 | 170.3 | 41.5 | 26.4 |
| pass skipped (`0x00111B90` nop) | 64.3 | 105.3 | 28.2 | 34.5 |
| cascade stopped at 128 (`0x00279EC8` = 128) | 104.2 | 173.4 | 42.6 | 61.8 |
| cascade stopped at 256 (clamp at `0x0012F610` raised) | 108.2 | 179.3 | 43.9 | 53.1 |
| **final sprite sampling the frame itself** | **104.8** | **173.7** | **43.7** | **86.7** |

Skipping the pass is the obvious patch and it is wrong: the picture loses a third of its
brightness, because this haze is also the game's exposure. Stopping the cascade earlier keeps
the brightness and gives back some detail, but what is added is still a blurred copy and it
still reads as a glow on the far city. The third answer is the one this repo used on Etheria's
feedback trail: keep the pass, change what it samples. The final sprite now reads the sharp
frame buffer, so the same 70 percent is added per pixel instead of per 58-pixel average. The
mean, the sky and the ground all land within 3 percent of stock, the far detail triples, and
the picture is a little more contrasty: 8.4 percent of pixels clip a channel against 7.1 in
stock.

## The words

The final sprite's packet is assembled at `0x0012FD64`-`0x0012FF0C` from the small buffer's
descriptor (`lw t1/a3, 0x270/0x274(a2)` - address and width of the last cascade buffer),
fixed 256x256 texture-size bits, a region clamp to the cascade size and UVs of
`(size + 2) << 4`. The frame buffer's own `FRAME` register value is already loaded into `t3` at
`0x0012FDD4` for the packet's `FRAME_2`, which gives the redirect everything it needs:

| Patch | Purpose |
|---|---|
| `0012FD80: 8CC70274 -> 24070280` | texture width 640 instead of the small buffer's (`srl 6` later makes it `TBW` 10) |
| `0012FDB8: 3C052000 -> 3C056800` | `TW` 8 -> 10 and the low bit of `TH` 8 -> 9, i.e. a 1024x512 texture like the cascade's own first copy; `TCC` unchanged |
| `0012FDE8: 00094A02 -> 316901FF` | `TBP0` from the frame's `FBP` (`andi t1, t3, 0x1ff`) instead of the buffer address `>> 8` |
| `0012FE30: 0009703C -> 00097140` | `sll t6, t1, 5`: pages to 256-byte blocks |
| `0012FE38: 000E703E -> 00000000` | the zero-extension shift that would have discarded it |
| `0012FE5C: 3485000A -> 34850005` | `CLAMP` mode clamp instead of region clamp, so the cascade size no longer bounds the UVs |
| `0012FEF4: A7B0016C -> A7B2016C`, `0012FEF8: A7B0016E -> A7B1016E` | `UV1` from the sprite's own corner (641, 449 in 12.4) instead of `(size + 2) << 4` |

Reusing the corner coordinates makes the UV run to 641/449 rather than 640.5/448.5; the
mapping error that leaves is under a thousandth of a texel per pixel, invisible. `place=1`, the
words are in a per-frame function, so a savestate loaded into a patched session comes up sharp
on its next frame. The cascade itself still runs every frame into its private buffers; it is
eleven small draws and it was left alone rather than add words.

Verified from a fresh boot with `[60 FPS]` and `[Remove Blur]` both enabled: all eight words
read back, 60 presents a second, and the mission frame measured 104.3 / 173.5 / 42.9 with the
far crop at 51.0 against the stock 25-33 of comparable crops.

## What it does not do

Nothing else changes: the colour-overlay pass at `0x0012F370` (gated by `0x00279EC4`, used for
fades and flashes) is untouched, and so are the game's fog and its distant-model detail, which
is why the far city is still grey and soft-edged, just no longer smeared. Missions that set a
different haze colour or size through `0x00111C80` get the same treatment, since the redirect
does not depend on either.
