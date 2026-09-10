# Devlog: 60 FPS for Steambot Chronicles (SLUS-21344)

The [patch](../../patches/SLUS-21344_9F391882.pnach) unlocks 60 FPS and corrects
the measured on-foot distance, follower speeds, animation-rate setup, idle-gesture timing and
in-game clock. It remains
**experimental**: this is not a complete conversion of the simulation to 60 Hz.
See the [frame-rate survey](frame-rate-survey.md) for the comparison with other games.

Target: Irem, 2006; USA UNDUB disc, boot ELF `SLUS_213.44` from `SYSTEM.CNF`,
PCSX2 ELF CRC `9F391882`; PCSX2 2.8.1. The installed bundle and the
[upstream entry](https://raw.githubusercontent.com/PCSX2/pcsx2_patches/main/patches/SLUS-21344_9F391882.pnach)
provide `[Widescreen 16:9]`, with no bundled `[60 FPS]` group for this serial+CRC.
Testing used 2x internal resolution on a Radeon 880M with `EECycleRate = 0`.

The serial was read from the disc, not inferred from its title. XORing the ELF's
32-bit words gives `9F391882`; the extracted ELF's SHA-256 is
`FF1323A29507935CC81283D03C99F1395BBAB8FAF5E22622B12610634BC0B564`.
The UNDUB retains the CRC associated with the USA release. This record covers
that extracted executable; it does not establish compatibility with other mods.

## What the fifteen writes change

| Address | Original | Patched | Purpose |
|---|---|---|---|
| `005BC89C` | `00000002` | `00000001` | Live display interval: one field per frame |
| `0022B68C` | `3C034270` | `3C0341F0` | Animation-rate numerator: 60.0 to 30.0 |
| `004186E4` | `3D8F5C29` | `3D0F5C29` | Gait table A, walk: 0.070 to 0.035 |
| `004186E8` | `3E23D70A` | `3DA3D70A` | Gait table A, run: 0.160 to 0.080 |
| `004186F4` | `3D8F5C29` | `3D0F5C29` | Gait table B, walk: 0.070 to 0.035 |
| `004186F8` | `3DCCCCCE` | `3D4CCCCE` | Gait table B, run: approximately 0.100 to 0.050 |
| `00418704` | `3C2C0832` | `3BAC0832` | Gait table C, walk: approximately 0.0105 to 0.00525 |
| `00418708` | `3CC49BA6` | `3C449BA6` | Gait table C, run: 0.024 to 0.012 |
| `001118A4` | `2883003C` | `28830078` | Clock rollover comparison: 60 to 120 ticks |
| `001118C0` | `2404003C` | `24040078` | Clock remainder divisor: 60 to 120 ticks |
| `001DD970` | `28410097` | `2841012D` | Idle-gesture eligibility threshold: 151 to 301 updates |
| `001DDA18` | `2402012C` | `24020258` | Idle-gesture repeat divisor: 300 to 600 updates |
| `001DDA1C` | `2463FF6A` | `2463FED4` | Idle-gesture repeat offset: -150 to -300 updates |
| `001DED84` | `3C023D8F` | `3C023D0F` | Follower's inline walking speed: 0.070 to 0.035 |
| `001DEDEC` | `3C023E23` | `3C023DA3` | Follower's inline running speed: 0.160 to 0.080 |

The interval is a runtime field. Changing only the initialization argument at
`003D18C4` is insufficient when loading a state that already contains interval 2.
The shipped write maintains `005BC89C = 1`; it does not rely on initialization
running again. All fifteen writes use `place=1`.

This address belongs to the **static** display object at `005BC650`, field
`+024C`; it is not a guessed heap allocation. Initialization at `0022A064` and
`0022A06C` constructs that constant address and `0022A084` stores it into
`0055C5F0`. The VBlank handler increments object field `+023C` at
`002644EC..002644F4` and compares elapsed fields with the interval at `00264514`.

The native animation-rate setter at `0022B680` computes:

```text
track.rate = requested_rate * numerator / engine_rate
```

`0022B68C` supplies the numerator, originally 60.0; the denominator is the float
at `0055C3CC`, addressed relative to `$gp = 00564370`. With the denominator left
at its stock 30.0, the change makes a requested rate of 1 become 1 instead of 2.
It changes the existing setter rather than injecting a trampoline into a child
animation path. Tracks initialized before the patch may retain their old rate.

The on-foot input routine at `001E17A0` selects one of the three gait tables,
reads its walk/run entry, and multiplies it by actor field `+01E8` at
`001E1974..001E198C`. It then constructs the movement vector at `+0370`.
Halving all six table entries covers this path without repeatedly overwriting
one particular actor's live multiplier. It also avoids relying solely on the
separate movement branch around `001E0200`.

The clock routine at `00111890` increments `005617B8` once per update. At its
threshold it advances `005617B4`, with `005617B0` as the next higher component.
Both the threshold and modulo divisor must change together. At stock 30 FPS,
60 ticks take about two real seconds; at 60 FPS the replacement needs 120 ticks
to preserve that same clock speed.

## Measured comparison

PINE sampled the VBlank counter `005BC88C`, update/frame counter `0055C958`, live
interval, actor coordinates and clock against a monotonic wall clock. The actor
in this scene was at `00A29350`, with XYZ at `+10`, `+14`, `+18`. Samples were
requested about every 20 ms; the elapsed times below use the actual endpoints.

Both movement runs began at `(7.808764, -2.640480, -4.134764)` and received the
same sustained forward input through the game's own input reader. Full forward
selects running, so these are **run-distance tests**, not walk-speed tests.

| Run | Seconds | VBlanks, first to last | Frames, first to last | Frames/s | Horizontal displacement |
|---|---:|---|---|---:|---:|
| Stock | 3.014166 | 109740 to 109920 (+180) | 58129 to 58219 (+90) | 29.859 | 14.399980 |
| Candidate | 3.018107 | 108085 to 108266 (+181) | 57544 to 57725 (+181) | 59.971 | 14.400001 |

Horizontal displacement is `sqrt(delta_x^2 + delta_z^2)` in game units. The
stock delta was `(3.624203, 13.936448)` in XZ; the candidate was
`(3.625828, 13.936047)`. Their net horizontal distances differ by approximately
0.000021 units. The near-identical distance rules out doubled on-foot running
speed in this scene. It does not establish identical turning or vertical motion:
the Y deltas were -0.090085 and -0.072376 respectively.

The sampled animation-rate field `00A29880` was 2.0 throughout the stock trace
and 1.0 throughout the candidate trace. The phase comparison below goes beyond
that rate-setting check, while remaining limited to the observed clips.

The longer idle comparison measured the clock independently of movement:

| Run | Seconds | VBlanks, first to last | Frames, first to last | Clock, first to last | Clock advance |
|---|---:|---|---|---|---:|
| Stock | 12.011133 | 111253 to 111973 (+720) | 58885 to 59245 (+360) | 13:44 + 25/60 to 13:50 + 25/60 | 6 seconds |
| Candidate | 12.005662 | 108274 to 108994 (+720) | 57733 to 58453 (+720) | 13:19 + 13/120 to 13:25 + 13/120 | 6 seconds |

The clock advanced 0.499537 versus 0.499764 counter seconds per real second. The
residual is wall-clock sampling variation: both runs covered 720 VBlanks and
exactly six counter seconds. Here the displayed pairs are minutes:seconds;
`005617AC` is the next higher, hour component. This preserves the original
counter's rate rather than asserting that it tracks real time correctly.
Idle frame rates were 29.972 and 59.972 respectively.
These short measurements reached 60 FPS without EE overclock; they do not
establish the performance requirement for every area or a higher resolution.

## Character animation comparison

A second A/B pass recorded about 28 seconds per configuration, using the same
cleaned beach state: three seconds of scripted forward input, then stationary
observation. This pass tested the initial ten-write patch, before the idle-timer
correction below. It sampled Vanilla at `00A29350` and Connie at `00A288C0`.
Their animation parents are actor `+052C`: `00A2987C` and `00A28DEC`.

Parent fields are float phase `+00`, float rate `+04`, active state `+08`
(16 bits), clip pointer `+0C`, first child pointer `+14`, and repeat/completion
counter `+18` (16 bits). A clip contains start/end floats at `+10/+14`.
For stable zero-start loops, advance is `delta_phase + end * delta_cycles`.
The parent wraps only when phase exceeds the end, subtracting the end at
`0022BAD4`; a duration-30 clip therefore wraps from 30 to 2 at stock rate 2.
Completed one-shot clips and clip/state changes are separate segments.

Existing animation rates are not retroactively rebuilt by a savestate load.
Connie initially retained rate 2 in the 60 FPS test, then naturally changed to
the patched rate after following Vanilla and returning to idle. Comparisons
exclude that stale segment and use matching active clips after initialization.
No animation rates were manually forced to obtain the result.

| Observation | Stock 30 FPS | Initial 60 FPS patch |
|---|---|---|
| Vanilla running, four complete phase cycles | 120 VBlanks / 2.000353 s | 120 VBlanks / 2.001206 s |
| Connie idle, ten complete cycles | 1200 VBlanks / 20.019280 s | 1200 VBlanks / 20.019530 s |
| Vanilla idle gesture, phase 2 to 160 | 158 VBlanks / 2.633975 s | 158 VBlanks / 2.633977 s |
| Interval between Vanilla's idle gestures | approximately 10 s | approximately 5 s |

These are the new comparison's stable intervals, excluding clip transitions.
Connie's parent and active child both advanced 1200 phase units over those
1200 VBlanks. Vanilla's duration-120 idle clip also advanced from phase 2 to
120 over exactly 118 VBlanks in both configurations. Exact endpoints, code
read-backs and gesture trigger times are recorded in the
[measurement summary](data/steambot-chronicles-animation-comparison.json).
The comparison also sampled an active skeletal track, child
index 46, for Connie's idle and Vanilla's idle gesture. Child `+00` is phase,
`+04` the interpolated scalar bone value, `+0C` the next node, and `+20` its
active state. First/last key pointers at `+18/+1C` carry signed 16-bit times at
key `+04`; use that range to unwrap child phase independently. Child loop
normalization can lag the parent by one update.

The interpolator uses the pre-increment phase to calculate the bone value.
Comparing values at `stored_phase - rate` therefore aligns the same point in
the animation. Connie's 60 common sampled phases and Vanilla's 80 common phases
gave identical scalar values: RMS and maximum difference both zero. This checks
one active bone component per clip, not every joint or every character animation.
The selected running child had zero duration and was excluded from bone claims;
the running comparison uses the parent phase instead.

The idle-cadence difference came from a separate scheduler. Actor `+0224`
(`00A29574` for Vanilla) increments once per stationary update at
`001D5280..001D528C` and resets during movement. `001DD970` tests the initial
150-update delay, and `001DDA18..001DDA28` forces a gesture restart on
`(counter - 150) % 300 == 0`. The recurring 300 updates take ten seconds at
30 FPS and five at 60 FPS, even though the selected gesture plays at the
correct speed. The first comparison documented this issue without changing
the executable patch; the following correction resolves it.

## Idle gesture timing correction

The patch scales all three scheduling constants together, as listed in
the instruction table above. Eligibility begins at counter 301 instead of 151;
forced repeats use `(counter - 300) % 600 == 0`. This preserves both the initial
roughly five-second delay and the subsequent roughly ten-second intervals.

The modulo condition controls a forced restart, not every call to the animation
setter. After passing the threshold, the normal setter at `001DC730` can start
a newly selected clip immediately; `001DC774..001DC778` suppresses restarting
the same clip. On a zero remainder, `001DDA50` selects the unconditional restart
path through `001DC5F0`. This explains the observed first entry at counter 301,
followed by forced entries at 900, 1500 and 2100. These branches apply to
Vanilla's actor identity 0; NPC identities take a different branch.

A 42-second retest began from the same clean state and used three seconds of
forward input to reset the idle counter. PINE read back all three new instruction
words and sampled four gesture entries. The first followed input release by
5.033 seconds, versus 5.063 seconds in the stock trace, within one stock update
of transition uncertainty. Subsequent intervals were:

| Interval | VBlanks / updates at 60 FPS | Wall time |
|---|---:|---:|
| First to second gesture | 599 | 9.989875 s |
| Second to third gesture | 600 | 10.014476 s |
| Third to fourth gesture | 600 | 10.007602 s |

The stock trace's observed interval was 598 VBlanks / 299 updates, or 9.977800
seconds. Entry samples have one update of transition uncertainty; the repeat
constants are exactly 300 stock updates and 600 patched updates. The previous
five-second repeat interval is gone.

All four corrected gestures advanced from phase 2 to 160 over exactly 158
VBlanks, matching stock playback speed. The recorded child-46 scalar values
again matched stock at all 80 common evaluation phases, with RMS and maximum
difference both zero. This is one sampled bone channel, not a whole-skeleton
comparison. The [idle-fix measurement summary](data/steambot-chronicles-idle-timing-fix.json)
records the events, counters, instruction words and matched phase ramps.

The user's current state was backed up before testing and restored in PCSX2
with the then-current thirteen-write patch after verification. The original save slots
were left unchanged.

## Follower movement correction

Playtesting exposed a separate issue: Connie walked behind Vanilla, then rushed
up beside him. The follower action, mode 10 at actor `+00A0`, calls `001DE950`.
It bypasses the shared gait table used by ordinary player input and contains
its own 0.07 walking and 0.16 running constants. Both therefore produced double
the stock distance per second at 60 FPS, despite the corrected player speed.

The two additional writes halve those inline floats by changing their upper
16 bits; the low halves at `001DED88` and `001DEDF0` remain unchanged. Both branches
multiply by actor `+01E8`, write their movement vector at `+0370`, and add it
to accumulated displacement at `+02D0`. The published gait at `+009C` still
selects the walking or running animation. Distance thresholds, target pointer
`+0128`, and the far-distance repositioning path are unchanged. The follower
does not update `+01EC`, so that field is unsuitable for measuring its speed.

Three matched runs used the clean beach state, three seconds of forward input,
then nine seconds stationary: stock, the thirteen-write patch, and the corrected
fifteen-write patch. All Connie samples remained in mode 10. The comparison
uses actual X/Z displacement between successive observed updates with stable
gait and target, normalized to 60 VBlanks; it also records the requested vector.

| Movement | Stock 30 FPS | Before follower fix | Corrected 60 FPS |
|---|---:|---:|---:|
| Connie walking, units per 60 VBlanks | 2.099993 | 4.200001 | 2.099995 |
| Connie running, units per 60 VBlanks | 4.800000 | 9.600000 | 4.800000 |
| Vanilla running, units per 60 VBlanks | 4.799996 | 4.800002 | 4.800002 |

Before the correction, Connie's walking speed nearly matched Vanilla's running
speed, delaying the switch to running; her eventual catch-up then used double
the stock running speed. The correction restores both measured speeds while
preserving player movement. Her final distance from Vanilla was 1.1084 units,
versus 1.1017 stock. Small trajectory and transition differences remain; follower
turn smoothing and its idle-look timer have not been converted.

The [follower comparison](data/steambot-chronicles-follower-comparison.json)
includes instruction read-backs, movement intervals, gait transitions and gaps.

The user also reported that Connie's idle animation looked fast. A separate
12-second capture at the user's saved position compared her active idle clip
`0126DFB0` with the stock reference. Stock completed ten parent and child cycles
over 1200 VBlanks; the corrected patch completed five over 600. Both therefore
take exactly 120 VBlanks per cycle, averaging 2.00193 seconds stock and 2.00174
seconds patched. The sampled child-46 scalar matched at all 60 common evaluation
phases, with RMS and maximum difference zero. No clip or state changes occurred
in the new capture. This observed idle clip is not double speed, so no additional
animation-rate change was made. The
[idle verification](data/steambot-chronicles-follower-idle-verification.json)
records those matched intervals and the scope of the bone comparison.

### Stopping outside the follow area is stock behavior

A later report described Connie staying behind after a longer walk. At the
reported beach position, both stock and patched captures left her at exactly
the same coordinates for six seconds, with mode 10, gait 0 and a zero movement
vector. Vanilla stood 12.3968 horizontal units away. The stock comparison state
restored fourteen instruction/table words from the retail ELF and set interval 2 offline,
preserving the reported positions and other runtime data. Inherited animation
rates in this copy are not evidence about stock animation; this test concerns
the movement gate.

The original call at `001DEB74` invokes `001E1670(follower, target)`. For this
state, Connie's restriction byte `+012C` is 1, all eight allowed surface IDs at
`+012E..+013C` are -1, and the target surface ID is 20. Following therefore
depends on the target position lying inside an active type-5 region, checked
by `0011BA60`. The only active region is record `006D11B0`, ID 2, with inclusive
bounds X `[-38, -24]`, Y `[-7.5, 2.5]`, Z `[45, 55]`. Vanilla's reported
position `(-14.0586, -3.9400, 54.2195)` is outside, while Connie remains inside.
The stock gate returns 1 and `001DEB88` forces the desired gait to zero.
The gate, region-test routines and caller match the retail ELF byte for byte.

A second matched replay applied forward input for 600 VBlanks, followed by
240 VBlanks idle. Vanilla reentered the area at relative VBlank 130 stock and
129 patched; Connie resumed walking at 132 and 130 respectively, one native
update after reentry in each case. Neither route subsequently exited the area.
The captures covered 840 VBlanks with 420 stock updates and 823 patched updates;
the latter did not sustain one update per VBlank, so wall-time and trajectory equality
are not claimed. Both demonstrate the same stop and resume rule.

No patch change was made for this behavior. The user's position was restored
with the fifteen-write patch enabled. See the
[runtime comparison](data/steambot-chronicles-follower-stop-comparison.json) and
[saved-state gate evaluation](data/steambot-chronicles-follower-stop-gate.json).

## Earlier codes and the local experiment

[asasega's original post, number 90, 18 January 2017](https://forums.pcsx2.net/Thread-60-fps-codes?page=9)
identified this serial+CRC and the interval write `005BC89C = 1`, together with
`0055C3CC = 42700000`. The latter doubles the engine-rate denominator to 60.0.
The author explicitly marked the result incomplete and warned about doubled
speed outside the animation correction.

[Red-tv's post, number 895, 27 February 2023](https://forums.pcsx2.net/Thread-60-fps-codes?page=90)
added `00A29538 = 3F000000`, halving the live player's distance multiplier, but
still warned about faster cutscene elements. Its optional player-speed write
was disabled. Those posts establish useful addresses and provenance; they do
not establish normal speed throughout the game.

This patch retains the interval address, changes the animation numerator instead
of the shared denominator, halves the selected gait tables instead of pinning a
single live actor field, and corrects the measured clock rollover and Vanilla's
idle-gesture scheduling. Credit for
the public interval and speed leads belongs to asasega and Red-tv.

A separate loose local experiment was present before this investigation. It
changed the interval's initialization value and used code trampolines for a
child-animation path and one movement branch. Loading a state restored interval
2 while its slowdown corrections remained active. The child-only animation
hook did not cover the native rate setup, and the movement hook missed the
direct input movement path above. Its prose contained earlier performance and
speed claims that were not adopted as evidence for this patch.

## Harness notes

The A/B tests used copies of the existing states and a backed-up loose patch.
Before loading either test state, 28 words targeted by the old local experiment
were restored **offline** from the extracted disc ELF, including its trampolines;
the live interval in the state was reset to 2. Code variants were applied through
a pnach and emulator restart. No code was written into a running emulator.
The portable installation ignored the attempted `-datapath` isolation; the
successful tests used explicit `-statefile` paths and the installed patch
directory. Read-back of the original hook words confirmed a clean baseline.

Forward input used the game's scripted pad replay at `0025E5B0`. The harness
preserved `005D4AB4..005D4AC7`, set remaining ticks `005D4AB8` to `00100000`,
and set both start/current pointers `005D4AC0`/`005D4AC4` to `0042E70C`.
That immutable mask-table location has `00001000` at `+4`, the D-pad-up bit.
It enabled replay at `005D4ABC` last, then disabled and restored it in a cleanup
handler after sampling. The long count must not expire into the adjacent table.
The ordinary reader `00164B40` converts that bit to full left-stick-up input.

For use outside the harness, restart and load a memory-card save. An old savestate
can restore already-initialized animation rates and other old runtime values;
`place=1` alone does not rebuild every dependent object. Prefer a fresh boot
when comparing configurations, and never hot-write a code word also targeted
by a continuous patch or a live interrupt handler.

## Deliberately left alone

On-foot turn smoothing still uses per-update divisors, including 2.5 on the
ordinary path at `001E1A08`. Acceleration and camera smoothing were not converted
to elapsed-time calculations. Equal straight-line distance therefore does not
mean every aspect of the controls feels identical at 30 and 60 FPS.

Vehicles, physics, cutscenes, effects and rhythm minigames were not validated.
The likely twin-stick vehicle paths read raw axes through `00164AE0`, bypassing
the on-foot D-pad conversion; the running test provides no vehicle evidence.
Keep the experimental qualification until those systems have their own matched
measurements. A separate fresh boot reached the opening movie/title sequence,
and memory reads confirmed the interval, animation, gait and clock writes.
That is a startup smoke check, not a fresh-boot gameplay or full-game validation;
the measured gameplay comparisons above used the cleaned test savestate.
