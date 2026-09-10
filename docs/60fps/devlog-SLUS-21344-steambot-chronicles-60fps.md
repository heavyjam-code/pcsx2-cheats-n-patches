# Devlog: 60 FPS for Steambot Chronicles (SLUS-21344)

The [patch](../../patches/SLUS-21344_9F391882.pnach) unlocks 60 FPS and corrects
the measured on-foot distance, follower speeds, normal Trotmobile cruising,
acceleration, steering and camera follow, animation-rate setup, idle-gesture
timing and in-game clock. It remains
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

## What the thirty-seven writes change

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
| `0021E7AC` | `3C023E4C` | `3C023DCC` | Trotmobile gait 1 target: approximately 0.200 to 0.100 |
| `0021E814` | `3C023E4C` | `3C023DCC` | Trotmobile gait 2 target: approximately 0.200 to 0.100 |
| `0021E8AC` | `3C023ECC` | `3C023E4C` | Trotmobile gait 3 target: approximately 0.400 to 0.200 |
| `0021E914` | `3C023ECC` | `3C023E4C` | Trotmobile gait 4 target: approximately 0.400 to 0.200 |
| `0021E9AC` | `3C033E4C` | `3C033DCC` | Trotmobile gait 5 target: approximately 0.200 to 0.100 |
| `0021EA04` | `3C033ECC` | `3C033E4C` | Trotmobile gait 6 target: approximately 0.400 to 0.200 |
| `0021E7B4` | `3C034100` | `3C034178` | Gait 1 acceleration divisor: 8 to 15.5 |
| `0021E818` | `3C034100` | `3C034178` | Gait 2 acceleration divisor: 8 to 15.5 |
| `0021E8B4` | `3C034100` | `3C034178` | Gait 3 acceleration divisor: 8 to 15.5 |
| `0021E918` | `3C034100` | `3C034178` | Gait 4 acceleration divisor: 8 to 15.5 |
| `0021E9B4` | `3C024100` | `3C024178` | Gait 5 acceleration divisor: 8 to 15.5 |
| `0021EA0C` | `3C024100` | `3C024178` | Gait 6 acceleration divisor: 8 to 15.5 |
| `0021E7BC` | `3C024180` | `3C0241FC` | Gait 1 yaw-error divisor: 16 to 31.5 |
| `0021E860` | `3C024180` | `3C0241FC` | Gait 2 yaw-error divisor: 16 to 31.5 |
| `0021E8BC` | `3C024180` | `3C0241FC` | Gait 3 yaw-error divisor: 16 to 31.5 |
| `0021E960` | `3C024180` | `3C0241FC` | Gait 4 yaw-error divisor: 16 to 31.5 |
| `0021EEB8` | `3C034180` | `3C0341FC` | Gait 12 ordinary spin yaw-error divisor: 16 to 31.5 |
| `0013B854` | `3C033E33` | `3C033DBB` | Clear-view vehicle-camera eye alpha, upper half |
| `0013B858` | `34633333` | `3463CFC6` | Clear-view alpha, lower half: float bits `3DBBCFC6` |
| `0013B838` | `3C033E80` | `3C033E09` | Obstructed vehicle-camera eye alpha: 0.25 to 0.1337890625 |
| `0013B8F4` | `3C043E33` | `3C043DBB` | Vehicle-camera initialization alpha, upper half |
| `0013B8FC` | `34883333` | `3488CFC6` | Initialization alpha, lower half: float bits `3DBBCFC6` |

The interval is a runtime field. Changing only the initialization argument at
`003D18C4` is insufficient when loading a state that already contains interval 2.
The shipped write maintains `005BC89C = 1`; it does not rely on initialization
running again. All thirty-seven writes use `place=1`.

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

## Trotmobile animation and forward travel

A matched test loaded the user's Trotmobile beach scene from the slot-7 backup.
Both configurations began from the same copy, with all 41 unique targets from
the current and earlier local patches restored offline from the disc ELF and
the display interval reset to 2. The fifteen-write patch was enabled only for
the 60 FPS run, through a restart. No code was written live. Native PCSX2
controller input held both sticks forward; the observed axis bytes were
`[127, 0, 127, 0]` (RX, RY, LX, LY), with vehicle gait 6 and action 0.
The comparison temporarily used 1x internal resolution, without EE overclock.

