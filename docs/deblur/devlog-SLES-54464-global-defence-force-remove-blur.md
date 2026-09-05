# Devlog: Remove Blur for Global Defence Force (SLES-54464)

Record of how the `[Remove Blur]` group in
[`patches/SLES-54464_DD35AC9F.pnach`](../../patches/SLES-54464_DD35AC9F.pnach) was made. The
build, the tools and the frame loop are described in
[the 60 FPS devlog](../60fps/devlog-SLES-54464-global-defence-force-60fps.md); the progressive
output in [the No-Interlacing devlog](../deinterlace/devlog-SLES-54464-global-defence-force-no-interlacing.md).
This one covers the two post-processes that soften the picture, and it took three attempts
to find both.

The report was "vaseline smearing on distant objects, the player character looks fine", right
after the 60 FPS patch went in. The first thing to settle was whether the patch had caused it:
from one NTSC savestate, the far buildings measured the same sharpness at a locked 60 with the
`[60 FPS]` group and at 30 with `[NTSC Mode]` alone (Laplacian variance 33.9 against 33.7), and
a stock PAL boot showed the same haze on the same building. So it is the game. It turned out to
be two separate effects layered on top of each other, and the second only became visible once
the first was gone.

## The haze

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
white and barely touches the dark soldier in the foreground.

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
(`0x0012F9A8`-`0x0012FB2C`), so 10 gives the 11-pixel final copy.

What was tried, all from the same mission savestate, hot-written over PINE, measured on
1280x896 captures as mean luma over the frame, the top 45 percent and the bottom 40 percent,
plus Laplacian variance on the far-building crop:

| Variant | mean | sky | ground | far sharpness |
|---|---|---|---|---|
| stock | 102.2 | 170.3 | 41.5 | 26.4 |
| pass skipped (`0x00111B90` nop) | 64.3 | 105.3 | 28.2 | 34.5 |
| cascade stopped at 128 (`0x00279EC8` = 128) | 104.2 | 173.4 | 42.6 | 61.8 |
| cascade stopped at 256 (clamp at `0x0012F610` raised) | 108.2 | 179.3 | 43.9 | 53.1 |
| **final sprite sampling the frame itself** | **104.8** | **173.7** | **43.7** | **86.7** |

Skipping the pass is the obvious patch and it is wrong: the picture loses a third of its
brightness, because this haze is also the game's exposure. The answer is the one this repo used
on Etheria's feedback trail: keep the pass, change what it samples. The final sprite now reads
the sharp frame buffer, so the same 70 percent is added per pixel instead of per 58-pixel
average. Its packet is assembled at `0x0012FD64`-`0x0012FF0C` from the small buffer's
descriptor, fixed 256x256 texture-size bits, a region clamp to the cascade size and UVs of
`(size + 2) << 4`; the frame buffer's own `FRAME` value is already loaded into `t3` at
`0x0012FDD4` for the packet's `FRAME_2`, which gives the redirect everything it needs:

| Patch | Purpose |
|---|---|
| `0012FD80: 8CC70274 -> 24070280` | texture width 640 instead of the small buffer's (`srl 6` later makes it `TBW` 10) |
| `0012FDB8: 3C052000 -> 3C056800` | `TW` 8 -> 10 and the low bit of `TH` 8 -> 9: a 1024x512 texture like the cascade's own first copy |
| `0012FDE8: 00094A02 -> 316901FF` | `TBP0` from the frame's `FBP` (`andi t1, t3, 0x1ff`) instead of the buffer address `>> 8` |
| `0012FE30: 0009703C -> 00097140` | `sll t6, t1, 5`: pages to 256-byte blocks |
| `0012FE38: 000E703E -> 00000000` | the zero-extension shift that would have discarded it |
| `0012FE5C: 3485000A -> 34850005` | `CLAMP` mode clamp instead of region clamp, so the cascade size no longer bounds the UVs |
| `0012FEF4: A7B0016C -> A7B2016C`, `0012FEF8: A7B0016E -> A7B1016E` | `UV1` from the sprite's own corner (641, 449 in 12.4) instead of `(size + 2) << 4` |
| `0012FE00: 24130008 -> 24130000` | `UV0` 0 instead of 0.5 texel, so `u = x` exactly at any internal resolution |

With `UV0` at 0 and `UV1` equal to the sprite corner, pixel centre `x + 0.5` samples texel
`x + 0.5` at native resolution and internal pixel `j + 0.5` at any upscale; with the game's
own half-texel origin the copy landed half a native pixel off, two pixels at 4x. Measured
frame-exact from a paused savestate (the world and camera freeze under the pause menu while
the post-passes keep running), the copy's edges sit at 0 to +1 internal pixel of the frame's in
every screen region.

## The depth of field

