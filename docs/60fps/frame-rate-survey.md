# Frame-rate survey: which games can take a 60 FPS group, and what it costs

Companion to [the No-Interlacing candidates doc](../deinterlace/no-interlacing-candidates.md).
That one asks "does this game shake?"; this one asks "what caps it at 30, and what breaks if
you lift the cap?"

Measured on PCSX2 2.8.1, 2x internal resolution, Radeon 880M. Every rate below is measured, not
inferred.

## How to measure a PS2 game's frame rate without a frame counter

Do not hunt for the game's own counter first - find it. Save a savestate, wait, save another,
and diff `eeMemory.bin` between them with [`tools/diff_savestates.py`](../../tools/diff_savestates.py):

```
python tools/diff_savestates.py "SLUS-21207 (F4715852).02.p2s" "SLUS-21207 (F4715852).03.p2s" --seconds 9.12
```

`--seconds` is the real gap between the two file writes. Leave it out and the script takes the
gap from the two files' modification times, which on 2.8.1 agreed with a game's own vblank
counter to 0.01 s over a 13.66 s pair. It needs numpy, and because PCSX2 2.x compresses the
members of a `.p2s` with Zstandard it also needs 7-Zip on `PATH` or the `pyzstd` package; the
script's docstring has the details.

The script histograms the per-word deltas. A 30 fps game with 60 Hz vblank produces **two
clusters in a 2:1 ratio** - the vblank counters and the game-logic counters - and the ratio *is*
the answer. Dragon Quest VIII over a 9.12 s gap: delta 546 on eight addresses (59.9/s) and delta
273 on five (29.9/s). A game that is already 60 fps produces one dominant cluster and almost
nothing at half it: Oni in gameplay gave **1092** addresses near 60/s against **2** near 30/s.

Two traps:

- **Measure in gameplay, not on a menu.** Oni's main menu is so static that the whole 32 MB image
  had only 40 increasing words and no 60/s cluster at all. The same scene in the training level
  gave 3292.
- **The savestate write is slow.** Two `F1` presses three seconds apart produced a real gap of
  **10.12 s**, not 3 s, because each save takes ~7 s to land. Time the gap around the actual file
  writes or every rate is wrong by 3x.

## Results

| Game | Serial | Presents | 60 FPS group |
|---|---|---|---|
| Samurai Western | `SLUS-21187` | **60** | not needed - already 60 |
| Oni | `SLUS-20064` | **60** | not needed - already 60 |
| Mortal Kombat: Shaolin Monks | `SLUS-21087` | **60** | not needed - already 60 |
| Red Dead Revolver | `SLUS-20500` | 30 | **ships upstream**, verified here |
| Dragon Quest VIII | `SLUS-21207` | 30 | lever found and proven; **doubles game speed** (confirmed twice) |
| Radiata Stories | `SLUS-21262` | 30 | lever not located |

### Already 60 fps

**Samurai Western** presents one field per frame at a vsync interval of 1, `ctx+0x14` reads 1 in
every sample, and the NTSC branch of its mode selector writes **60** into the engine's own FPS
constant at `002C8880` (against 50 on the PAL branch). There is no 30 to unlock.

**Oni** and **Shaolin Monks** were settled by the delta histogram: 1092-against-2 and
156-against-11 in favour of 60/s. Their game logic steps 60 times a second, so the render rate is
60 and there is nothing to patch.

### Red Dead Revolver - the shape a cheap one looks like

The shipped word is `201018AC: 24030002 -> 24030001`, an `li v1, 2 -> 1` feeding
`sw v1, -21620(v0)` - a vsync interval at `004FAB8C`. Measured on the engine's own buffer counter
at `0079FE40`: **30.0/s stock, 60.0/s patched, 30.0/s restored.**

Two things worth carrying forward. The game **rewrites that global every frame**, which is why the
shipped line is `place=1` and why a PINE write to the *variable* reverts within a second while a
write to the *instruction* sticks - if a hot write will not take, patch the code, not the data. And
the draw environments stay pinned at `OFY = 29184` throughout, so unlike Way of the Samurai 2 the
interval change does **not** switch field rendering on here.

