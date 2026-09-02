# Devlog: Remove Blur for Ghost in the Shell: Stand Alone Complex (SLUS-21006)

How the `[Remove Blur]` group in
[`patches/SLUS-21006_95CC86EF.pnach`](../../patches/SLUS-21006_95CC86EF.pnach) was made.
Same disc, ELF and CRC as the
[No-Interlacing devlog](../deinterlace/devlog-SLUS-21006-gits-sac-no-interlacing.md);
the ELF map there (`file_offset = va - 0xff000`, display object at `0x396960`, `gp =
0x476070`) is assumed here.

Symptom: with No-Interlacing on and the game confirmed progressive, the picture is
still soft — and soft in a specific way. Cel outlines, the weapon icon, the ammo
rounds and the HUD rings all smear **vertically** while horizontal edges stay crisp.
That asymmetry is the tell, and it is the same class of effect as the
[Cowboy Bebop flicker filter](devlog-SLPS-25550-cowboy-bebop-remove-blur.md), just
heavier: Bebop blends one offset copy at 37%, this game blends three lines into every
output line.

The [method from that job](devlog-SLPS-25550-cowboy-bebop-remove-blur.md) transferred
almost intact — dump a frame, read the draw list, find the emitter — and finding it
took minutes rather than the two hours of ELF string-hunting Bebop cost.

## Reading the draw list

`GSDumpSingleFrame` rebound to plain `F7` (Shift+F8 cannot be posted to an unfocused
window), one frame captured from the gameplay savestate: 1,940 draws per frame, and
PCSX2's own GameIndex already hints at what is coming — this game carries
`halfPixelOffset: 2 # Aligns post effects`, `nativeScaling: 1 # Fixes post effects`
and `textureInsideRT: 1 # Fixes post shuffles`.

The relevant three are the **first** draws of every frame, not the last:

```
#0 SPRITE n=10 TME       FBP=0000 PSM=01   TEX0 TBP0=1400 PSM=00 MMAG=1
     xy y = 0 .. 448    uv v = 0.5 .. 448.5
#1 SPRITE n=10 TME+ABE   FBP=0000 PSM=01   TEX0 TBP0=1400          ALPHA A=Cs B=Cd C=FIX D=Cd FIX=64
     xy y = 1 .. 449    uv v = 0.5 .. 448.5
#2 SPRITE n=10 TME+ABE   FBP=0000 PSM=01   TEX0 TBP0=1400          ALPHA A=Cs B=Cd C=FIX D=Cd FIX=42
     xy y = -1 .. 447   uv v = 0.5 .. 448.5
```

`FBP=0x000` is the **display** buffer — `DISPFB` reads `FBP=0 FBW=10 PSM=1` — and
`TBP0=0x1400` is the render target the scene was drawn into (`FBP=0x0a0`). So the
game does not display what it rendered. It renders into `0x1400`, then at the top of
the next frame composites that into `0x0000` in three passes, each ten 64-pixel
strips wide:

| pass | screen y | texel v | tap | blend |
|---|---|---|---|---|
| #0 | 0 … 448 | y + 0.5 | line **y** | opaque base copy |
| #1 | 1 … 449 | y − 0.5 | line **y − 1** | `FIX=64` → 64/128 = **50%** |
| #2 | −1 … 447 | y + 1.5 | line **y + 1** | `FIX=42` → 42/128 = **32.8%** |

(#2's y reads as 4095 in the dump because `XYZ2` stores 12.4 unsigned and the value
is `0xFFF0`; with `XYOFFSET = 0` that is −1.)

Compose them and the weights land on almost exactly equal thirds:

```
after #1:  0.5·above + 0.5·centre
after #2:  0.328·below + 0.672·(that)  =  0.336·above + 0.336·centre + 0.328·below
```

64 and 42 are not arbitrary — they are 128/2 and 128/3, the standard way to build a
running average of three taps with two blends. **Every output line is the mean of
three source lines.** That is a textbook interlace flicker filter, and on a
progressive display it is a vertical box blur and nothing else.

## Finding the emitter

The ALPHA register values do not exist in the ELF — as on Bebop, searching for them
there finds nothing. In EE RAM they appear exactly once each, at `0x396cf0` and
`0x396e90`, which is the display object `+0x390` and `+0x530`: two pre-built GIF
packets, `A+D` `nloop=4` (RGBAQ, TEX0_1, TEX1_1, **ALPHA_1**) followed by a
`REGLIST nloop=10` vertex block, laid out on a `0x1A0` stride.

Writing 0 over the `FIX` word lands and is reverted within one or two frames, so the
packets are rebuilt every frame — engine state, not configuration, exactly the trap
the Bebop job recorded. But this time the emitter did not need the stack-residue
hunt, because it materialises both constants inline at `0x1b9944`:

