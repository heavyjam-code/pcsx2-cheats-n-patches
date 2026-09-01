# Devlog: 60 FPS for Ys VI - The Ark of Napishtim (SLUS-20980)

Record of how the `[60 FPS]` group in
[`patches/SLUS-20980_EF9E43EF.pnach`](../patches/SLUS-20980_EF9E43EF.pnach) was made. The
[No-Interlacing group in the same file](devlog-SLUS-20980-ys-vi-no-interlacing.md) is a
separate piece of work and shares nothing with this one but the ELF.

Target: Falcom/Konami (2005), NTSC-U retail, boot ELF `SLUS_209.80` (1,753,008 bytes),
ELF CRC **`EF9E43EF`**. Compiler string `MW MIPS C Compiler (2.4.1.01)`, libgraph 2.7.0.
PCSX2 2.8.1 bundles `[Widescreen 16:9]` and `[Fix Analog Deadspot]` for this serial+CRC and
nothing frame-rate related, so a loose file adding `[60 FPS]` merges cleanly.

The whole patch is one word. The work was in proving that it is safe, and the proof is more
interesting than the address: **this game does not need to be made frame-rate independent,
because it already is.** The 30 fps cap is a presentation divider bolted onto an engine that
simulates at 60 Hz and throws half its frames away.

## The port kept its PC skeleton

The first hint is in the strings. `bin\data\YS6_WIN.INI` at `0x2907F0` is followed by the
Windows build's whole config-key table — `BackBufferWidth`, `RefreshRate`, `WaitVSync`,
`TripleBuffer`, `ClampInternalFrameRateMin` / `Max`, `ShowFPS`. The PS2 build still parses
them (`0x00129DE0` and `0x00129DF4` for the two clamps) and still carries the PC engine's
variable-frame-rate machinery. It also carries the debug FPS readout: `fps:%d` at
`0x002910F8`, formatted at `0x00130CA0` from a counter at `0x002DFD58`.

Two of those defaults are the key to the whole thing. `ClampInternalFrameRateMin` defaults
to 5 and `Max` to 10000, and the engine's two delta clamps sit in initialised `.data` as
`0x0026A1D0 = 12.0f` and `0x0026A1D8 = 0.006f` — which are exactly `60/5` and `60/10000`.
**The engine's unit of time is one 1/60 s tick.**

## Map of the frame chain

EE virtual addresses; the single loadable segment maps `file_offset = va - 0x100000 + 0x80`.

| Address | What it is |
|---|---|
| `0x002E09C4` | the tick counter, incremented at `0x0021F564` |
| `0x0021F540` | the VBLANK_START INTC handler: `tick++`, wake the display thread, `sync`, `ei`. **Ungated** — it runs 59.94 times a second no matter what |
| `0x0021F5F0` | the display thread body. Computes `base = (*(s16*)0x2E0A06 == 2) ? 60 : 50`, clamps `*0x2E0A50` down to `base`, then `divisor = (int)(base / *0x2E0A50)` and **`if (tick % divisor != 0) goto 0x0021F730`** — skipping the entire frame |
| `0x002E0A50` | **the target frame rate.** Four writers, no more |
| `0x00217624` | `addiu v1,zero,0x1e` — the 30 in the NTSC arm of `0x00217618`, stored to `0x002E0A50` at `0x00217630`. `0x00217628` is the PAL twin (25) |
| `0x002174D8` | hardwires `*(s16*)0x2E0A06 = 2`; it is the only writer, so the PAL arm is unreachable in this build |
| `0x002244A4` | the movie player setting `*0x2E0A50` to 60 (NTSC) for the duration of an FMV, having saved the old value to `0x002E5CC0` at `0x0022448C`; `0x00224674` restores it |
| `0x00129640` | the main loop: consume one posted frame from `0x002E09C8`, clamp the backlog to 2, bump `0x002E09C0`, call the frame function `0x0012A9C0` |
| `0x0020A110` | per frame: `dt = tick - prev`, written to `0x0026A1C0` and `0x0026A1C8`, clamped to `[0.006, 12.0]` |
| `0x0020A070` | the **sub-step pump**: hands out `min(remaining, 1.0)` and decrements the budget, returns 0 when spent |
| `0x0012AE80` / `0x0012B198` | `while (pump()) { logic(); }` — the sub-step loop |
| `0x0026A1C0` | the frame delta the game actually reads, ~150 sites |

