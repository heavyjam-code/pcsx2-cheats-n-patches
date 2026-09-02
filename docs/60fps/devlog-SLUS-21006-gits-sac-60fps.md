# Note: 60 FPS for Ghost in the Shell: Stand Alone Complex (SLUS-21006)

**There is no patch file in this repo for this one, deliberately.** PCSX2 already
bundles a working `[60 FPS]` group for this exact serial+CRC, and a loose file cannot
improve on it — PCSX2 merges the bundled and loose entries and de-duplicates by group
name, so a second `[60 FPS]` would simply be skipped. This note records what the
bundled patch actually does and the measurement that says it is safe to enable, which
is the part its one-line description does not cover.

The bundled `SLUS-21006_95CC86EF.pnach` (author `asasega`) is:

```
patch=1,EE,20392f7C,extended,00000001    // stock value 00000002
```

An `extended` code whose leading `2` selects a 32-bit write, so it is
`patch=1,EE,00392f7c,word,00000001` written every vsync.

## What the address is

`0x392f38` is the frame-pacing object, and `0x392f7c` is its `+0x44` field. The whole
mechanism is in the VBlank handler at `0x19c000`:

| Field | Meaning |
|---|---|
| `+0x00` | field counter, ++ every vsync |
| `+0x04` | frame counter, ++ only when a frame is actually presented |
| `+0x14` | fields the current frame is allowed to take |
| `+0x18` | fields the current frame has taken so far |
| `+0x34` | **fields the frame actually took**, snapshotted at present time |
| `+0x44` | the configured divider — reloaded into `+0x14` on every present |

```
+0x18 += 1 ; +0x00 += 1
if (+0x18 < +0x14) return                 // not this field
... present ...
+0x04 += 1 ; +0x34 = +0x18 ; +0x14 = +0x44 ; +0x18 = 0
```

So `+0x44` is a pure presentation divider: 2 means "show a frame every second field".
`0x266fc8` writes 2 there during init, which is why the patch has to be `place=1` —
a `place=0` write would be consumed by that init store. There is exactly one other
writer, `0x19beec`, which sets 1 on a path the retail game does not take.

## The measurement

Read live over PINE, sampling the two counters against wall clock:

| | field counter `0x392f38` | frame counter `0x392f3c` |
|---|---|---|
| divider = 2 (stock) | 59.97 /s | **29.98 /s** |
| divider = 1 (patch) | 59.64 /s | **59.64 /s** |

It reaches and holds 60 on a Radeon 880M at 2× internal resolution, so the "might need
EE Overclock" hedge in the bundled description did not bite here.

## Game speed is not affected

This is the question worth answering, because a presentation unlock that also doubles
the simulation rate is a common failure and the bundled description does not say
either way. The handler snapshotting `+0x34` — how many fields the frame really took —
is the structural hint that the engine is delta-timed off the field count rather than
off frames, and the walk test confirms it.

Method: load the same savestate, hold forward for a fixed wall-clock interval, capture
the end frame. Real time is pinned by the field counter, which is hardware-paced and
identical in both runs.

| Run | duration | fields | frames presented |
|---|---|---|---|
| A — divider 2 | 4.19 s | 251 | 126 |
| B — divider 1 | 4.20 s | 252 | 252 |
| C — divider 2, walked 0.61 s longer | 4.80 s | 289 | 145 |

| Comparison | MSE |
|---|---|
| A vs B — 30 fps vs 60 fps, same real time | **105** |
| A vs C — same fps, 0.61 s more walking | **974** |

Two thirds of a second of extra walking moves the picture roughly **nine times**
further than switching to 60 fps does, and the A/B residual is consistent with the
one-field difference in duration plus animation phase. Had the simulation doubled,
the 4.2 s run would have covered the ground of an 8.4 s one, which would dwarf the
0.61 s reference by an order of magnitude in the other direction. Phase correlation
puts the A-vs-B displacement at 0 px.

So: enable the bundled group, it does what it says. It also composes with
[the No-Interlacing patch](../deinterlace/devlog-SLUS-21006-gits-sac-no-interlacing.md)
— the two touch nothing in common, one being a vsync-handler divider and the other a
CRTC flag.
