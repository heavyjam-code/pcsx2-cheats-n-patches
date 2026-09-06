# Frame-rate survey: which games can take a 60 FPS group, and what it costs

Companion to [the No-Interlacing candidates doc](../deinterlace/no-interlacing-candidates.md).
That one asks "does this game shake?"; this one asks "what caps it at 30, and what breaks if
you lift the cap?"

Measured on PCSX2 2.8.1, 2x internal resolution, Radeon 880M. Every rate below is measured, not
inferred.

## How to measure a PS2 game's frame rate without a frame counter

Do not hunt for the game's own counter first - find it. Save a savestate, wait, save another,
and diff `eeMemory.bin` between them:

```
python tools/... (see docs; the working script diffs two .p2s files as numpy uint32 arrays)
```

Then histogram the per-word deltas. A 30 fps game with 60 Hz vblank produces **two clusters in a
2:1 ratio** - the vblank counters and the game-logic counters - and the ratio *is* the answer.
Dragon Quest VIII over a 9.12 s gap: delta 546 on eight addresses (59.9/s) and delta 273 on five
(29.9/s). A game that is already 60 fps produces one dominant cluster and almost nothing at half
it: Oni in gameplay gave **1092** addresses near 60/s against **2** near 30/s.

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
| Dragon Quest VIII | `SLUS-21207` | 30 | lever found and proven; **doubles game speed** |
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

### Dragon Quest VIII - the lever exists, and it is not shippable

The pacer is `wait_vblanks(start, count)` at `001604A0`: it loops on the vblank counter at
`003D26B0` (`gp-28864`, `$gp = 003D9770`) until `now - start >= count`. Its caller at `001450CC`
reads the count from **`config+0x20`**, where `config = *(obj+0x260)` - the same struct the video
mode table fills, live at **`003E4B00`** reading mode 2, `512x448`, `+0x1C=1`, `+0x20=2`,
`+0x24=0`, `+0x28=262`.

Writing **1** to `003E4B00+0x20` over PINE gives **exactly 60.0 fps**, reversibly:

| | vblanks | frames |
|---|---|---|
| stock | 59.7/s | 30.0/s |
| interval 1 | 59.7/s | **59.7/s** |
| restored | 60.0/s | 30.0/s |

**And the world runs at exactly double speed.** Counters doubling could be trivial, so this was settled with pixels: from one savestate at the attract flyover, captures at fixed wall-clock offsets after the load, at interval 2 and again at interval 1. The interval-1 frame at **2 s matches the interval-2 frame at 4 s** (MSE 19.9) and the one at **3 s matches 6 s** (MSE 19.7), against 320-430 for every other pairing - the scripted camera covers the same path in half the time. Every game-logic counter doubles with it too: Four heap counters sampled alongside - `0091D3FC`,
`0091D750`, `00A0398C`, `00A075CC` - go 30.0/s to 60.0/s while vblanks hold at 60, i.e. their rate
*per vblank* goes 0.502 to 1.004. That is a fixed-step engine stepping once per presented frame, so
60 fps is 2x game speed, exactly the Way of the Samurai 2 problem, and that patch needed forty words
and three play-tests to correct. Not attempted.

The lever itself is shippable in the Red Dead shape - `patch=1,EE,003E4B20,word,00000001` (and `003E4CB0` for the second
copy of the struct) holds 1 against the initialiser and gives 60.0 fps from boot; the obvious static initialiser at
`001468A4` (`li v0, 2` into `sw v0, 32(s0)`) does *not* stick at `place=0`, something else writes the 2 after it. But the
line is not shipped, because of the speed. There is no single time constant to halve: `1/30f` and `1/60f` are each used
nowhere in code, while `30.0f` appears at 27 code sites and `60.0f` at 49, scattered through subsystems. The main loop
(`001A0470`-`001A0F40`) passes no tick count into an update - the one constant-2 argument in its tail goes to a varargs
formatter at `0024D710`, not a stepper. So correcting the speed is the Way of the Samurai 2 job: find the animation clock,
the movement integrators and the frame-counted timers one subsystem at a time, forty words and a play-test cycle. Not
started.

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
