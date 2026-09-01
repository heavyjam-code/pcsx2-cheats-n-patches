# Devlog: No-Interlacing for Ys VI - The Ark of Napishtim (SLUS-20980)

Record of how the `[No-Interlacing]` group in
[`patches/SLUS-20980_EF9E43EF.pnach`](../patches/SLUS-20980_EF9E43EF.pnach) was made.
The `[60 FPS]` group in the same file is [a separate piece of work](devlog-SLUS-20980-ys-vi-60fps.md).
The game was entry 10 on the [NTSC-U shortlist](no-interlacing-candidates.md#ntsc-u-shortlist) —
"measured full-frame, so far cheaper than Ys V". That prediction held: it is a genuine
TIER-B and the fix is three words. The interesting part is that two of those three words
are somewhere the [Ys V](devlog-SLPM-66360-ys-v-no-interlacing.md) and
[Mega Man X7](devlog-SLUS-20487-mega-man-x7-no-interlacing.md) recipes do not look.

Target: Falcom/Konami (2005), NTSC-U retail, boot ELF `SLUS_209.80` (1,753,008 bytes),
ELF CRC **`EF9E43EF`**. PCSX2 2.8.1 already bundles `SLUS-20980_EF9E43EF.pnach` with
`[Widescreen 16:9]` and `[Fix Analog Deadspot]`, but no interlacing group; a loose file
adding only `[No-Interlacing]` merges with it cleanly.

## Tier measurement

Booted unpatched at 2x internal resolution with deinterlacing set to None, screenshots at
`ScreenshotSize = 2`:

```
title screen   1024x896     -> 512x448, vertical doubles -> TIER-B, full frame
opening FMV    1024x896     -> same
```

Confirmed from RAM rather than pixels. `sceGsGParam` lives at `0x250E10` and reads
`interlace=1, outmode=2 (NTSC), ffmd=0, GS rev 0x1b`. **`ffmd = 0` is FIELD mode** — the
GS reads alternate lines out of a full-height buffer — which is exactly the shape of a
full-frame renderer, and the opposite of the `ffmd = 1` FRAME mode that Ys V and X7 used
to display a 224-line field buffer. There is no half-line bob to chase here.

## How the game does video (map of the ELF)

EE virtual addresses; the single loadable segment maps `file_offset = va - 0x100000 + 0x80`.

| Address | What it is |
|---|---|
| `0x100278` | `sceGsResetGraph(mode, interlace, omode, ffmd)` — shorts sign-extended via `sll`/`sra` 16; writes GParam; tail-calls `SetGsCrt` at `0x10b5a0`. Three callers: `0x217784` (real init), `0x222040` and `0x22435c` (both `mode=1`, GS reset only, GParam untouched) |
| `0x100408` | GParam getter, a two-instruction leaf returning `0x250E10` |
| `0x100530` | `sceGsSetDefDispEnv(env, psm, w, h, dx, dy)` — SMODE2 into `env+8`, DISPFB `env+0x10`, DISPLAY `env+0x18` |
| `0x1005F0` / `0x1005FC` / `0x100600` | the three SMODE2 constants: 2 progressive, 3 interlaced FRAME, 1 interlaced FIELD |
| `0x10066C` | NTSC **interlaced** `DISPLAY.DY = dy + 0x32` |
| `0x1006A4` | NTSC interlaced **FRAME** `DH = 2h-1`; `0x100758` is the PAL twin |
| `0x100768` | the FIELD tail, shared by NTSC and PAL: `DH = h-1` |
| `0x1006DC` | NTSC **progressive** `DISPLAY.DY = dy + 0x19` |
| `0x1007F4` | a third arm of the same builder for `omode == 0x50` (DTV480P), never reached |
| `0x1008A8` | `sceGsPutDispEnv` — branches on GS revision at `0x1008BC`; rev is `0x1b` here so the live arm is `0x10090C`, writing PMODE, **SMODE2**, DISPFB2, DISPLAY2, BGCOLOR |
| `0x21F010` | the engine's own display setup: calls `sceGsSetDefDispEnv(env, psm=0, w=512, h=448, dx=0, dy=1)`, then **overwrites the env** and pushes it to the GS by hand |
| `0x21F0F0` | inside that: `or v1,v1,a0` assembling `SMODE2 = INT | (FFMD<<1)` from GParam |
| `0x21F140` | `sd v1, 8(s4)` — the engine's SMODE2, written over libgraph's |
| `0x21F1B0` | `sd a0, 0x20(0x12000000)` — a direct SMODE2 write from game code |
| `0x21F2A0` | reads CSR bit 13 into `*0x2E09DC`, but only while `GParam.interlace != 0` |
| `0x2E0A60` / `0x2E0A88` | the two engine display envs, 0x28 bytes each, selected by `*0x2E09E4 & 1` |
| `0x2E5990` / `0x2E59B8` | **the movie player's own display envs**, base returned by `0x222710` |
| `0x2E0A04` | video-mode flags, hardwired to 7 by `0x2174A0`: bit0 interlace, bit1 → `ffmd = !bit1`, bit2 picks PMODE `ALP` 0x7f vs 0xff |
| `0x217730` | builds the `sceGsResetGraph` arguments from those flags: always `(0, 1, 2, 0)` |

## The trap that is specific to this game

Both prior patches in this repo work by rewriting libgraph's SMODE2 constant. Here that
alone does **nothing for gameplay**, because `0x21F010` calls `sceGsSetDefDispEnv` and then
immediately recomputes `env->smode2` itself:

```
0021f0d0  xori a0, s1, 1        ; a0 = ffmd
0021f0e0  dsra32 v1, v1, 0      ; v1 = (GParam.interlace == 1)
0021f0e8  dsll a0, a0, 1        ; a0 = ffmd << 1
0021f0f0  or   v1, v1, a0       ; v1 = INT | (FFMD<<1)
0021f12c  lbu  a0, 8(s4)        ; preserve the DPMS bits libgraph put there
0021f140  sd   v1, 8(s4)        ; env->smode2 = v1
```

Whatever libgraph wrote is thrown away one instruction later. The engine also pushes the
env to the GS itself at `0x21F1A0`-`0x21F1DC` instead of going through
`sceGsPutDispEnv`. So the live patch site is `0x21F0F0`: replacing `or v1,v1,a0`
(`00641825`) with `addiu v1,zero,2` (`24030002`) forces `SMODE2 = 2` — INT=0, FFMD=1,
libgraph's own progressive value — and `v1` is not read again until `0x21F13C`, so nothing
else changes.

*Lesson: before patching a libgraph constant, check whether the game writes the same field
back. Grepping for writers of `env+8` finds this in one pass; assuming libgraph is
authoritative does not.*

## DH needs no patch here, DY does

Because the game runs FIELD mode, the interlaced branch already lands on the shared tail at
`0x100768` and computes `DH = h-1 = 447` — the same value the progressive branch would
produce. There is no `2h-1` doubling on the live path and therefore no PAL-twin hazard.

`DISPLAY.DY` is the one that differs: `dy + 0x32` interlaced versus `dy + 0x19`
progressive, because DY counts half-lines while `SMODE2.INT = 1` and real scanlines once it
is 0. Live readback of the unpatched envs:

```
env0 @002E0A60  smode2=1  DX=636  DY=50  MAGH=4  MAGV=0  DW=2559  DH=447   -> 512x448
env1 @002E0A88  smode2=1  DX=636  DY=50  ...                                 (identical)
```

so `0x10066C: 24420032 -> 24420019` is the unit partner of the INT flip.

**Measured, not assumed.** Booting with the SMODE2 word alone and Screen Offsets
(`pcrtc_offsets`) enabled puts 48 black rows at the top of the frame and moves the picture
down by exactly 50 pixels at 2x — 25 scanlines, the difference between 0x32 half-lines and
0x19 lines:

| Build (title screen, 2x, Screen Offsets ON) | First non-border row | Best vertical shift vs. the finished patch |
|---|---|---|
| unpatched | 1 | — |
| SMODE2 only | **48** | **-50 px** (MSE 4.35 there, 2503 at zero) |
| SMODE2 + DY | 1 | 0 px, **byte-identical to unpatched** |

Byte-identical is the result to want: the patch must not move the picture, only change how
it is scanned out.

## The movie player is a second display env

`sceGsSetDefDispEnv` has five callers. Four are inside libgraph; the fifth is the engine's
`0x21F088`. Following the libgraph one that actually reaches `sceGsPutDispEnv`
(`0x1019F8`, called from `0x22224C` and `0x2222B8`) leads to a base pointer returned by
`0x222710` — and that is **`0x2E5990`, not `0x2E0A60`**. The movie player builds its own
pair of display envs and pushes them with stock libgraph, so it never runs the engine's
SMODE2 override.

That matters more than it looks. With only the first two patches the movie envs would keep
`SMODE2 = 1` while still picking up the patched `DY = 0x19` from the shared builder — an
interlaced env with a progressive offset, i.e. the movies sitting 12 lines high the moment
anyone turns Screen Offsets on. `0x100600: 24020001 -> 24020002` closes it, and live
readback with all three patches shows the whole set agreeing:

```
game0 smode2=2 DY=25 DH=447 | game1 smode2=2 DY=25 DH=447
mov0  smode2=2 DY=25 DH=447 | mov1  smode2=2 DY=25 DH=447
```

## What the patch is actually worth on PCSX2

Worth being honest about, because it is not "removes visible shaking".

PCSX2 already understands a FIELD-mode full-height buffer and does not deinterlace it. A
sweep of every deinterlace mode on the unpatched game, one boot, one savestate, native
resolution, measuring line-alternation energy `mean|row[i] - (row[i-1]+row[i+1])/2|`:

| Mode | Automatic | Off | Weave | Bob | **Blend** | Adaptive |
|---|---|---|---|---|---|---|
| comb energy | 3.461 | 3.461 | 3.461 | 3.460 | **2.089** | 3.461 |

Everything except Blend is bit-for-bit the same picture. Blend is the outlier, and it is
not removing an artefact — it is averaging neighbouring lines on an image that never had
one, which costs 40% of the vertical line-to-line detail. Patched and unpatched title
screens captured from clean boots at PCSX2's default Automatic setting are **byte-identical**.

So the patch buys two things: the game genuinely reports progressive output rather than
being reconstructed as progressive by the emulator, and `gsinterlacemode=1` pins the
deinterlacer Off so a globally-set Blend cannot soften this game. The `description=` in the
pnach says exactly that and nothing more.

## Verification

1. **Static**: capstone MIPS64-LE decoded one instruction at a time (R5900 `lq`/`sq`/MMI
   desynchronise a streaming disassembler); whole-image `jal`/`j` xref map;
   `lui`-base-resolved scans for every access to the mode globals and the display envs —
   which returned *no* stores into either env struct from outside the two routines above.
2. **Live state via PINE**: GParam, all four display envs and both patched words read back
   from EE RAM every run, at boot, on the title screen, in an FMV and in gameplay.
3. **A/B from clean boots** with an identical scripted key sequence, which this game
   replays deterministically (independent boots produce byte-identical frames).
4. Played from cold boot through the Falcom logo, the opening FMV, the title screen, New
   Game, the opening cutscene and into field gameplay. No hang, output 1024x896 throughout,
   frame-to-frame best vertical shift 0 px on a 4-frame gameplay burst.

An eight-agent static pass over the same ELF, run blind, independently derived the same
map and the same tier, and proposed the same DY word.

## Deliberately left alone

- **GParam and the `sceGsResetGraph` arguments.** `0x21F2A0` samples CSR.FIELD only while
  `GParam.interlace != 0`; zeroing it is the Ys V attempt-1 trap. Output constants only.
- **PAL paths** (`0x100758`, `0x1006E0`+): unreachable, `0x2E0A06` is hardwired to 2.
- **The engine's `DY - 1` nudge** at `0x21F1EC`, and this one deserves a follow-up rather
  than a shrug. The engine pushes `DISPLAY1` from the env at `0x21F1D4`, *then* decrements
  the env copy's DY by one scanline and writes it back — and the live PMODE is `0x7F67`,
  i.e. `EN1 = EN2 = 1`, `MMOD = 1`, `SLBG = 0`, `ALP = 0x7F`. Two read circuits, merged at
  roughly 50%, one scanline apart: that is the shape of a **vertical flicker filter**, the
  standard interlace-era anti-shimmer trick. If that reading is right it is dead weight once
  the output is progressive — pure half-line blur bought to fight flicker that no longer
  exists — and `0x21F1EC: 2484FFFF -> 00000000` would sharpen the game for free.
  It is not in this patch because it was not isolated end to end (which circuit ends up
  driving the visible frame was not pinned down), and because it changes pixels: every
  verification above rests on the patched output being byte-identical to the unpatched one,
  and this would break that. Worth its own group and its own A/B, not a silent addition to
  a no-interlacing patch.
- **The `0x50` DTV480P arm of the env builder** at `0x1007F4`. Unlike Cowboy Bebop, this
  game has no mode-table entry that would ever ask for it — `0x217730` builds `omode` from
  a hardwired 2 — so reaching it would mean writing the mode selection, not forcing it.

## Final patch summary

| Patch | Purpose |
|---|---|
| `0021F0F0: 00641825 → 24030002` | engine display setup: `SMODE2 = 2` (INT=0, FFMD=1) instead of rebuilding it from GParam |
| `0010066C: 24420032 → 24420019` | `sceGsSetDefDispEnv` NTSC interlaced `DISPLAY.DY` base 50 → 25, the unit partner of the INT flip |
| `00100600: 24020001 → 24020002` | the same builder's interlaced-FIELD SMODE2 constant, which is what the **movie player's** envs at `0x2E5990` use |

Plus `gsinterlacemode=1` so PCSX2 stops deinterlacing an image that is now progressive.
