# Devlog: No-Interlacing for Ys V - Lost Kefin, Kingdom of Sand (SLPM-66360)

Trial-and-error record of how [`patches/SLPM-66360_09F7E99D.pnach`](../patches/SLPM-66360_09F7E99D.pnach) was made. No existing no-interlacing code existed for this game, so everything below came from reverse-engineering the boot ELF of the English 1.1 fan-translated ISO. Kept because the failures are more instructive than the final patch.

Target: PS2 remake by Taito (2006), boot ELF `SLPM_663.60`, ELF CRC `09F7E99D` (PCSX2 CRC = XOR of every little-endian u32 of the whole ELF file). Tested on PCSX2 2.8.0.

## How the game does video (map of the ELF)

All addresses are EE virtual addresses; the single loadable segment maps `file_offset = va - 0x100000 + 0x80`.

| Address | What it is |
|---|---|
| `0x100310` | `sceGsResetGraph(mode, interlace, omode, ffmd)` — shorts arrive sign-extended via `sll`+`sra` 16; writes GParam; tail-calls `SetGsCrt` (syscall 2 stub at `0x10f3a0`) |
| `0x274b90` | `sceGsGParam`: `+0` interlace, `+2` outmode, `+4` ffmd — the game's single source of truth for "am I interlaced" |
| `0x1005c8` | `sceGsSetDefDispEnv` — builds a display env from GParam: SMODE2 = `inter==0 ? 2 : (ffmd ? 3 : 1)`; DISPLAY DH = `2h-1` (interlaced FRAME) or `h-1` |
| `0x100940` | `sceGsPutDispEnv` — the **only** code in the entire image that writes the GS SMODE2 register (value taken from `env+8`) |
| `0x186f20` | Taito video-mode dispatcher (`sys_hig.c`): 6-entry jump table at `0x3615f0` (NTSC/PAL × progressive/FRAME/FIELD); always called with mode word `0x201` → **index 1 = NTSC interlaced FRAME** |
| `0x101198` | field-sync helper: if `GParam.interlace == 1` returns live CSR.FIELD (bit 13 of `0x12001000`), **otherwise returns a constant** |
| `0x1015e8` | `sceGsSetHalfOffset(drawenv, cx, cy, field)` — adds +8 (half pixel, 12.4 fixed) to XYOFFSET on odd fields; two callers: engine `0x18723c`, boot loader `0x135894` |
| `0x188928` | per-object render dispatch — receives the field parity and passes it to every registered render callback (this is how the world renderer learns the field) |
| `0x327b80/0x327ba8` | engine display envs (double-buffered, FBP `0`/`0x46`); flip by frame-counter parity at `0x187254` |
| `0x436680/0x4366a8` | boot-loader / movie-player display envs |

The game runs a 640×224 framebuffer in interlaced FRAME mode (SMODE2=3, DH=447), draws each field with an alternating half-line offset, and the movie player paces itself on CSR.FIELD.

## Attempt 1 — patch the `sceGsResetGraph` interlace argument (FAILED: hang)

The "obvious" patch: flip `interlace=1` → `0` at both `sceGsResetGraph` call sites (`0x1367E8` boot, `0x186F78` dispatcher, plus the three unused table entries). Everything downstream derives from GParam, so one patched argument gives SMODE2=2 and a correct progressive DISPLAY for free. Statically it verified end-to-end.

Result: **black screen forever, EE spinning at ~28% CPU.** The boot code waits for the odd field in loops like `do { v = f_101198(0) } while (v == 0)`. With `GParam.interlace == 0`, `0x101198` never reads CSR.FIELD and returns a constant 0 — infinite loop before the first frame.

**Lesson: this game must keep believing it is interlaced.** Any patch that changes GParam changes game *logic*, not just video output.

## Attempt 2 — patch the output constants instead (PROGRESS: boots, but half-height)

New strategy, standard for stubborn titles: leave every argument and GParam alone, and force progressive at the *output* level only:

- env-builder SMODE2 constants: `3 → 2` (`0x100694`) and `1 → 0` (`0x100698`)
- env-builder DH doubling `sll v0,s2,1` → `move v0,s2` … patched at `0x1007F0`
- `sceGsSetHalfOffset` field argument forced to 0 at both call sites (`0x187234`, `0x135898`)

