# No-Interlacing candidates: NTSC-U and NTSC-J fan translations

Research notes for picking the next `[No-Interlacing]` patch to write. Scope is deliberately narrow: **NTSC-U retail releases**, and **NTSC-J games with a completed English fan translation**.

Everything here is measured against PCSX2 **2.8.1**'s own bundled database (`resources/patches.zip`, 4704 files; `resources/GameIndex.yaml`, 12830 serials). Regenerate the tables in [`data/`](data/) with:

```
python tools/scan_deinterlace_coverage.py --pcsx2 <PCSX2 install> --out docs/deinterlace/data
```

## The state of play

| | |
|---|---|
| Serials with a deinterlacing or progressive group | **507** (435 distinct titles) |
| NTSC-U | 174 covered of 2364 |
| NTSC-J / NTSC-K | 104 covered of 5949 |
| Median size of the 531 existing deinterlace groups | **2 `patch=` lines** (78% are ≤3) |
| Groups that also set `gsinterlacemode=1` | 85% |

Most solved cases are trivial. [The Ys V patch](devlog-SLPM-66360-ys-v-no-interlacing.md), at 6 lines plus a render-dispatch fix, sits in the top ~10% of complexity in the entire corpus — that is the exception, not the shape of the work.

## Grading a candidate

Tier comes from a measurement, not from genre intuition. Run the game at 2× internal resolution with no patch and read the output height:

| Measurement | Meaning | Tier |
|---|---|---|
| `640x448 -> 1280x896` | Vertical doubles. Full 448-line frame, interlaced only on output. | **TIER-B** — 1–3 instructions |
| `640x448 -> 1280x447` | Vertical does *not* double. One field at a time with an alternating half-line offset. | **TIER-A** — the Ys V case |

Two more grades are worth naming because they change the budget completely:

- **TIER-C** — a dormant 480p path exists in the code and is never taken. Force the mode selector; usually 1–4 immediates.
- **TIER-D** — already solved on a different build. Copy an existing pnach and re-target it. Minutes.

A fan translation always changes the ELF CRC, so **no shipped pnach can load on a translated ISO** even when the untranslated release is fully covered. That makes every translated build uncovered by construction, and it is the cheapest class of work on the platform.

### Do not search for `[No-Interlacing]`

Seventeen games are solved under other group names and a literal search misses all of them: `Full Frame Mode` (Capcom vs. SNK 2, Marvel vs. Capcom 2), `Start in Progressive Mode` (Vexx), `Force Progressive Scan` (Urban Reign, Guitar Hero II/III/Smash Hits), `Autoboot in 480p` (Gran Turismo 4, Tourist Trophy), `240p Progressive Output`, `Interlaced Field Display Fix`.

Match `interlac|progressive|480p|full ?frame` instead, and check **per CRC**, not per serial — an aggregate "has a patch" line can mean one of four CRCs has it.

## Near-free wins

The same game, already solved on another build.

| Target | Copy from | Notes |
|---|---|---|
| Namco × Capcom, English `SLPS-25505_9536E111` | `SLPS-25505_75C01A04` | Both CRCs already ship; only the Japanese one got the group. One line, `201047F4`. The two files share a byte-identical widescreen block, so `.data` did not move. |
| Extermination Undub `SCUS-97112_087A3C85` | `SCUS-97112_0AE679AF` | Two words, `0010187C` / `00101614`. The PAL build uses the identical pair, so an audio-only undub will not move them. |
| Tales of Rebirth, English `SLPS-25450` | `SLPS-25450_B4EC196F` | Two extended NOPs, `2019AB84` / `2019AC0C`. Life Bottle's patch adds a VWF and subtitles, so assume the ELF relinked and byte-search. |
| Tales of Destiny DC, English `SLPS-25842` | `SLPS-25842_E84AA114` | One store rewrite, `20109FA8` → `A620066C`. Same team as above; do both in one sitting. |
| Flower, Sun and Rain, English `SLPS-25034` | `SLPS-25034_8DF76475` | Two NOPs, `0010325C` / `00103524`. Translation is weeks old and nobody has filed the CRC. |
| Gradius III & IV `SLUS-20040` | forum code `5EB127E7` | Two NOPs, `0032EB1C` / `0032EBA4`, 136 bytes apart. Never upstreamed. The JP build `SLPM-62007` has no pnach either. |
| SMT III Nocturne Chronicle `SLPM-66681` | `pcsx2_patches` issue #459 | A working, screenshot-verified NTSC-U pnach (`002AA1B4`, `002ADBE0`) open since Dec 2024. Merging it also closes the ticket. |

