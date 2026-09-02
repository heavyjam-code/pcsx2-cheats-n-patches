# Devlog: No Motion Blur for The Sword of Etheria (SLES-53768)

How the `[No Motion Blur]` group in
[`patches/SLES-53768_88E95888.pnach`](../../patches/SLES-53768_88E95888.pnach) was made.
Same disc, ELF and CRC as the [60 FPS devlog](../60fps/devlog-SLES-53768-sword-of-etheria-60fps.md);
the ELF map there (`main` segment at `0x4c0000`, file offset `va - 0x4c0000 + 0x100`, second
segment `0x100000..0x154000` at file offset `0x5d3800`, `$gp = 0x00A28070`, GS driver at
`0x6e4000..0x700000`) is assumed here. PCSX2 2.8.1, Vulkan, 2x internal resolution throughout.

Symptom, reported after the 60 FPS patch went in: anything that moves drags a soft trail. It
looked like a motion blur, and it was one, but it turned out to be one the game had always had.
At 30 fps the trail is a discrete after-image a full 33 ms behind the object; at 60 fps it is
half as far behind and there are two of them in the same span, which the eye reads as smear.

The fix is not to delete the effect. Deleting it costs a quarter of the picture's brightness and
all of its glow, because the trail and the brightness are the same pass. The fix redirects the
pass at the frame being drawn instead of the previous one, which keeps the light and drops the
time component.

## Reading the draw list

One frame captured from the tutorial-fight savestate with `GSDumpSingleFrame` rebound to `F7`.
The mission renders 111 draws per frame into two 512x448 display buffers at `0x0000` and
`0x0e00` (FBW 8, PSMCT32), alternating, with a 16-bit Z at `0x1c00`, a 128x128 bloom chain at
`0x3f00`/`0x3e00`, and this, drawn after the scene and before the bloom:

```
#94  TRIFAN n=24 IIP+TME+ABE   FRAME FBP=0070 (0x0e00)   TEX0 TBP0=0000 TBW=8 PSM=00 TW=9 TH=9
     ALPHA A=0 B=2 C=0 D=1 FIX=0     ZTST=1 ZMSK=1     CLAMP WMS=1 WMT=1
     12 quads of 128 x 152.67 tiling 0..512 x 0..458, ST at 1:1 (Q = 2.0)
     RGBAQ = 80 80 80 20  on every vertex
```

The frame is being drawn into `0x0e00` and the texture is `0x0000`, the *other* display
buffer: the frame that was presented last vblank, bloom, HUD and all. The blend is
`(Cs - 0) * As + Cd` with `As = 0x20/128 = 0.25`, so every pixel of the new frame gets a quarter
of the old one added to it. The next three frames in the dump (draws `#205`, `#316`, `#427`)
do the same with the buffers swapped. Nothing else in the frame samples either display buffer
except the bloom downsample, which reads the buffer being drawn.

Because the old frame already contained a quarter of *its* predecessor, this is a feedback
series, not a single tap:

```
out_n = scene_n + 0.25 * out_(n-1)
      = scene_n + 0.25 * scene_(n-1) + 0.0625 * scene_(n-2) + ...
```

A still pixel converges to `1 / (1 - 0.25) = 1.333` times its rendered value (less where it
clips). A moving edge leaves copies at 25 %, 6 %, 1.5 % behind it. The same pass is both the
game's "glow" and its trail, and no constant inside it separates the two: turn the alpha down
and both go together.

## Finding the emitter

The register words in the draw are not in the ELF. The packet lives in the driver's display
list ring at `0x00AAEF00` (and `0x00B2E2A0` for the other buffer's frame), assembled per frame
as one A+D register write per GIF tag: `TEX1 K=-64`, `TEXFLUSH`, `TEX0`, `TEX1 K=540`,
`MIPTBP1`, `MIPTBP2`, then a DMA `CALL` to a VU1 microprogram at `0x0083F180` and 128 quadwords
of vertex data with the colour as floats `(255, 255, 64, 255)`, scaled by `0.502` (`0x3f008313`
at `0xA200C0`) on the way to the GS. That is where the `0x20` alpha comes from: `64 * 0.502`.

Two baits on the way, both worth recording:

- `TEX1.K = 540` looked like the most distinctive constant in the packet. `0x21c` appears as an
  immediate at five places in the ELF and every one of them is the JST time-zone offset in
  minutes (`0x7afda8` returns it as a default). The texture descriptor's K field is simply
  uninitialised memory that happened to hold 540. Likewise `MIPTBP1 = 0x00871EE0_00000900`: the
  `0x871ee0` is a linked-list head in `.data` that overlaps the descriptor's mip fields.
- The VU1 quad dispatchers at `0x6fda80..0x6fdc10` (`0x9ec5e8`/`0x9ec5f8` hold the two
  microcode descriptors) have no `jal` callers; the driver calls them through a command table.
  Walking up from them goes nowhere.

What worked was walking *down* from the data. Searching RAM for the packet's `TEX0`
(`0x0000000264020000`) and the `(0x900, 0x871ee0)` pair found one non-ring copy, a texture
descriptor at `0x00CB62B0` inside a heap image object at `0x00CB6290`:

```
00cb6290  owner=00cb59a0  0  0  w=512  h=512  bpp=32  pitch=0x800  0
00cb62b0  flags=05008082  0  512  512  0x800  0  0  tex0lo=64020000
00cb62d0  tex0hi=2  ..  K=021c  miptbp=0900 00871ee0 00871ee0 ..
```

`flags & 7 == 2` is the tell. The driver's texture emitter at `0x6ffc44` (context 1; `0x700380`
is the context-2 twin) does this for type-2 images:

```
006ffc50  lbu   v1, 0x20(s1)          ; image flags
006ffc58  andi  v1, v1, 7
006ffc5c  bne   v1, 2, 0x6ffca8       ; other types use TBP0 as stored
006ffc64  lw    v0, -0x797c(gp)       ; 0xA206F4: the driver's frame counter
006ffc68  andi  v0, v0, 1
006ffc6c  beqz  v0, 0x6ffc80
006ffc78  ld    a0, -0x2d80(v0)       ; odd:  FRAME shadow B at 0xA8D280 = 0x80000  (FBP 0x00)
006ffc84  ld    a0, -0x2ef0(v0)       ; even: FRAME shadow A at 0xA8D110 = 0x80070  (FBP 0x70)
006ffc8c  andi  a0, a0, 0x1ff
006ffc90  dsll  a0, a0, 5             ; FBP << 5
006ffca0  daddu v0, v0, a0            ; TBP0 = descriptor TBP0 (0) + that
```

A type-2 image is "a display buffer, chosen by frame parity". The three places that pick the
*render target* (`0x6e7f4c`, `0x6e88d8`, `0x6f2898`) use the same counter with the opposite
mapping (odd -> A, even -> B), so type 2 always resolves to the buffer that is not being drawn:
the previous frame. Four image objects carry the flag (`0xcb6290`, `0xcb64d0`, `0xcb6710`,
`0x1d62ec0`), and each is the texture of one screen-quad object of the same class:

| Object | Slot | Colour at `+0x34` | Texture |
|---|---|---|---|
| `0x00CB6580` | `0x00A27D2C` (`gp-0x344`) | `00000000` | `0xcb6710` |
| `0x00CB6100` | `0x00A27D30` (`gp-0x340`) | `40ffffff` | `0xcb6290` |
| `0x00CB6340` | `0x00A27D34` (`gp-0x33c`) | `00000000` | `0xcb64d0` |
| `0x01D62D30` | a mission object at `0x1d603a0` | `50ffffff` | `0x1d62ec0` |

Vtable `0x009F45C0`, constructor `0x00591DA0`. The constructor sets the colour at
`0x591e64..0x591e8c`: `0xff` into bytes `+0x34..+0x36` and `0x40` into `+0x37`, from
`addiu v1, zero, 0x40` at **`0x00591E6C`**. The three static slots are constructed during engine
init, before the video-format prompt (frame counter 991 at the prompt in a cold boot). Only the
slot-1 object draws in the tutorial fight; the two with colour 0 are skipped, and a live write
of `0x00ffffff` into slot 1's colour removed draw `#94` from the next dump entirely, which
confirmed the object and that alpha 0 means "don't draw".

## Why not just delete it

That live write is also the measurement that killed the obvious patch. Same savestate, same
frame, alpha zeroed:

| | mean luma | 95th pct | clipped |
|---|---|---|---|
| stock | 51.95 | 101.2 | 0.239 % |
| feedback removed | 39.28 | 70.7 | 0.000 % |

Minus 24 % overall, the gold and red characters gone flat, nothing clipping any more. The whole
"glowing" look of the game is this accumulation pushing highlights into clip. Per
[the Crimson Tears lesson](devlog-SLUS-20948-crimson-tears-remove-blur.md) an additive pass has
to be paid back if removed, and a ShadeBoost curve cannot reproduce a 1.33x multiply that
clips. Better to keep the multiply and lose only the delay.

## The fix: sample the frame being drawn

Swapping the two `ld` displacements at `0x6ffc78`/`0x6ffc84` makes type-2 images resolve to the
buffer *being drawn*. The blend then reads its own target: `out = scene + As * scene`, a flat
gain with no history. Verified live in a dump: draws `#94`, `#205`, `#316`, `#427` now show
`FB=0e00 TBP=0e00`, `FB=0000 TBP=0000`, alternating with the target. PCSX2 handles a render
target sampled as its own texture through its feedback-loop path; the 12 tiles do not overlap,
and the frames came out clean at 2x.

With the alpha left at 0.25 the gain is 1.25x, short of the stock series' 1.33x (measured
1.20x, since stock also accumulates bloom and the vignette overlay, which sit after this draw).
So the constructor's `0x40` goes up. Deterministic A/B: both sides load the same savestate and
the stock side gets the original words written back; captures 6 s after load; luma difference
against stock over the full frame and over the top 300 lines of background:

