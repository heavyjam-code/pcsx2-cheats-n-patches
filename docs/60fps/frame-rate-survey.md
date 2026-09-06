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

Then histogram the per-word deltas. A 30 fps game with 60 Hz vblank produces **two clusters in
a 2:1 ratio** - the vblank counters and the game-logic counters - and the ratio *is* the
answer. Radiata Stories over a 10.12 s gap: four system counters at 59.9/s against fourteen
heap counters at 29.9/s. A game that is already 60 fps produces one dominant cluster and almost
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