**Another Century's Episode is the best of these.** ACE3 `SLPS-25784` has a working one-line forum code — `patch=1,EE,0010208C,word,00000000`, annotated `//64420008`, the canonical half-offset add — and the bundled file for that exact CRC is **100% commented out**, carrying nothing but a disabled widescreen hack. ACE1 `SLPS-25394` and ACE2 `SLPS-25623` measure the same field signature on the same engine with no code at all. One byte-search, three games, plus the `SLPS-73227` reprint and the `SLPS-25829` Special Vocal Version.

### False gaps

`SCUS-97179` (Twisted Metal: Black), `SCUS-97512` (GT3 Greatest Hits) and `SCUS-97201` (The Mark of Kri) are the **same disc** as their solved siblings — Redump's internal serial matches, so the existing patch already loads. `SLUS-20353` (King's Field IV) is a GameIndex alias stub with no dumped disc.

Rule: any `no pnach at all` row whose sibling serial is patched must be checked against Redump's internal-serial field before any work starts.

## NTSC-U shortlist

| # | Game | Serial | Tier | What it needs |
|---|---|---|---|---|
| 1 | Final Fantasy X | `SLUS-20312` | D | One word. PAL donor `SCES-50490_A39517AB` zeroes the interlace argument at `002D98B4`. A 2020 request for this exact CRC went unanswered. |
| 2 | Gust engine sweep — Atelier Iris 1–3, Mana Khemia 1–2, Ar tonelico II | `SLUS-21113`, `21327`, `21564`, `21735`, `21890`, `21788` | D | One NOP each. Donor `SLUS-21445_4437F4B1` (`00340864`). Six patches from one signature — the best ratio on this list. |
| 3 | Zone of the Enders: The 2nd Runner | `SLUS-20545` | B | Measured `512x448 -> 1024x896`. NOP the two half-offset call sites; donor is ZOE1 `SLUS-20148_8CB179A6`. |
| 4 | Yakuza / Yakuza 2 | `SLUS-21348`, `SLUS-21769` | B | **No pnach at all on any of the four serials in any region.** Both measure `512x448 -> 1024x896`. No template exists; genuine from-scratch work, but one engine covers both. |
| 5 | TimeSplitters 2 / Future Perfect | `SLUS-20314`, `SLUS-21148` | B | One NOP each. Donor `SLUS-20090_8966730F`. The other TS1 CRC drifts `0x1B60` *within one game* — match on pattern, never on a delta. |
| 6 | Fatal Frame II | `SLUS-20766` (×2 CRCs) | B | See the correction below: FF1 is **not** a drop-in template. |
| 7 | Total Overdose | `SLUS-21283` | C | Force the dormant DTV480P selector — three immediates. Donor `SLES-53492_4C380F8B`; the identical triple appears in Ape Escape 3 from a different studio. |
| 8 | Sonic Heroes | `SLUS-20718` | C | Force the three `sceGsResetGraph` arguments. **Drop the PAL conditional** — `SLES-51950` gates on the 50/60 Hz menu, which NTSC-U does not have. |
| 9 | Dynasty Warriors 5 | `SLUS-21153` | D | Two lines. Donor `SLUS-21299_A719D130`. Byte-search the *original* forms `64420008` and `30420001`, not the patched ones. |
| 10 | Ys: The Ark of Napishtim | `SLUS-20980` | B | **Done** (`EF9E43EF`), see [the devlog](devlog-SLUS-20980-ys-vi-no-interlacing.md). Three words, and the prediction held — but two of them are not where the Ys V recipe looks: the engine overwrites libgraph's SMODE2 with its own, and the movie player keeps a second pair of display envs. |
| 11 | Final Fantasy XII | `SLUS-20963` | B | Measured `512x448 -> 1024x896`. Also unlocks the IZJS build `SLPM-66750`. |
| 12 | Kingdom Hearts II | `SLUS-21005` | ? | Largest audience on the list, no donor in any region. **Do before KH2 Final Mix+** — one disassembly ships to four to six files across both lanes. |

## NTSC-J fan translations