`0x002E0A50` is the entire cap. `0x00217624` is where the 30 comes from.

## Why this cannot make the game run fast

The obvious worry with any 60 fps patch is that the game runs at double speed. Here it is
not merely unlikely, it is structurally impossible, and the reason is `0x0020A070`:

```
0020a074  lwc1 f2, -0x5e38(at)   ; f2 = remaining budget (0x0026A1C8)
0020a080  c.eq.s f0, f2          ; spent?
0020a090  beqz v0, 0x20a0a0      ;   ...and we already ran a step -> return 0
0020a0b4  c.ole.s f2, f1         ; remaining <= 1.0 ?
0020a0cc  swc1 f2, -0x5e40(at)   ;   yes: delta = remaining, budget = 0
0020a0e4  swc1 f1, -0x5e40(at)   ;   no:  delta = 1.0, budget -= 1.0
```

The budget is `tick - prev_tick`, and `tick` comes from the **ungated** vblank handler. So
the number of simulation steps per wall-clock second is 60, always, whatever the divider is
set to. At 30 fps the loop runs twice per presented frame with `delta = 1.0` each time; at
60 fps it runs once. Every one of the ~150 consumers of `0x0026A1C0` sees the identical
value `1.0` in both cases.

The same holds one level down. The engine's own logic-tick gate at `0x0012AE90` is

```
0012aea0  sb   zero, -0x7d40(gp)     ; flag = 0
0012aea8  lwc1 f0, -0x5e40(at)       ; delta
0012aeb4  add.s f0, f2, f0           ; acc += delta
0012aeb8  c.olt.s f0, f1             ; acc < 1.0 ?
0012aed0  sb   v0, -0x7d40(gp)       ;   no: flag = 1, acc -= 1.0
```

and since `delta` is pinned to `1.0` per sub-step, the flag fires on **every** sub-step —
60 times a second at any presentation rate. Everything called from inside that loop
(`0x0012B140`-`0x0012B17C`: the module updates, the script VM, the message system) is
therefore already running at 60 Hz in the shipped game. The patch does not speed those up;
it stops discarding the frames they were computed for.

Live readback confirms the arithmetic rather than assuming it. Unpatched, in gameplay:

```
target@2E0A50 = 30    tick delta = 4    delta@26A1C0 = 1.0    fps counter = 30
```

and with 60:

```
target@2E0A50 = 60    tick delta = 1    delta@26A1C0 = 1.0    fps counter = 60
```

`delta` is `1.0` in both. That is the whole argument in one line of output.

## The measurement

Two cold boots of PCSX2 2.8.1 and one savestate of the same scene (Rehda, the Olha /
Chief Ord dialogue), emulator pinned at 100% in every run — `ticks/s = 60.00` measured off
`0x002E09C4` each time, so nothing below is a speed-percentage artefact.

Presented frames counted from `0x002E09C0`, which the main loop bumps once per iteration:

| Run | `*0x2E0A50` | ticks/s | presented frames/s | tick delta |
|---|---|---|---|---|
| stock | 30 | 60.00 | **15.00** | 4 |
| stock, repeat | 30 | 60.00 | 14.83 | 4 |
| patched | 60 | 60.00 | **60.00** | 1 |
| 100 s soak, patched, scripted input | 60 | 59.91 | 59.10 | 1 (99.8% of samples) |

The stock 15 is not a typo and not a slow host — the same host holds a flat 60.00 with the
patch, which is strictly more drawing. It is the divider aliasing against itself: with
`divisor = 2` the display thread will only start a frame on an even tick, so a frame that
overruns 33 ms does not cost 1 tick, it costs 2, which buys the next frame a 4-tick budget
and four sub-steps of logic, which makes it overrun again. Sweeping the target confirms the
shape — 30 settles at a tick delta of 4 and sometimes 12 (the `12.0f` clamp), 20 and 15
oscillate, and only 60 is stable, because with `divisor = 1` every tick is a legal start and
a late frame loses exactly one.

