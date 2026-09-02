# Devlog: No-Interlacing for Samurai Champloo: Sidetracked (SLUS-21343)

Record of how [`patches/SLUS-21343_7A5B4F80.pnach`](../../patches/SLUS-21343_7A5B4F80.pnach)
was made. One word, at an address inside `sceGsResetGraph`, and everything else — the
`SMODE2` flag, the `DISPLAY` height, the `DISPLAY` origin, and the game's own half-scanline
field offset — follows from it through code that was already in the build.

Target: Bandai / Grasshopper Manufacture (2006), the `Samurai Champloo Sidetracked (UNDUB)`
ISO, boot ELF `SLUS_213.43` (3,457,456 bytes), ELF CRC **`7A5B4F80`**. The undub is
audio-only: that CRC is the retail one, and PCSX2's `resources/patches.zip` ships a
`SLUS-21343_7A5B4F80.pnach` for it (ElHecht's `[Widescreen 16:9]`, the only group any region
has), so the build is confirmed without a second dump. Tested on PCSX2 2.8.1, Vulkan.

## Why it was worth looking at

The [candidates list](no-interlacing-candidates.md) had this game filed under *no evidence
the artefact is actually bad* — the weakest tier, ranked last however cheap. That grade was
wrong, and cheaply so: the game turns out to be a genuine field renderer whose jitter is
present in every frame of every scene.

## How the game does video (map of the ELF)

EE virtual addresses; the loadable segment maps `file_offset = va - 0x100000 + 0x80`. No
`.sndata`/`SNR1` symbol table, so this was ordinary code reading — but the game links Sony's
`libgraph` unmodified, which makes most of the map free.