| # | Game | Serial | Translation | Notes |
|---|---|---|---|---|
| 1 | Ys III: Wanderers from Ys | `SLPM-62532`, `TCPS-10094/10109` | Kaisaan / Josep / Etokapa, v1.0, Aug 2026 | Zero prior art on all three serials, and largely the same people who translated Ys V. Run the Ys V recipe as the working hypothesis. |
| 2 | JoJo's Bizarre Adventure: Phantom Blood | `SLPS-25686` (both CRCs) | penguino + Hudgyn Sasdarl, RHDN #6223 | The only lane-2 entry with third-party attestation of severity. Study `SLPM-65140_61BFF056` for the technique; addresses will not transfer. Penguino118 wrote that fix *and* co-translated this game. |
| 3 | Kingdom Hearts II Final Mix+ | `SLPM-66675` (2 EN CRCs + 1 JP) | Crazycatz00 | The most-played PS2 English fan translation. Solve KH2 first, then re-anchor by signature. |
| 4 | Fate/stay night [Réalta Nua] | `SLPM-66513`, `66512`, `74270` | Quibi v1.0, Jan 2026 | All three serials have no pnach at all. Static high-contrast text is the worst case — every deinterlace mode degrades legibility. Quibi rewrote font *code*, so rebase everything. |
| 5 | Front Mission 5 | `SLPM-66205` | FM Translation Project, Patch 4 | English CRC is already tracked upstream, so this is an append. Diff against `2615F542` first. |
| 6 | Boku no Natsuyasumi 2 | `SCPS-15026` | Hilltop v1.2 | The only entry with a direct, dated player complaint naming the CRC. Never answered. |

Greenfield, no pnach on any serial or CRC: **Berwick Saga** `SLPS-25497`, **SRW OG Gaiden** `SLPS-25836`, **Zill O'll Infinite** `SLPM-65892`, ~~**Cowboy Bebop: Tsuioku no Serenade** `SLPS-25551`~~, **Gantz: The Game** `SLPM-65950`, **Detective Conan** `SLPS-25426`. Gantz is the pick — the Japanese build is unsolved too, so one investigation yields two files.

**Cowboy Bebop is done** (`SLPS-25550_53DDC158`, English v1.0.0), see [the devlog](devlog-SLPS-25550-cowboy-bebop-no-interlacing.md) — and it corrects this list twice. The serial above is the standard edition; the translated disc is the **First Limited Edition `SLPS-25550`**, which has no bundled pnach of any kind, so check the serial off the disc rather than off a wiki. And it measured TIER-B but is really **TIER-C**: the ELF carries a complete `[ 4] 640x480 DTV480` entry in a ten-entry video-mode table that early init never selects. Six words of table data buy 480p progressive instead of two words of hand-forged 448p.

Two gotchas: grep Zill O'll by serial, its GameIndex title uses fullwidth tildes. And boot SRW OG holding Triangle+X first — Banpresto titles of that era sometimes ship a progressive mode.

## Measured field renderers

[`data/fieldrender-gaps.tsv`](data/fieldrender-gaps.tsv) is the evidence-first list: 50 NTSC-U serials whose vertical resolution does not double under upscaling and which have no deinterlacing group. Nothing on it was nominated from memory. Nearly all already carry a Widescreen patch, meaning someone opened the ELF and simply never wrote the interlacing code.

Standouts, with what is already known about each:

- **Wild ARMs 3** `SCUS-97203` — a partial forum code exists; the author notes "interleacing is off but no always, battles shake some intensity". Worth finishing properly.
- **Legaia 2** `SLUS-20414` — a two-line forum code exists and was never merged. A requester calls it "severe interlacing artifacts".
- **Mortal Kombat: Shaolin Monks** `SLUS-21087` — the existing code is explicitly incomplete, fixing 3D but not menus or HUD, and people are still asking.
- **Raiden III** `SLUS-21465` — no patch in any region, and the only shmup in this research whose field rendering survives measurement.
- **Mega Man X7** `SLUS-20487` — measured `512x448 -> 1024x447`. A naive interlace flip is on record as failing. **Done** for the Ns Edition v1.5.2 romhack (`55AC9791`), see [the devlog](devlog-SLUS-20487-mega-man-x7-no-interlacing.md); the failing flip is the CSR.FIELD trap again, and the fix is six words of libgraph output constants. Retail `3EDA6DE7` is untested (no disc to hand), but worth a byte-search: the romhack does not appear to have relocated code, since the shipped retail `[Widescreen 16:9]` address `0014d3e4` still holds its original `lui v0,0x44e0` in this build.
- **Samurai Champloo: Sidetracked** `SLUS-21343` — **Done** (`7A5B4F80`), see [the devlog](devlog-SLUS-21343-samurai-champloo-no-interlacing.md). It reaches this list from nowhere: it is not in the TSV, and the shortlist had it in the bottom tier. `512x224` with `FFMD=1`, stock libgraph, and a half-pixel `XYOFFSET` between the two buffers — one word inside `sceGsResetGraph` takes the interlace flag out and the DISPLAY constants and the field offset both follow on their own.
- **Melty Blood: Act Cadenza** `SLPM-66438` — no pnach at all; the later *Actress Again* `SLPM-55184` has a community code to read as the idiom.
- **Haven — Call of the King** `SLUS-20517`, **Beat Down** `SLUS-21150`, **Dark Angel** `SLUS-20131` — all independently tester-confirmed as still needing a patch, and all reached this list from two directions.

## Triage in ten minutes

Each step is cheaper than the one after it. The first two kill most candidates before a disassembler is opened.

1. **Kill it on paper.** Check `data/deinterlace-coverage.tsv` for the serial, then `ls` the bundle per CRC. Three hard kills: an in-game 480p toggle; a community code outside `patches.zip`; the "missing" sibling being the same disc under a Redump alias.

2. **Does it even shake?** Boot to real 3D gameplay, set deinterlacing to **None**.
   - Stable full image → full-frame renderer, a patch does nothing, **stop**. This killed Silent Hill 4, Suikoden III, Ape Escape 2, Ratchet & Clank, Rogue Galaxy and Tales of the Abyss.
   - Bobs each frame, or combs under Weave → proceed.
   - **Prefers Bob `bff` over Bob `tff` or vice versa → proceed.** A field-order preference only exists if the game genuinely alternates fields. This is the only positive signal available for games the upscale survey never measured.

   Then take an F8 pair on consecutive frames and diff for a one-line vertical shift.

3. **Fix the tier from GS state.** Savestate → `eeMemory.bin`, or a read breakpoint on `0x12001000`. `DH ≈ 2h−1` over a 224/240-line buffer is TIER-A; `DH ≈ h−1` over a 448/512-line buffer is TIER-B; a `0x50` constant present but unreached is TIER-C.

4. **Grep the ELF** (capstone, MIPS64-LE):

   ```
   sceGsResetGraph  sceGsSetDefDispEnv  sceGsPutDispEnv  sceGsSetHalfOffset  SetGsCrt

   64420008        daddiu v0,v0,8  <- THE half-offset add; patch to 64420000 or NOP
                                      hexstring 08004264 for a RAM search
   24xx0050        li reg,0x50 = SCE_GS_DTV480P -> a dormant progressive path
   24060002        the NTSC mode argument you overwrite with 0x50
   000001C0 / 000001E0 / 000000F0     line-count immediates (448 / 480 / 240)
   30420001        andi field-parity mask -> zero it
   lui 0x1200      GS privileged writes: 12000010 SMODE2, 12000070/90 DISPLAY1/2
   ```

   `SMODE2`: 3 = interlaced FRAME, 2 = interlaced FIELD, 0/1 = progressive. The TIER-B fix is usually 3 → 2, plus `DISPLAY DH` from `2h−1` to `h−1`. If `64420008` is absent the game wraps libgraph in a custom routine — that is real disassembly, not a signature scan.

5. **Respect the CSR.FIELD trap — but find out whether the game waits on it or only samples it.** If the game *polls* CSR bit 13 for a change, telling it that it is progressive deadlocks the boot; patch output constants only. This is [attempt 1 of the Ys V devlog](devlog-SLPM-66360-ys-v-no-interlacing.md). A game that merely *reads* the bit once a vsync and feeds it to libgraph's half-offset helper is the opposite case: freezing the bit is precisely what makes the field offset stand down, and the interlace flip is then the whole patch — [Samurai Champloo](devlog-SLUS-21343-samurai-champloo-no-interlacing.md). Which one you have takes one look at the code around the `12001000` read.