So on this setup the patch is not worth 2x. It is worth 4x, and most of that is removing the
quantisation rather than raising the ceiling. How much of the stock 15 is this host and how
much is the PS2 is not something a PCSX2 session can answer; the mechanism is the game's
either way.

## Proving the speed is unchanged

The arithmetic above says game speed cannot change. The pixels say so too.

From the same savestate, run for exactly 5.00 s of wall clock with no input, then screenshot:

| Pair | mean abs difference | pixels differing by >8 |
|---|---|---|
| stock vs stock (repeat) | **0.0000** | 0.000% |
| stock vs patched | 0.0436 | 0.134% |

Two independent stock runs are byte-identical, which is what makes the method worth
anything. Against that zero baseline the patched run differs in 0.134% of pixels, all of it
inside one character's idle animation — the sub-step phase the frame happened to land on.
Same pose, same position, same candle.

With input it holds up under a harder test. Same savestate, same wall-clock input script
(advance four dialogue lines, walk right 3 s, attack, walk left 2 s):

| Pair | pixels differing by >8 |
|---|---|
| stock vs stock (repeat) | 0.149% |
| stock vs patched | **0.183%** |

Stock-versus-stock is not zero here because the input is delivered on wall-clock timers, so
two stock runs already disagree slightly. Stock-versus-patched sits at the same noise floor.
Both runs end on the same dialogue line, with the party in the same place.

Text reveal was checked separately, because a static pass had flagged the message system as
frame-counted. Capturing mid-reveal at matched wall-clock offsets:

| delay after keypress | stock text pixels | patched text pixels | ratio |
|---|---|---|---|
| 0.03 s | 22453 | 23925 | 1.07 |
| 0.05 s | 23348 | 25457 | 1.09 |
| 0.07 s | 23925 | 26220 | 1.10 |
| 0.09 s | 25457 | 26836 | 1.05 |
| 0.12 s | 25457 | 27221 | 1.07 |
| 0.15 s | 27221 | 27221 | 1.00 |

A doubled reveal rate would show the patched column complete while stock sat near half. A
flat 5-10% that converges to 1.00 the moment both finish is one 15 fps frame of presentation
lag, which is exactly what a 15-versus-60 comparison should show. The reveal is not doubled
— consistent with it living inside the sub-step loop.

## The interlacing question, which turned out to be a non-question

The game runs INTERLACE + FIELD (`0x002E0A04` is hardwired to 7 at `0x002174FC`). At 30 fps
each rendered image is scanned out as two fields; at 60 fps the front buffer changes every
field, so the signal a PS2 would put on the wire becomes genuine 60i, and a deinterlacer
weaving two fields of *different* images would comb. That is a real concern on hardware and
worth checking, because this repo ships `[No-Interlacing]` in the same file and the answer
decides whether the two groups need each other.