The vehicle pointer at `0058F660` identifies the object at `0058F6A0` in this
state. Its animation parents at `+135C` and `+15BC` naturally changed to forward
clips `00D00280` (length 12) and `00D3A300` (length 38). Both acquired rate 2
stock and rate 1 patched. This excludes inherited idle rates from the playback
claim. The vehicle calls the same native rate setter at `0022B680`, including
calls around `00219744..00219798`; the existing numerator correction therefore
also reaches these vehicle parents.

After excluding the initial phase hold during the transition, matching
complete-cycle intervals with sustained update cadence measured:

| Parent / clip length | Stock cycles / updates / VBlanks | Patched cycles / updates / VBlanks | Phase units per 60 VBlanks, stock / patched |
|---|---|---|---|
| `+135C` / 12 | 63 / 378 / 756 | 63 / 756 / 756 | 60.000 / 60.000 |
| `+15BC` / 38 | 19 / 361 / 722 | 19 / 722 / 722 | 60.000 / 60.000 |

The tracks advance exactly 2 phase units per stock update and 1 per patched
update. These intervals took 12.613891 versus 12.600922 seconds and 12.043717
versus 12.041928 seconds, respectively. Across the longer available wrap
intervals, the patched tracks lost two and one updates, measuring 59.851 and
59.921 phase units per 60 VBlanks; those small deficits are recorded rather
than claiming sustained 60 FPS throughout the capture. Neither animation runs
at double speed. Both configurations take 12 and 38 VBlanks per cycle at full
cadence (about 0.200 and 0.634 seconds). The other two
sampled parents, `+870C` and `+896C`, remained frozen and provide no playback
evidence. This comparison measures animation-parent progression, not individual
bone values, attacks, turning, jumping or every vehicle animation.

**The fifteen-write patch ran forward vehicle travel approximately twice as fast.** In the
straight interval from 120 to 180 VBlanks after the first sampled forward gait, stock
horizontal displacement was approximately 10.801 units and patched displacement
21.600 units. Later travel hits terrain, so whole-run distance is unsuitable
for this comparison. Gait 6 selects the branch at `0021EA00`, which retains
the target speed `0.40000004 * vehicle[+1010]`, approached using divisor 8.
The observed multiplier is 0.9, producing approximately 0.36 units per update
in both configurations. Doubling update frequency therefore doubles travel
speed even though animation playback is corrected. Acceleration also remains
expressed per update. This first test recorded the issue; the correction below
adds the six vehicle targets to the patch.

The [Trotmobile measurement summary](data/steambot-chronicles-trotmobile-comparison.json)
records the trace hashes, counter/phase endpoints, clip identities and movement
comparison. The original Trotmobile position, 2x resolution and enabled 60 FPS
group were restored afterward; original save files and the installed patch
were preserved. Full captures and the reusable harness remain local.

### Normal Trotmobile cruising-speed correction

The next six writes halve the speed targets in the normal driving branches
for gaits 1 through 6, listed in the instruction table. They change only the
upper half of each float; the following low-half instruction is preserved.
Gaits 1/2 handle single-stick forward/backward input, 3/4 mixed longitudinal
and lateral input, and 5/6 slower/full same-direction input. Full forward and
full reverse both select gait 6. The animation setter and its requested rates
are unchanged.

Halving the stored movement vector after the branches converge would be
incorrect: that vector feeds the next update's acceleration calculation.
Repeatedly halving it would change the equilibrium beyond the intended factor
of two. Halving the target instead preserves the recurrence and halves its
steady result. This is a cruising-speed correction; it does not convert the
acceleration or steering recurrence to elapsed time.

Three fresh stock/corrected comparisons used identical copies of the beach
state, native full-forward/full-reverse/half-pressure-forward controller macros,
1x rendering and no EE overclock. Each captured 360 VBlanks after movement
began. All six new instruction words were read back in each capture. Forward
axes were `[127, 0, 127, 0]`, reverse `[127, 255, 127, 255]`, and slow forward
`[127, 43, 127, 43]`; slow input naturally selected gait 5.

The clean forward and slow intervals cover VBlanks 180 through 300 after
movement onset. Net XZ endpoint distance and the requested vector agree:

| Input | Stock distance per update | Corrected distance per update | Corrected / stock |
|---|---:|---:|---:|
| Full forward | 0.36000071 | 0.18000006 | 0.499999 |
| Slow forward | 0.18002373 | 0.08999999 | 0.499934 |

Multiplying these measured distances by the intended 30/60 updates per second
gives approximately 10.800/10.800 units for full forward and 5.401/5.400 for
slow forward. Those are calculated full-cadence rates, not a claim that every
captured second reached 60 FPS. The corrected intervals contained 119 and 117
updates in 120 VBlanks, so their actual distance per 60 VBlanks was 10.710 and
5.265, versus stock's 10.800 and 5.401. The doubled cruising speed is removed;
missed updates reduce actual speed in this scene.