```
1b9944  lwc1  f20, -0x4210(gp)      ; flicker-filter parameter, 0.0 in the ELF and live
1b9948  mtc1  zero, f0
1b994c  c.eq.s f20, f0
1b9950  bc1f  0x1b99d4              ; f20 != 0 -> scaled variant
1b996c  jal   0x103440              ; base copy, t0 = 0x60 (bilinear), opaque
1b9988  addiu a3, zero, 0x40        ; <-- 64
1b998c  dsll32 a3, a3, 0
1b9990  ori   a3, a3, 0x64          ;     a3 = 0x0000004000000064  = ALPHA_1, FIX=64
1b9998  jal   0x1034f8              ; tap at y-1
1b99b8  addiu a3, zero, 0x2a        ; <-- 42
1b99bc  dsll32 a3, a3, 0
1b99c0  ori   a3, a3, 0x64          ;     a3 = 0x0000002a00000064  = ALPHA_1, FIX=42
1b99c4  jal   0x1034f8              ; tap at y+1
```

**A note on how this was nearly missed.** The first scan for `li rt, 42` matched the
word against `0x24000000` under the mask `0xffff0000` — which pins the `rt` field to
zero as well as `rs`, so it only ever matches `addiu $zero, $zero, imm` and returned
nothing for 42, `0x42` and `0x64` alike. That empty result was read as "the constants
are computed, not immediate" and sent the search off toward data tables and
displacement scans (one of which, `sw v1, 0x394(v0)` at `0x1296d0`, looked like a
direct hit on the ALPHA `FIX` word and is in fact a jump table being filled with
`0x2F4xxx` function pointers — the base-resolution trap again). Masking an immediate
comparison must clear only `op` and `rs`: `(x & 0xfc1f0000) == 0x24000000`.

## The patch

```
patch=1,EE,001b9988,word,24070000     ; li a3, 0  -> FIX = 0
patch=1,EE,001b99b8,word,24070000     ; li a3, 0  -> FIX = 0
```

With `FIX = 0` the blend `out = (Cs − Cd)·FIX/128 + Cd` collapses to `out = Cd`: both
taps still draw but contribute nothing, leaving the display buffer holding the base
copy alone. The base copy's UVs are texel-centred and 1:1 (`u 0.5..64.0` over
`x 0..63.5`, `v 0.5..448.5` over `y 0..448`) with bilinear filtering, so what reaches
the screen is an exact copy of the render target.

Zeroing the alpha rather than skipping the two `jal`s is deliberate: `0x1034f8`
returns the next packet slot in `v0`, which the following call consumes as `a0` and
the epilogue returns as `t5`. NOP-ing the calls would break that chain.

## Verification

Boot-to-boot from the shared gameplay savestate, 4× internal resolution, No-Interlacing
on in both runs, only the two blur words differing:

| metric | blur on | blur off | change |
|---|---|---|---|
| mean `abs(dY/dy)` — vertical detail | 0.9715 | 1.2652 | **+30.2%** |
| mean `abs(dY/dx)` — horizontal, the control | 1.0003 | 1.0766 | +7.6% |
| v/h ratio | 0.971 | 1.175 | — |
| mean RGB | 37.60, 49.02, 69.71 | 37.75, 49.19, 69.87 | **+0.06%** |
| std (contrast) | 34.64 | 35.17 | +1.5% |

The vertical/horizontal split is the whole argument: a vertical-only filter should
lift vertical gradient energy far more than horizontal, and it does, moving the v/h
ratio from below 1 (vertically softer than horizontally — which is not what a
correctly rendered frame looks like) to above it. The residual horizontal gain is
real: sharper lines raise the gradient across diagonal edges too.

**Brightness is free here.** Unlike the bloom case recorded in
[the Bebop notes](devlog-SLPS-25550-cowboy-bebop-remove-blur.md), the three weights
sum to one, so this is an averaging filter rather than an additive one — the mean
moves by 0.06% and no ShadeBoost gamma/saturation compensation is wanted.

## Deliberately left alone

**The scaled variant at `0x1b99d4`.** When the parameter at `gp-0x4210` is non-zero
the function takes a different branch and emits three taps whose `FIX` values are
computed — `(1 − f20)·128 / f21`, then that × 0.5, then × 0.33, with `f21 = 1.83` and
the scale `0.33` living at `gp-0x6a04` / `gp-0x6a00`. Notably it emits **no opaque
base copy**, so it is compositing onto something already present and is more likely a
crossfade than the steady-state filter. The parameter is `0.0` in the ELF and stayed
`0.0` across every sample taken in gameplay, so the fixed path is the one that is
always on; zeroing the alpha in the scaled path would risk flattening a real effect
to remove a blur that may never appear. If a future scene is found where the picture
softens again, that branch is where to look.

A third case exists: `f20 >= 1.0` jumps straight to the epilogue and emits nothing at
all, which would be the game's own "no filter" mode — but since it also skips the base
copy, taking it would require knowing what the caller does with `DISPFB` instead. Not
worth the risk when two words already do the job.