| Address | What it is |
|---|---|
| `0x36adc0`+`0x10*n` | syscall stub table; `SetGsCrt` (#2) is the stub at `0x36ade0` |
| `0x369268` | `sceGsResetGraph(mode, inter, omode, ffmd)` — fills GParam, tail-calls `SetGsCrt`. **Two callers**, `0x10d278` and `0x10eff4`, both `(0, 1, 2, 1)` |
| `0x369520` | `sceGsSetDefDispEnv` — the DH/DY builder |
| `0x369898` | `sceGsPutDispEnv` — pushes PMODE/SMODE2/DISPFB/DISPLAY/BGCOLOR at env `+0/+8/+0x10/+0x18/+0x20`. One caller, `0x10c924`, every frame |
| `0x369a20` | `sceGsSetDefDrawEnv` — `XYOFFSET = ((2048−w/2)<<4) | ((2048−h/2)<<4)<<32` |
| `0x36a120` | **the half-offset helper** — recomputes `XYOFFSET` from `SCISSOR`, and adds `8` (half a pixel in 12.4) when its field argument is non-zero |
| `0x36a470` | `sceGsSetDefDBuff`. One caller, `0x10d2a4`, with `psm=0, w=512, h=224` |
| `0x483480` | the DBuff struct: display envs at `+0` / `+0x28`, draw envs at `+0x60` / `+0x1d0` (`+0xe0` / `+0x250` for context 2) |
| `0x4839b4` | buffer index, toggled by the `xori a1,a1,1` at `0x10b118`; `sceGsPutDispEnv` is called with `0x483480 + 40*index` |
| `0x4839c0` | the game's copy of **`CSR.FIELD`**, read out of `0x12001000` bit 13 at `0x10e6e0`–`0x10e6fc` every vsync |
| `0x10b1b0`, `0x10bd4c` | the two calls to the half-offset helper, one per buffer, each passing `!CSR.FIELD` |

libgraph's `sceGsSetDefDispEnv` is the stock one, with the constants this repo has met
before:

```
NTSC, interlaced      DY = dy + 50   DH = ffmd ? 2h−1 : h−1
NTSC, non-interlaced  DY = dy + 25   DH = h−1
SMODE2 = (inter == 0) ? 2 : (ffmd ? 3 : 1)
```

## The measurement

Read live over PINE, and it agreed with the static read on every field:

```
disp env  : SMODE2=3  -> INT=1, FFMD=1        (interlaced, FRAME mode)
            DISPLAY DX=636 DY=50 MAGH=4 MAGV=0 DW=2559 DH=447
            DISPFB   FBP=0 / FBP=56, FBW=8, PSM=0     (512x224 PSMCT32, two buffers)
draw envs : SCISSOR 0..511 x 0..223, OFX=28672 (1792.0 px) for all four
            OFY = 30984 (1936.5 px) on buffer 0
            OFY = 30976 (1936.0 px) on buffer 1
```

`512×224` with `FFMD=1` says the game is 240p content sent as 480i — each field carries all
224 lines, line-doubled by the CRTC to fill 448. That alone would be a picture with nothing
wrong with it. The two `OFY` values are what make it a field renderer: **exactly 8 apart,
which is half a pixel in 12.4 fixed point**, the same signature the
[Mega Man X7 job](devlog-SLUS-20487-mega-man-x7-no-interlacing.md) recorded. The game draws
the scene twice per two frames from two origins half a scanline apart, so that on a CRT the
fields interleave into roughly 448 lines.

It reaches the screen intact. Six captures of a static menu at 2× internal resolution, with
deinterlacing off:

| | |
|---|---|
| Distinct images among 6 captures | **2** |
| MSE between the two states | 499.68 |
| Best alignment | frame A shifted **+2 rows** matches frame B, MSE 0.054 |

Two output rows at 2× is one display line, which is half a line of the 224-line buffer —
the `OFY` difference, measured at the far end of the pipe. Nothing else about the two states
differs. That is the whole artefact: the entire picture hops half a scanline, 60 times a
second, in every scene.

## The one word

**`0x369294`: `sra s1, a1, 16` → `daddu s1, zero, zero`** (`00058c03` → `0000882d`).

`s1` is `sceGsResetGraph`'s sign-extended `inter` argument and nothing else; it is stored to
`GParam+0` and passed to `SetGsCrt`. Forcing it to zero makes both call sites ask for
`(mode 0, non-interlaced, NTSC, FRAME)` instead of `(0, interlaced, NTSC, FRAME)`, and three
separate things fall out of that:

- **`SMODE2` goes 3 → 2.** `INT=0, FFMD=1` — the same value libgraph's own non-interlace
  branch produces. PCSX2 sees a progressive frame and stops deinterlacing.
- **`DISPLAY` goes `DH=447, DY=50` → `DH=223, DY=25`.** Not hand-computed: `sceGsSetDefDispEnv`
  reads `GParam` and takes its non-interlaced NTSC path, which is where `h−1` and `dy+25`
  live. `DY` counts half-lines while `INT=1` and whole scanlines once it clears, so halving
  it is exactly right — and it comes out of the library rather than out of arithmetic done
  here, which is the reason this patch has no second `patch=` line.
- **The half-scanline field offset stops being applied.** The game asks
  `0x36a120` for the offset once per buffer, passing `!CSR.FIELD`; with a non-interlaced
  display PCSX2 stops toggling `CSR.FIELD`, both calls get 0, and the `daddiu v0,v0,8` at
  `0x36a18c` is never taken. All four draw environments settle on `OFY = 1936.0`.

`a1` is dead after the patched instruction (`0x369344` reloads it), the `ffmd` argument in
`s3` is untouched — deliberately, since `FFMD=0` would make `DH` mean something else — and
`mode` is 0 at both call sites, so only the `0x3692d4` path runs.

## Verification

Boot-to-boot, patch on versus patch absent. No savestate is involved on either side: the
display env is built once during init and never rebuilt, so a state saved under the patch
carries the patched CRTC and cannot serve as a baseline — the trap the
[GitS SAC job](devlog-SLUS-21006-gits-sac-no-interlacing.md) documented, in a form that a
write-the-original-word-back group cannot rescue.

| Check | Stock | Patched |
|---|---|---|
| Capture size at 2× | 1024×896 | **1024×448** |
| Distinct images among 6 captures, static scene | 2, MSE 499.68 apart | **1 — all six byte-identical** |
| `SMODE2` | 3 | 2 |
| `DISPLAY` | `DH=447 DY=50` | `DH=223 DY=25` |
| draw `OFY`, all four envs | 1936.5 / 1936.0 | **1936.0 throughout** |
| Buffer flip | alternates | alternates (≈60 toggles/s) |
| Frame rate | 60 | 59–60 |

**Screen Offsets** (`pcrtc_offsets`), the setting that exposes a `DH` patched without its
`DY`: the dialog's bounding box sits at rows 286..607 stock and 142..303 patched in the same
1280×896 raster. Mapping stock into patched geometry with `y_p = (y_s − 100)/2 + 50` aligns
at **+1 px out of a ±6 sweep** (MSE 41.6, versus 127 at 0 and 362 at +4) — half a display
line, which is the interlaced raster's own half-line. The picture sits where it always sat;
there is no band above or below it.

Also checked: gameplay renders correctly at 4× (HUD, minimap, combo meter, geometry all in
place) at 59–60 fps, the buffer flip still toggles once per frame, and the display env is
identical during menus, gameplay and the attract movie — the mode is set once at init and
nothing switches it later.

## What it costs

Vertical resolution, honestly stated. The two fields are *not* two halves of a 448-line
image; each is a complete 224-line render, one scanline-pair-phase apart and 1/60 s apart in
time. A CRT resolves them as something close to 448 lines. A progressive frame is the 224
lines the game actually draws — which is also all any deinterlacer ever had to work with per
field. The trade is a genuinely still picture for a picture with more apparent vertical
detail and a permanent half-line shake.

## Deliberately left alone

- **`[Widescreen 16:9]`.** PCSX2 already bundles ElHecht's for this exact serial+CRC, and
  loose files merge with the zip rather than shadowing it.
- **The soft-focus pass.** The game also runs a full-screen post-process — a copy of the
  frame blended back over itself four times — and it is removed by the `[Remove Blur]` group
  in the same file. See [that devlog](../deblur/devlog-SLUS-21343-samurai-champloo-remove-blur.md);
  it is a separate effect from anything here, and this patch does not touch it.

  Worth recording that an earlier revision of this file called that pass not worth patching,
  on the strength of a whole-frame mean-gradient that moved less than a percent. That was the
  wrong instrument — most of a frame is flat, and the two captures were of an animated scene
  a couple of frames apart. Counting draws in a GS dump, and asking the person looking at the
  screen, both said otherwise.

## Harness notes

- **`(word & 0xfc1f0000) == 0x24000000` pins `rt`, not `rs`.** That mask matches
  `addiu $zero, rs, imm` — nothing real — so every `li` scan built on it returns empty and
  reads as "the constant is computed, not immediate". To find `addiu rt, zero, imm`, mask op
  *and* `rs`: **`(word & 0xffe00000) == 0x24000000`** (`0x64000000` for `daddiu`). This is
  the second job in a row the wrong constant has cost time on; it is now written down
  correctly.
- **An absolute-address scan cannot see a store through a pointer.** Nothing in the image
  stores to the draw env's `XYOFFSET` at `0x483500` with a `lui`-resolvable base, yet a PINE
  write there was reverted in ~80 ms. The writer was `sd v0, 0x20(a0)` at the end of the
  half-offset helper, reached with `a0` already holding the env — invisible to the scan and
  found only by asking what libgraph function takes a field flag.
- **Pinning the data proved the data was not the source.** Spamming both of buffer 0's
  `XYOFFSET` copies at ~9.5k writes/s (against a 60 Hz writer) did not change the alternation
  at all, which ruled the DBuff envs out as the thing being drawn from and sent the hunt to
  the helper instead. A negative result from a hot-write is worth the five minutes.
- **Sample a per-frame toggle faster than the frame.** Reading the buffer index every 200 ms
  is every 12 frames — an even number — so a value that flips every frame reads as a
  constant, and "the patch broke double buffering" was a scary five minutes that a
  no-sleep loop (72 transitions in 1.2 s) closed.
- **`PostMessage` pad keys need the scan code in `lParam`.** `F8`/`F5`/`F1` hotkeys arrive
  fine with `lParam = 0`, but Qt resolves a *character* key through the scan code, so pad
  input posted with `lParam = 0` is silently dropped and the game looks frozen. Send
  `1 | (MapVirtualKey(vk, 0) << 16)`, plus bits 30/31 on the key-up.