The reverse test's earlier VBlank 60..120 interval measured 8.595 versus 8.495
units, with a requested-vector ratio of approximately 0.502. Its direction and
terrain response were still changing, and later travel was obstructed. This
supports the correction but is not a precise validation of reverse handling.
Gaits 1..4 share the verified scalar target pattern; their turning trajectories
were not separately validated at this stage.

The forward animation parents retained rate 1, versus stock's 2, with no
additional animation writes. At sustained cadence, the corrected body clip
completed 13 cycles in 156 VBlanks and the leg clip completed four in 152,
matching their stock 12- and 38-VBlank periods. The longer wrap intervals in
all three tests expose missed updates rather than concealing them. This checks
the observed parent tracks, not every bone or vehicle action.

**The cruising-only version still accelerated quicker.** During the first 60 VBlanks, corrected
forward travel was 9.079 units versus stock's 8.351 (about 8.7% farther), and
slow travel was 4.579 versus 4.195 (about 9.2%). The speed targets are halved,
but each update still approached its target using divisor 8. The next section
records the subsequent normal acceleration and steering correction; boost,
jumps and combat still need their own timing work and measurements.

The [speed-fix measurement summary](data/steambot-chronicles-trotmobile-speed-fix.json)
contains all six trace hashes, code read-backs, movement endpoints, animation
intervals and remaining limitations. Final live verification confirmed all 21
patch words after reloading the user's pre-test state at the original settings.
The installed patch was updated, temporary controller macros were removed,
the user's current state was retained in slot 8, and PCSX2 was closed after
verification. Existing slots 1, 7's backup and 9 were preserved.

### Normal acceleration and steering correction

The next sixteen writes correct response coefficients in the six normal driving
branches, five normal steering branches and the vehicle camera. They preserve
the earlier cruising targets and animation setter. Original instruction words
were checked against the extracted ELF, and all 37 installed words were read
back after restarting and loading the user's preserved state.

Each ordinary driving branch calculates `v_next = v + (target - v) / D`.
Keeping divisor 8 while doubling update frequency makes acceleration quicker.
For a fixed target, the stock error retention is `q = 1 - 1/D`; two new updates
should retain the same error, so `D_new = 1 / (1 - sqrt(q))`. For acceleration,
the exact divisor is 15.4833148. The single-instruction value 15.5 gives paired
retention 0.875130073 versus stock's 0.875, about 0.11% slower relaxation. Using
16 would be about 3.45% slower. The target remains halved because it represents
distance per update, and the stored vector still feeds the next recurrence.

The forward startup trace fitted divisor 7.999993 stock and 15.499991 patched,
with targets 0.359999759 and 0.179999893. After stock updates 1, 2, 4, 8 and 12,
compared with patched updates 2, 4, 8, 16 and 24, the normalized requested speeds
agreed within 0.11%. This establishes the response curve independently of
occasional missed updates. During the first 60 VBlanks the patched counter
advanced only 56 updates, versus stock's 30, and displacement was 7.792 versus
8.396 units. That is not evidence of identical startup position in wall time:
missed updates and the smaller integration steps both matter. The later
180..300-VBlank interval traveled 21.600088 versus 21.600043 units.

**Normal release already stops immediately.** The gait-0 branch checks the
previous gait. After normal driving gaits 1..6 it zeros the requested movement
vector at `0021E798`. Both captured releases reached zero in the same VBlank
as neutral stick input. The separate 0.8 damping constants at `0021E77C` and
`0021EF30` belong to other conditions; changing them would not correct ordinary
stopping. They remain untouched.

Steering requires correcting its camera reference as well. Gaits 1/3 add the
wrapped heading error to vehicle `+ED4`; gaits 2/4 calculate the reverse-facing
error first. Gait 12 is an ordinary opposed-stick spin and additionally uses
vehicle multiplier `+1194`, which was 1 in these tests. Each uses divisor 16.
Divisor 31.5 approximates the fixed-target half-step value 31.4919334, with paired
retention 0.937515747 versus stock's 0.9375. These are approximations for a
coupled system, not an exact guarantee for every attachment or camera mode.