Measured with `[No-Interlacing]` deliberately **off** (the group stripped from the installed
file, since PCSX2's global auto-enable otherwise turns it on by name) and the deinterlacer at
its Automatic default, capturing mid-walk and scoring line-alternation energy
`mean|row[i] - (row[i-1]+row[i+1])/2|` at three granularities:

| Run | comb, screen rows | comb, PS2 scanlines | even vs. odd scanlines |
|---|---|---|---|
| target 30 | 0.4422 | 0.9727 | 2.3203 |
| target 60 | 0.4424 | 0.9727 | 2.3204 |

Identical. PCSX2 presents the whole 448-line buffer rather than reconstructing a field pair,
so raising the flip rate does not introduce combing under emulation. The two groups are
independent; pair them if you want, but `[60 FPS]` does not need `[No-Interlacing]` to look
right.

(The two captures also came out 99.97% pixel-identical, which is one more accidental control
on the speed question.)

## `place` matters here, and it is not the usual choice

The first build used `patch=1` (every frame, at vsync), which is what the other patches in
this repo use. It read back correctly and did nothing:

```
word@0x217624   = 2403003C     <- patched
target@0x2E0A50 = 30           <- unpatched
```

`0x00217624` executes once, about a millisecond of emulated time after the ELF entry point,
and nothing rewrites `0x002E0A50` afterwards. A vsync-time write lands after `0x00217630`
has already stored the 30. `patch=0` applies at the entry point, before any game code, and
then it works:

```
word@0x217624   = 2403003C
target@0x2E0A50 = 60
```

*Lesson: `place=1` is the right default for an instruction the game re-executes every frame,
and the wrong one for a constant that is read once during init. Read back the value the patch
is supposed to produce, not just the word the patch wrote.*

## What was considered and rejected

- **`patch=1,EE,002E0A50,word,0000003C`** — force the global directly. It has to be place=1
  because the address is BSS, so it rewrites the word every vsync forever, and it asserts a
  value instead of configuring the source. It also stamps on the movie player's temporary
  override rather than letting the save/restore at `0x0022448C`/`0x00224674` work.
- **Nop the modulo branch at `0x0021F6AC`.** Deletes the throttle but leaves `0x002E0A50`
  reading 30, so anything that consults the nominal rate is left lying to.
- **The PAL constant at `0x00217628`.** Unreachable: `0x002E0A06` has exactly one writer
  (`0x002174D8`) and it stores 2.
- **The clamp at `0x0021F620`.** 60 is the clamp boundary on NTSC, not past it, so the value
  survives untouched and the divisor is exactly 1. No divide-by-zero is reachable — the
  clamp guarantees `1 <= rate <= base`.

## Deliberately left alone

- **The movie player.** It already drives this exact mechanism at 60 and is the best evidence
  the rest of the engine tolerates it. With the patch its save/restore becomes a no-op
  (saves 60, sets 60, restores 60), which is strictly safer than today, where a missed
  restore would strand the game at 60.
- **The delta quantizer** at `0x0020A1D8` (`0x002DFD20`). It has exactly one access in the
  whole image — that load — and lives in BSS, so it is `0.0f` forever and the quantization
  block is dead code. Measured `0.0000` live, and left alone.
- **The frameskip path** at `0x0020A24C`. It triggers when a frame's delta exceeds `12.0`,
  which becomes *less* reachable at 60 fps, not more.

## Verification

1. **Static**: per-instruction capstone MIPS64-LE decode (R5900 `lq`/`sq`/MMI decoded by
   hand); whole-image `jal`/`j` xref map; `lui`-base-resolved scans for every access to
   `0x002E0A50`, `0x002E09C4`, `0x0026A1C0` and the timing globals, checked against
   `$gp`-relative writers as well as absolute ones.
2. **A six-way blind static pass** over the same ELF — display mechanism, delta pipeline,
   two halves of a fixed-step hunt, movie/audio/IO, and an independent search for other caps
   — each report then handed to a separate reviewer told to refute it. It independently
   derived the same map, the same single gate and the same patch word, and it is where the
   `place=1` defect was caught before it shipped. It also produced the one claim the live
   measurement overturned: that the message system would print at double speed.
3. **Live state via PINE**: `0x002E0A50`, `0x002E09C4`, `0x002E09C0`, `0x0026A1C0`,
   `0x0026A1C8`, `0x002DFD20`, `0x002DFD48` and the patched word read back every run, on a
   cold boot and from a savestate, in gameplay and during an FMV.
4. **A/B from an identical savestate** with wall-clock-matched durations and a scripted input
   sequence, scored on pixels, with a stock-versus-stock control in every batch.
5. **A 100-second soak** at 60 fps with continuous scripted input: 59.10 presented frames/s,
   no hang, no PINE error, tick delta 1 in 99.8% of 1.18M samples.

## The patch

| Patch | Purpose |
|---|---|
| `00217624: 2403001E → 2403003C` | the NTSC arm of the video-mode init loads 60 instead of 30 into the target frame rate at `0x002E0A50`, so the display thread's `tick % divisor` gate opens on every vblank instead of every second one |

`place=0`, because the instruction runs once during init and never again.