That fixed the smear and left a second, offset outline on every distant building - "double
vision" in the user's words - which the haze redirect could not be blamed for: from the paused
state the copy was aligned, and the doubling did not change between 30 and 60 fps, so it was not
a stale frame either. PCSX2's GameDB carries three hardware fixes for this title, each annotated
"Depth of Field", and the dump has the pass they were written for. Draw #3146 in every frame:

```
#3146  LINE  n=894  xy=[-1..638, -1..445]  z=9586 then 4027
       TEX0 = the frame buffer (bp 0, bw 640, 1024x512)   TEX1 = bilinear
       ALPHA = A:Cs B:Cd C:FIX(64) D:Cd  -> (Cs + Cd) / 2
       TEST  = 0x73801: ZTE, ZTST 3 (GEQUAL), ATE with AFAIL RGB-only
       vertex UVs: u = x + 1.875, v = y + 2.875 (line y samples line y+2)
```

447 horizontal lines per pass, each copying the frame onto itself from roughly (1.4, 2.4)
pixels away at half weight, and only where the depth buffer holds a value below the line's
`z` - the far pixels - in up to three passes at increasing distance (the mission uses two).
That is a depth-graded two-tap blur. At native resolution it softens far edges by a pixel; at
4x internal resolution the copy is drawn sharp, 6-9 pixels from the original, and every distant
silhouette becomes two. The GameDB's `halfPixelOffset: 4` (Align to Native), `nativeScaling: 1`
and `autoFlush: 2` are what turn that double back into a blur, which is the "vaseline" as
first reported.

The line strip is prebuilt at display init (`0x0012A930`: 447 entries, `0x1bf`, with the
corners `0x6bf0`/`0x93e0` and the UV origin `0xe`) into a buffer whose pointer sits at
`0x0027B77C`, refreshed each frame from a request record by the GS-done callback
(`0x0012CEE8`). It is drawn by `0x0012EAE0(dx, dy, z)`, which writes that request record, builds
the texture-blend-test packet and sends the 894 quadwords (`0x0012ECE4`). Eight call sites,
all of the shape:

```
001BE1E0  addiu a0, zero, 16       ; dx = 1 px
001BE1E8  cvt.w.s / mfc1 a2        ; z from a per-level float
001BE1EC  jal  0x12eae0
001BE1F0  daddu a1, a0, zero       ; dy = 1 px
001BE1F4  addiu s4, s4, 1
001BE1FC  bne  s4, 3, loop         ; three depth levels
```

None of them read the return value, so the pass is removed by making the function return at
once: `0012EAE0: 27BDFF80 -> 03E00008` (`jr ra`) and `0012EAE4: FFBF0070 -> 00000000`. No
brightness is involved - a 50/50 blend of the frame with a shifted copy of itself preserves
energy - and the request record simply stops being written, which the callback already treats
as "nothing to update".

Measured at the user's 4x, GameDB fixes at their defaults, from the same savestate, hot-written:

| | far sharpness |
|---|---|
| depth of field on | 5.6 |
| depth of field skipped | 52.6 |

and by eye the window columns of the far facades resolve and every silhouette is single.

## PCSX2 settings that matter now

With the pass gone, the three GameDB fixes have nothing left to fix, and one of them still
costs detail. Same build, 4x, static, far sharpness:

| Hardware fixes | far sharpness |
|---|---|
| GameDB defaults (align to native, auto flush 2, native scaling) | 47.5 |
| manual: auto flush 2, half-pixel offset off, native scaling off | 56.7 |
| manual: everything off | 56.6 |

Align to Native samples the haze redirect's copy at native resolution and lays it over the
frame as a soft veil. The description tells the user to turn it off for this game; auto flush is
kept because it is what guarantees the redirect's frame-buffer read is current. Mip-mapping was
checked too - the scene uses up to five levels with trilinear filtering and a negative LOD bias -
and forcing it off or trilinear on changed nothing (47.5 all three ways), so the far textures
are already at their base level. What remains soft at distance is the resolution of the assets.

Two blind alleys worth recording. Forcing PCSX2's deinterlacer off did not change the
doubling, because the doubling was never the deinterlacer; and a Laplacian sharpness figure
goes *up* when a shifted copy adds a second set of edges, which is how "fixes off is sharper"
was misread for an hour while the depth-of-field twin was the thing being measured.

## What it does not do

The colour-overlay pass at `0x0012F370` (gated by `0x00279EC4`, used for fades and flashes) is
untouched, and so are the fog and the distance models. The haze cascade still runs into its
private buffers every frame - eleven small draws - and was left alone rather than add words.
Missions that set a different haze colour or size through `0x00111C80`, or different
depth-of-field distances, get the same treatment, since neither change depends on the values.