The vehicle-camera updater `0013B350` reads the current Trotmobile and its
published yaw at `+F94`. It writes eye interpolation alpha 0.175 to camera
`+254` on the clear-view path at `0013B854..0013B85C`. The common camera code
at `00134738..00134770` blends desired eye `+1F0` from previous eye `+210` with
coefficient `camera[+254] * camera[+25C]`. Camera-derived yaw is stored at `+230`
by `00134904`; steering reads that reference at `0021E66C`. Letting the camera
follow twice as frequently reduces its lag and increases the steering error.

The camera correction uses `1 - sqrt(1 - 0.175)`, float `3DBBCFC6`, approximately
0.09170489. The initializer seeds the same coefficient. The obstruction branch
has only one LUI available for its 0.25 coefficient; replacement `3E090000`
represents 0.1337890625, approximately 0.14% below `1 - sqrt(0.75)`. Its paired
retention is 0.750321388 versus stock's 0.75. That obstruction value is a static
correction: the final captures observed only the clear-view coefficient, with
eye/look-at multipliers 1 and camera `+264` flag 0. That flag controls an offset
applied to the previous eye/look-at positions, not the selected camera mode.
Obstruction transitions and the
separate distance-recovery divisor 8 at `0013B3A4` remain unvalidated.

Simply changing the five turn divisors to 32 with the original camera was
rejected: steady turns remained approximately 12..15% fast. Adding the camera
correction with divisor 32 made the measured turns approximately 1..1.5% slow.
The final 31.5 plus camera correction was then tested with native controller
macros, without input-buffer writes or injected game code:

| Native stick input | Gait | Final steady angular speed versus stock |
|---|---:|---:|
| Left forward, right neutral | 1 | +0.058% |
| Left backward, right neutral | 2 | -0.233% |
| Left forward, right rightward | 3 | +0.047% |
| Left backward, right rightward | 4 | -0.573% |
| Left forward, right backward | 12 | +0.053% |

These comparisons use VBlanks 180..300 after input onset. Repeated scalar yaw
values establish individual update increments; normalized 30/60-update rates
and the independently measured angle per 60 VBlanks agree closely in these
windows. The report retains both, plus sample endpoints and rejection counts.
PINE reads can straddle publication boundaries: for example, the final spin
window contains 120 observed yaw increments while its frame-counter endpoints
differ by 119. Earlier windows also expose real missed updates. None of these
figures promises uninterrupted 60 FPS on this machine.

The final forward animation check retained rate 1 versus stock's 2. The body
parent completed 92 cycles in 1104 VBlanks and the leg parent 29 in 1102, retaining
the stock 12- and 38-VBlank periods. The existing animation correction therefore
survives the handling change; this does not validate every bone or action.

Boost gaits and the L2-triggered spin burst, gait 13, remain unverified. That
burst uses divisor 4 plus a countdown initialized to 8 or 10, shared with boost
handling; these initial values are not a measurement of its total duration.
Halving its angular step alone would halve its total rotation without restoring
duration, so `0021EEE4` remains stock. Actions that retain the vehicle camera
can still be affected by its correction; they are not claimed to be unchanged.

The [handling measurement summary](data/steambot-chronicles-trotmobile-handling.json)
records source hashes, original and final code read-backs, acceleration fits,
native input modes, steering endpoints, animation intervals and rejected
variants. Each code variant was tested through a pnach and restart, using the
same cleaned beach state, 1x rendering and no EE overclock. Full captures and
analysis scripts remain local. The original 2x settings and controller bindings
were restored, temporary slot 6 was removed after a hash check, and the user's
slot 8 retained its original hash. Final verification confirmed all 37 words,
the original input getter, neutral sticks and idle gait; PCSX2 was closed.

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
ordinary path at `001E1A08`. The vehicle-specific response corrections do not
convert the whole engine to elapsed-time calculations. Equal straight-line distance therefore does not
mean every aspect of the controls feels identical at 30 and 60 FPS.

The Trotmobile tests validate forward-animation parent cycles, normal cruising
targets, acceleration response, ordinary release-to-stop behavior and five normal
steering modes in the tested vehicle. Other attachment multipliers, camera
obstruction transitions and camera distance recovery remain unvalidated.
Boost, jumping, combat, other physics, cutscenes, effects
and rhythm minigames remain unvalidated. Twin-stick vehicle
paths read raw axes through `00164AE0`, bypassing the on-foot D-pad conversion;
the earlier on-foot running test provides no vehicle evidence.
Keep the experimental qualification until those systems have their own matched
measurements. A separate fresh boot reached the opening movie/title sequence,
and memory reads confirmed the interval, animation, gait and clock writes.
That is a startup smoke check, not a fresh-boot gameplay or full-game validation;
the measured gameplay comparisons above used the cleaned test savestate.