### Dragon Quest VIII - the lever exists, and it is not shippable (confirmed twice)

The pacer is `wait_vblanks(start, count)` at `001604A0`: it loops on the vblank counter at
`003D26B0` (`gp-28864`, `$gp = 003D9770`) until `now - start >= count`. Its caller at `001450CC`
reads the count from **`config+0x20`**, where `config = *(obj+0x260)` - the same struct the video
mode table fills, live at **`003E4B00`** reading mode 2, `512x448`, `+0x1C=1`, `+0x20=2`,
`+0x24=0`, `+0x28=262`. Writing **1** there gives **exactly 60.0 fps**, reversibly, with vblanks
unchanged at 60. The engine keeps a copy at `003E4CB0` that it refreshes from the config every
frame, so only the config word matters; the static initialiser at `001468A4` is rewritten later
in boot, so a shipped line would have to be `place=1`. Note that unticking such a patch does not
restore 30 fps: nothing ever writes the 2 back until the video mode is re-initialised.

**And the world runs at exactly double speed.** First shown on the attract flyover (the interval-1
frame at 2 s matches the interval-2 frame at 4 s), then wrongly retracted for a day, then confirmed
in the field the way it should have been done the first time: sampling all of static memory and
the active heap at 30-50 Hz with the lever on and again with it off, and comparing the period of
every cycling value and the rate of every counter. **813 of 869 comparable words run at exactly
twice the rate at interval 1** - the hero's idle cycle goes from 1.68 s to 0.84 s, the grass sway
block at `003F6860` halves its period, every bone matrix in `00B30000`-`00C10000` oscillates twice
as fast - and the 12 that hold their rate are vblank counters. The player confirmed it on screen:
animations, grass and water all at double speed.

What misled the retraction, so nobody repeats it: the hero's **translation** is time-correct at
interval 1 - 47.9 units/s against 47.5, sampled on the position vector at `0040F3E0` - because
the player module scales its step by `interval / 2` (`001847F8`), and the frame function does
compute a measured frame delta at `sys+0xF00` (`003E5790`, 2.0 stock, 1.0 at interval 1) that
is handed to one entity scheduler (`00176CD0`). Those two facts, plus a handful of
`interval == 1` branches (`00168960` returns 1.0 for 2 and 0.5 otherwise; `00229B58`,
`002D7F48`, `0036CF78`), looked like an engine designed for interval 1. They are islands. A
savestate diff cannot see a periodic clock - a walk that ends after a whole number of animation
cycles produces the same end frame at either rate, which is exactly what happened - so the
"no per-frame steppers" verdict from snapshot diffs was worthless, and the live period
comparison is the test that should have been run before anything shipped.

The fix would be the Way of the Samurai 2 job at Dragon Quest scale: the motion player's frame
advance, the texture and vertex animators (grass, water), the particle systems, the NPC and event
timers, the camera, battle timing, each found and halved - or the whole engine made to consume
the frame delta it already computes. Not started.

### Radiata Stories - unfinished

30 fps confirmed: over a 10.12 s gap in-game, **14** heap counters at 29.9/s against **4** system
counters at 59.9/s (`0018A0C8`, `0018EA7C`, `0018EAFC`, `0018ECC0`, all in the boot ELF's `.bss`).
The lever was not found. Progress for whoever picks it up: the vblank-start handler is registered
at `0012D3E4` (`AddIntcHandler(cause=2, handler=0012D150)`) and the vblank-end handler at
`00131630` (cause 3, `001313B0`); `0012D150` calls `0012D4C0` with `0019EA80` and then `0012CBD0`,
and the counter increment is in one of those. Note `$gp = 001862F0` and that only `0018A0C8` is
gp-reachable, so the others are all base-register accesses - resolve the base, never match on the
displacement alone.

A practical obstacle worth recording: **Radiata cannot be driven past its first-boot Screen menu
with `PostMessage` key input**, and its Triangle+Cross progressive toggle does not register that way
either, however long the two key-downs are held. Both need a human on the pad.