| alpha byte | GS As | mean luma | diff vs stock | mean abs diff | top-300 diff |
|---|---|---|---|---|---|
| stock (previous frame, 0x40) | 0.25 | 50.66 | | | |
| 0x40 | 0.25 | 46.83 | -3.82 | 4.68 | -3.31 |
| 0x50 | 0.31 | 48.89 | -1.76 | 2.40 | -1.61 |
| 0x56 | 0.336 | 49.76 | -0.89 | 1.69 | -0.88 |
| 0x5a | 0.352 | 50.24 | -0.42 | 1.51 | -0.52 |
| 0x60 | 0.375 | 51.11 | +0.46 | 1.66 | +0.20 |
| 0x66 | 0.40 | 51.83 | +1.17 | 2.14 | +0.76 |

The zero crossing is between `0x5a` and `0x60`; `0x5c` (92, which the `0.502` scale truncates to
`As = 46/128 = 0.359`, the same GS value as `0x5d`) lands within half a luma unit of stock.
Re-measured boot-to-boot (each side booted with its own patch set, same savestate, only the
object's colour byte written over PINE): stock 52.82, patched 52.90 mean luma, difference
`+0.08`, top-300-line background `-0.27`.

What does not match is a tint. Per-channel means go from `R 52.9 G 51.1 B 61.9` to
`R 52.1 G 52.1 B 59.0`, and mean chroma (`|channel - luma|`) from 7.27 to 6.50, evenly over the
frame rather than around the glowing characters (far from any bright pixel: 5.32 vs 4.39;
in the 3-40 px halo: 8.54 vs 7.83). The reason is draw order. The feedback runs *before* the
bloom composite (`#107`), the additive overlay (`#108`) and a full-screen lerp haze (`#110`,
a 256x256 8-bit texture over a 36-triangle strip), so stock accumulated those too, at the
same 1.33x, while the self-blend multiplies only what is drawn before it. The haze is blue, so
the patched frame is about 5 % less blue and 2 % greener. The overlay was ruled out as the
source by zeroing its colour word at `0x998DF4` on a stock boot: luma and chroma moved by
`0.1`. Moving the feedback later in the frame was tried through the object's `+0x38`/`+0x3c`
fields (5 and 2, set by the constructor); values 3-8 left the draw where it was.

The two words at `0x7003ac`/`0x7003b4` are the same selector in the driver's context-2 emitter.
Nothing in the mission uses it, but the class could draw through it elsewhere, and the patch
should mean "type-2 images are the current frame" everywhere or nowhere.

## The patch

| Patch | Purpose |
|---|---|
| `006FFC78: DC44D280 -> DC44D110` | context-1 texture emitter: odd frames take FRAME shadow A |
| `006FFC84: DC44D110 -> DC44D280` | context-1 texture emitter: even frames take FRAME shadow B; together, type-2 images resolve to the buffer being drawn |
| `007003AC: DC44D280 -> DC44D110` | the same swap in the context-2 emitter |
| `007003B4: DC44D110 -> DC44D280` | |
| `00591E6C: 24030040 -> 2403005C` | screen-quad constructor: default alpha 64 -> 92, so the self-blend's gain matches the old series |

`place=1` for all five. The constructor runs during engine init well after the first vsync
(verified in a cold boot: slot 1's colour reads `5cffffff` at the video-format prompt), and the
driver words are re-applied every frame, which also covers a stock savestate loaded into a
patched session. One caveat with such a state: the effect objects inside it still carry alpha
`0x40`, so until the next scene constructs fresh ones the picture is a 1.25x gain instead of
1.36x, about 7 % darker than stock. A save made under the patch, or any scene change, fixes it.

Rejected:

- Zeroing the alpha or skipping the draw (`-24 %` luma, see above).
- Changing the image type from 2 to something absolute. The descriptor's TBP0 is 0, so every
  other type would pin it to buffer A and be wrong on alternate frames.
- Compensating a removed pass with ShadeBoost. The stock effect is multiplicative and clips;
  gamma or gain sliders neither clip the same way nor belong in a `.pnach`.
- Tinting the self-blend to put the missing blue back. The constructor writes R, G and B from
  one register (`addiu a0, zero, 0xff` at `0x591e68`, three `sb`), so a per-channel value needs
  code that is not there. Raising the alpha until blue matched (`~0x6c`) would push red and
  green 5 % over stock instead.

## Notes for next time

- The parity swap is a two-word change with no knowledge of the client. Any Konami title on this
  driver that ships a "previous frame" trail can probably take the same patch after confirming
  the type-2 mapping.
- PINE-writing a code word that a `place=1` pnach line also targets killed PCSX2 with
  `[EE] Impossible block clearing failure` within a second. The earlier live code writes here
  were fine because no pnach line covered them yet. Once the patch is installed, A/B by booting
  each side with its own patch set and load the same savestate; write only data over PINE.
- A live alpha write shows the *object*; it does not show the *constructor*. The static home
  of a colour byte was found by disassembling the ctor reached from the vtable, not by grepping
  for the word (`0x40ffffff` exists in `.data` five times and none of them is it).
