# Devlog: No-Interlacing for Mega Man X7, Ns Edition v1.5.2 (SLUS-20487)

Record of how [`patches/SLUS-20487_55AC9791.pnach`](../../patches/SLUS-20487_55AC9791.pnach) was made. The game was entry 5 on the [measured field-renderer list](no-interlacing-candidates.md#measured-field-renderers) — `512x448 -> 1024x447`, TIER-A, with a note that "a naive interlace flip is on record as failing". It is the second TIER-A job in this repo after [Ys V](devlog-SLPM-66360-ys-v-no-interlacing.md), and it went much faster because the Ys V recipe transferred almost verbatim: same Sony libgraph, same trap, same PAL twin. The interesting parts are the two places it *didn't* transfer.

Target: Capcom (2003), "Ns Edition v1.5.2" romhack ISO, boot ELF `SLUS_204.87` (3,553,328 bytes), ELF CRC **`55AC9791`**. Retail is `3EDA6DE7`, which ships only a `[Widescreen 16:9]` group upstream and no interlacing code — and cannot load here anyway, because the romhack changed the CRC. Tested on PCSX2 2.8.1.

## How the game does video (map of the ELF)

EE virtual addresses; the single loadable segment maps `file_offset = va - 0x100000 + 0x80`. No `.sndata`/`SNR1` symbol table, so this was ordinary code reading.

| Address | What it is |
|---|---|
| `0x105620` | `sceGsResetGraph(mode, interlace, omode, ffmd)` — writes GParam, tail-calls `SetGsCrt` (syscall 2 stub at `0x1205a0`). **Exactly two callers**: `0x2ee334` game init `(0,1,2,ffmd=1)`, `0x25af38` movie player `(0,1,2,ffmd=0)` |
| `0x400950` | `sceGsGParam`: `+0` interlace, `+2` outmode, `+4` ffmd, `+6` GS revision |
| `0x1057b0` | GParam getter — a two-instruction `lui`/`addiu` leaf |
| `0x1058d8` | `sceGsSetDefDispEnv(env, psm, w, h, dx, dy)` — SMODE2 at `0x1059ac` from `inter==0 ? 2 : (ffmd ? 3 : 1)`; DISPLAY at `env+0x18` |
| `0x105c50` | `sceGsPutDispEnv` — the **only** writer of GS SMODE2 (`0x12000020`), from `env+8`. Branches on GS revision at `0x105c6c`; rev is `0x1b` under PCSX2, so the SMODE2-writing path is the live one |
| `0x106968`, `0x106bd0` | two byte-identical copies of `sceGsSetHalfOffset(drawenv, cx, cy, field)`; the `+8` half-pixel add is `0x1069d4` / `0x106c3c`. **One caller each** |
| `0x1061b0` | `sceGsSyncV` — returns live CSR.FIELD (bit 13 of `0x12001000`) **only** when `GParam.interlace == 1`, else a constant |
| `0x2edf20` | per-frame: samples `0x1061b0`, stores the field parity to `gp-0x6944`, bumps a frame counter |
| `0x2edf80` | per-frame: picks a draw-env pair by `BUF_INDEX` (`gp-0x6948`) and calls `sceGsSetHalfOffset` twice with that parity |
| `0x2ee000` | display setup: `sceGsSetDefDispEnv` on both envs (w=`0x200`, h=`0xe0`), then `sceGsSetDefDBuff`. **One caller**, at boot |
| `0xE748A0`, `0xE748C8` | the two display envs |
| `0xE74900`/`0xE74980`, `0xE74A70`/`0xE74AF0` | the two draw-env pairs |
| `0x25b000`–`0x25b600` | movie player — builds its own display env on the stack, w=`0x200` h=`0x1c0` (512×448, full frame) |

The game renders **512×224** and displays it as 448 interlaced lines, drawing alternate fields with a half-line offset. The FMV player is a different animal: a genuine 512×448 full-frame buffer, which is why boot movies measure `2048x1792` under 4× upscale while gameplay does not.

## The measurement that made this cheap

Rather than diffing screenshots to guess the tier, PINE reads the draw envs directly. Two numbers settled it in one shot:

```
SCISSOR : scax1=511  scay1=223          -> a 512x224 draw buffer
XYOFFSET: buffer set 0  OFY = 30976
          buffer set 1  OFY = 30984      -> exactly 8 apart
```

8 in 12.4 fixed point is half a pixel. The two buffer sets are permanently half a line apart, and the game alternates between them every frame. That *is* the bob, read straight out of RAM — no image processing required. It also confirms the arithmetic: `sceGsSetHalfOffset(env, 0x800, 0x800, field)` with w=512,h=224 gives `OFX=(0x800-256)<<4=28672` and `OFY=(0x800-112)<<4=30976`, `+8` when field is set.

**Lesson worth reusing: for a field renderer, read XYOFFSET out of the draw envs before you screenshot anything.** It is unambiguous, it needs no static scene, and it tells you the fix worked the instant you hot-patch.

## What transferred from Ys V

**The CSR.FIELD trap, avoided by design.** `0x1061b0` returns real CSR.FIELD only while `GParam.interlace == 1`, and the movie player spins on it (`0x25b4e0`: `do { v = syncV(0) } while (v == 1)`). Zeroing the interlace argument would deadlock the boot exactly as it did on Ys V. So GParam was never touched — only output constants.

**The PAL twin.** `sll v0,s2,1` (`00121040`) — the `DH = 2h-1` doubling — occurs four times in the image. `0x105a4c` is the NTSC interlaced-FRAME path; **`0x105b00` is the byte-identical PAL one**. Same trap, same shape, one function over. Patched the NTSC one; the PAL path is unreachable (omode is always 2).

## What did *not* transfer

**Ys V needed a render-dispatch fix; this game does not.** The field parity global `gp-0x6944` has 8 readers. Six of them are not half-line offsets at all — they pick GS buffer/texture descriptors out of a 22-byte-stride table at `0x1118C10` for frame-capture blits and effect textures, and the selector reduces algebraically to `BUF_INDEX ^ 1` for either parity value. So the parity contributes nothing there. That is why the patch forces the **argument** at the two `sceGsSetHalfOffset` call sites instead of zeroing the global: it is the minimal cut that touches only XYOFFSET. An adversarial sweep confirmed the `daddiu v0,v0,8` pair is the only per-field Y term in the image — CSR.FIELD enters at exactly one instruction, and GS XYOFFSET_1/XYOFFSET_2 are each written at exactly one.

## Three things that nearly went wrong

**1. A scan matched on the offset and ignored the base.** Looking for direct writes to `env0.SMODE2` (`0xE748A8`), a scan for stores with immediate `0x48a8` produced a confident hit at `0x1e1368` — `sh v0, 0x48a8(at)`, storing a 7. It looked like the game overriding SMODE2 behind libgraph's back, which would have invalidated the whole approach. It was a false positive: `at` there comes from `lui at,0xe4`, so the target is `0xE448A8` — an unrelated struct. Re-running the scan with `lui`-base tracking showed **no direct writes to either env's SMODE2 anywhere in the image**. *Never match a gp/lui-relative access on the displacement alone; resolve the base first.*

**2. GParam said `ffmd=0` while the live env said FRAME mode.** Reading GParam in-game gives `interlace=1, omode=2, ffmd=0`, which by the env builder's own logic should yield `SMODE2=1` and `DH=h-1`. The live env instead held `SMODE2=3`, `DH=447`. The explanation is scheduling, not a bug: the game builds both envs **once**, at boot, while ffmd is still 1; the movie player then calls `sceGsResetGraph(...,ffmd=0)` for every FMV and never restores it. `0x2ee000` has exactly one caller, so the envs are never rebuilt — the boot-built copy is simply re-pushed to the GS every frame. This is why **both** SMODE2 constants are patched: `3 -> 2` is what the game's env actually uses, `1 -> 0` covers the movie player's own env.

**3. DH and DY are a matched pair, and the first attempt took only half of it.** `sceGsSetDefDispEnv`'s interlaced branch computes `DH = 2h-1` *and* `DY = dy + 0x32`; its progressive branch computes `DH = h-1` *and* `DY = dy + 0x19`. DY counts half-lines while INT=1 and real scanlines once INT=0, so the two constants have to move together. Patching DH alone produced a picture that was pixel-identical at PCSX2's defaults — and visibly wrong the moment **Screen Offsets** was enabled, sitting high in the frame with a black band below. Capcom's own read-back code states the convention outright: `0x38d6a0` does `(DY - 0x32) >> 1`, and that `>> 1` is only correct while interlaced.

Adding `0x105a14: 24420032 -> 24420019` fixes it. Verified to be free: with and without it, the rendered frames at default settings are **byte-identical** (same two frame hashes across a burst), while Screen Offsets renders correctly.

## Deliberately left alone

- **The game's in-game screen-position option.** DISPLAY is re-assembled by hand at eight later sites (in `0x37dc80`, `0x37e150`, `0x38eef0`, `0x397da0`) that hardcode `DX = x*4 + 0x27c` and `DY = y*2 + 0x32`. With a non-zero screen offset the vertical nudge therefore moves twice as far as it should. Fixing it properly means ~20 more instruction rewrites across the player-state module, all of them untestable without reaching those specific screens. Not worth it for an option most players never touch; the boot-built env — which is what everything else uses — is correct. Live monitoring through the attract demo showed DY holding at 25 with no re-assertion.
- **PAL paths**: unreachable, `omode` is always 2.

## Verification

1. **Static**: capstone (MIPS64-LE, per-instruction so R5900 `lq`/`sq`/MMI opcodes don't stall the stream), a whole-image `jal`/`j` xref map, and `lui`-base-resolved scans for every access to the display envs and GS privileged registers. An 8-agent adversarial pass re-derived the map independently and found the DH/DY pair.
2. **Live state via PINE**: every patch site read back from EE RAM and compared against the ELF before trusting any of it; GParam, both display envs and all four draw envs sampled per frame.
3. **A/B on a static screen**: the title screen captured at 4× internal resolution with deinterlacing set to None, patched and unpatched, from clean boots.

The controlled A/B, same screen both runs:

| | Unpatched | Patched |
|---|---|---|
| Output | 2048×1792 | 2048×896 |
| Draw-env OFY | 30976 / **30984** | 30976 / **30976** |
| Best frame-to-frame vertical shift | **±4 px** (MSE 813 at zero shift, **0.1** at 4 px) | **0 px**, one pair byte-identical |
| Vertical alignment vs unpatched | — | 0 lines |

±4 upscaled pixels at 4× is one output line at 448p — half a source line at 224p. Exactly the predicted artefact, and it goes to zero.

## Final patch summary

| Patch | Purpose |
|---|---|
| `001059A4: 24020003→24020002` | env SMODE2, interlaced FRAME → progressive (the branch the game takes) |
| `001059A8: 24020001→24020000` | env SMODE2, interlaced FIELD → progressive (the branch the movie player takes) |
| `00105A4C: 00121040→02401021` | NTSC FRAME DISPLAY: DH = h−1, not the `0x105B00` PAL twin |
| `00105A14: 24420032→24420019` | NTSC DISPLAY: DY base 50 → 25, the unit partner of DH |
| `002EDFB8: 938796BC→0000382D` | `sceGsSetHalfOffset` field argument = 0 (draw env A) |
| `002EDFE4: 938796BC→0000382D` | same (draw env B) |

Plus `gsinterlacemode=1` so PCSX2 stops deinterlacing an image that is already progressive.

## Harness notes

- **PCSX2 launched with `StartFullscreen = true` puts the main window in an iconic state.** With `ScreenshotSize = 0` ("Screen Resolution") the F8 screenshots then come out **1×1 pixels** — a silently useless capture that looks like a black frame. Set `ScreenshotSize = 2` (Internal, uncorrected) for any measurement work; it also makes the capture independent of window size and aspect correction.
- `PostMessage(WM_KEYDOWN/UP)` to the pcsx2-qt windows drives both hotkeys **and** pad input unfocused, which is what makes an unattended A/B possible.
- Screenshot writes are asynchronous and slow (2–3 MB PNGs, several seconds); the files stay locked well after the OSD says "Saved". Copy, don't move, and wait.
- The output *height* is a free tier check once the patch is on: 1792 → 896 is the display flipping from 448 interlaced lines to 224 progressive ones.