Result: game boots (field waits still see real CSR.FIELD — empirically PCSX2 keeps toggling it even with SMODE2 INT=0), but the title screen renders in the **top half of a 448-line canvas**.

Debugging trick that cracked it: **PCSX2 savestates are zip files; `eeMemory.bin` inside is the raw 32MB EE RAM.** Reading the live display envs showed SMODE2=2 ✓ but DH still 447 ✗ — while the patched instruction was verified present in RAM.

## Attempt 3 — the byte-identical twin (FIXED half-height)

Root cause of attempt 2: the ELF contains **two** identical `sll v0,s2,1` (`00121040`) instructions in the env builder. `0x1007F0` is the **PAL** FRAME path's DH doubling; the NTSC FRAME one is at **`0x10073C`**. A byte-level "verify original value before patching" check passes at the wrong address when the wrong address is a twin. Moved the patch to `0x10073C` → full-frame, clean, progressive title screen (savestate-confirmed DH=223 everywhere).

**Lesson: never trust a pattern match alone — confirm which *branch* an instruction belongs to, and verify effects at runtime (savestate), not just bytes.**

## Attempt 4 — the world still bobs (FIXED: the real half-line source)

In-game, the background bobbed hard while dialogue textboxes stayed still. That asymmetry was the clue: the GS/display side was already stable (that's why UI was steady); the *renderer* was drawing the world shifted half a line on alternating fields.

Traced the field parity flow: main loop `0x151c9c` calls `0x101198` → `s3 = !CSR.FIELD` → flip handler `0x1871c0` → `0x188928` `move s2,a1` → passed as an argument to **every registered render-object callback**. The world/camera code applies a half-line shift from it; UI callbacks ignore it.

One instruction severs it for all consumers without touching the field-sync waits: `0x188940`: `move s2,a1` → `move s2,zero`.

Measured with rapid emulator screenshots (best-vertical-shift image diff between consecutive frames): before = alternating ±4 output rows (≈ half a source line at 224p upscaled), after = **exactly 0**.

## Deliberately left alone

- **Boot FMVs** (Taito/Falcom logos, intro PSS movies): the movie player alternates decoded field images by design, phase-machine driven (`*0x436500` cycles 2→1→0, keyed on the CSR field sample stored at `0x1357E0`). Forcing that field variable to 0 deadlocks the phase cycle → movie freeze. FMVs keep a slight inherent shimmer; menus/title/gameplay are fully progressive.
- **PAL paths**: unreachable (dispatcher only ever receives NTSC mode `0x201`), so the PAL DH twin stays unpatched.

## Verification methodology (reusable)

1. **Static**: capstone (MIPS64-LE) disassembly; exhaustive sweeps for syscall stubs, `jal`/`j`/pointer references, and every `lui 0x1200`-based GS privileged-register store. An adversarial multi-agent pass confirmed: exactly one SMODE2 write in the image, one bounds-checked mode table, two `sceGsSetHalfOffset` callers, no other writers of GParam.
2. **Runtime state**: F1 savestate → unzip → parse `eeMemory.bin` for env structs, GParam, and patched instruction bytes in RAM.
3. **Motion**: 4 rapid F8 (built-in GS screenshots) → per-pair vertical cross-correlation to quantify bobbing objectively.
4. **A/B**: always boot once unpatched to the same point before blaming (or crediting) the patch.

## Final patch summary

| Patch | Purpose |
|---|---|
| `00100694: 24020003→24020002` | env SMODE2, interlaced FRAME → progressive |
| `00100698: 24020001→24020000` | env SMODE2, interlaced FIELD → progressive (safety) |
| `0010073C: 00121040→02401021` | NTSC FRAME DISPLAY: DH = h−1 (not the `0x1007F0` PAL twin!) |
| `00187234: 00073C03→0000382D` | engine: `sceGsSetHalfOffset` field arg = 0 |
| `00135898: 00073C3F→0000382D` | boot loader: same |
| `00188940: 00A0902D→0000902D` | render dispatch: field parity = 0 for all callbacks (kills world bobbing) |

Plus `gsinterlacemode=1` so PCSX2 stops deinterlacing an image that is already progressive.