6. **Fan translations, before reusing any address.** Boot the translated build and read the CRC — if it did not change there is no gap and the shipped pnach already applies. Confirmed non-CRC-changing mechanisms: data-archive hex edits, texture replacement, hardsubbed FMVs. Otherwise diff the translated ELF against the original to prove `.text` did not move; if the two CRC files' shared `[Widescreen 16:9]` addresses are identical, `.data` did not move, which is strong but not conclusive. Font and word-wrap rewrites **do** relocate code. Carry *every* existing group into the new CRC file so the translated build is not left worse off than the base.

## Corrections and shaky claims

**Four tiers assigned on genre intuition are wrong.** Odin Sphere, GrimGrimoire, Gradius V and R-Type Final were all called true field renderers because 2D shmup or sprite RPG "must" be. All four measure full vertical doubling:

```
Odin Sphere    512x448 -> 1024x896   full frame
GrimGrimoire   640x448 -> 1280x896   full frame
Gradius V      640x448 -> 1280x896   full frame
R-Type Final   640x448 -> 1280x896   full frame
Raiden III     640x448 -> 1280x447   genuinely field-rendered
```

**Fatal Frame 1 is not a template for Fatal Frame II.** FF1 measures `640x448 -> 1280x447` and is field-rendered; FF2 and FF3 both measure `-> 1280x896` and are full-frame. Same studio, different mechanism. Read `SLUS-20388_339A0B8C` for the Tecmo idiom but expect a different fix; FF3 ships a real progressive path in its own ELF and is the better reference.

**Excluded outright.** Vampire Night `SLUS-20221` shows a field signature but has a real in-game 480p mode. Disgaea `SLUS-20666` measures `640x224 -> 1280x448` — a 224-line buffer doubling cleanly, which is a natively progressive 240p game, not a field-rendered one. DMC3 vanilla is completeness only; the Special Edition everyone plays is already solved outside the repo.

**Verify with a five-minute boot test** (hold Triangle+X at the PS2 logo, and check the options screen) before disassembling any of these, whose status rests on absence from a 480p list rather than a positive statement: Just Cause, X-Men Legends 1 & 2, Splinter Cell: Double Agent, The Suffering, Way of the Samurai 2, Sonic Heroes, Persona 4, Raiden III, SRW OG: Original Generations.

**No evidence the artefact is actually bad** — nothing confirms these look wrong, only that nothing refutes it. Rank last however cheap: Castlevania LoI and CoD, Rule of Rose, Clock Tower 3, Kuon, both Contra titles, Kingdom Hearts Final Mix. For Castlevania there is a mild negative signal: felixthecat1970 had all six serials' ELFs open for ultrawide work and wrote no interlacing code, and he writes progressive codes routinely.

**Samurai Champloo was in that last tier and did not belong there.** It is a field renderer with a half-scanline hop in every frame of every scene, and it took one word — see [the devlog](devlog-SLUS-21343-samurai-champloo-no-interlacing.md). "Nothing refutes it" is a statement about who has written about a game, not about the game; the ten-minute boot test settles it, and this tier is where the cheapest wins are hiding rather than the least promising ones.

**The upscale test misgrades a 240p-over-480i game, and this is the important one.** The grading table above assumes a 448-line buffer. A game that renders `512x224` with `SMODE2.FFMD = 1` has its buffer line-doubled by the CRTC into a 448-line display, so it measures `-> 1024x896`, vertical doubling, apparent TIER-B — while actually being a field renderer with a half-line offset. Samurai Champloo measures exactly that and is nothing of the kind. Whenever `FFMD = 1`, ignore the output height and read the two draw environments' `XYOFFSET` instead: `OFY` values 8 apart in 12.4 fixed point *are* the artefact, and equal values mean there is none.

**The bias worth knowing about.** Roughly 70% of everything nominated from memory was rejected, most often as redundant — because fame is exactly what attracted a patch author years ago. Recall-based searching selects *against* the remaining gaps, which is why `data/fieldrender-gaps.tsv` is full of games nobody would think to name.

## Sources

PCSX2 2.8.1's bundled `patches.zip` and `GameIndex.yaml`; the [PCSX2/pcsx2_patches](https://github.com/PCSX2/pcsx2_patches) repository and its open issues; the PCSX2 forum "No interlacing codes" thread; and the community upscale survey of 1081 tested games, which supplies the field-render measurements. The survey is not redistributed here — `tools/scan_deinterlace_coverage.py` takes a path to your own copy.
