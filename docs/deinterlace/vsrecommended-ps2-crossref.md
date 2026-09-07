# /v/'s Recommended Games: PlayStation 2 list, cross-referenced with PCSX2 patch coverage

Source list: https://vsrecommendedgames.miraheze.org/wiki/PlayStation_2 (17 genre subpages, fetched 2026-09-05). Coverage: PCSX2 2.8.1's bundled `patches.zip` (4700 files; verified against upstream `PCSX2/pcsx2_patches` at 2026-09-04, which adds only 5 files, none relevant here) plus this repo's `patches/`. Native-480p data: the PlayStation Fandom 'alternative display modes' table and the Retro Game Boards community sheet (267 titles, 57 confirmed by serial).

Flags on a CRC: **D** = a deinterlacing / progressive group exists, **F** = a 60 FPS group (PAL 50 FPS, 50/60 FPS and NTSC Mode toggles excluded), **B** = a blur / bloom / DoF group. The *primary* build is the NTSC-U release when one exists, else PAL, else NTSC-J. Demo serials are excluded.

| Category | Count |
|---|---|
| REPO | 5 |
| TIER-D | 8 |
| DEINT-DONE (partial) | 9 |
| OPEN | 177 |
| NATIVE-480P | 35 |
| DEINT-DONE | 69 |
| UNMATCHED | 4 |

Categories: **REPO** shipped in this repository. **TIER-D** the primary build has no deinterlacing group but another region or revision does. **DEINT-DONE (partial)** at least one primary CRC has a group and at least one does not. **OPEN** no deinterlacing group on any build and no confirmed native 480p. **NATIVE-480P** the game has a confirmed progressive-scan mode of its own. **DEINT-DONE** every primary CRC already carries a group.

## 1. Already in this repository

| Game | Page | Primary build, CRCs | 480p |
|---|---|---|---|
| Blood Will Tell: Tezuka Osamu's Dororo | Action-adventure | SLES-52755 D78D3D1F | unknown |
| Way of the Samurai 2 | Action-adventure | SLUS-20893 158FA006 1B3EDC36 | unknown |
| Crimson Tears | RPG | SLUS-20948 D31904C2(D) | yes |
| The Sword of Etheria | RPG | SLES-53768 88E95888 | unknown |
| Chikyuu Boueigun 2 (JP) / Global Defence Force (EU) | TPS | SLES-54464 DD35AC9F<br>SLES-54589 (no pnach) | unknown |
| Dragon Quest VIII: The Journey of the Cursed King | RPG | SLUS-21207 F4715852(D) | no |

## 2. A donor patch exists on another build (TIER-D)

A donor named **No-Interlacing** is a real deinterlacing patch to re-target. A donor named **480p Mode** only autoboots a progressive mode the game already has, so the US build most likely carries the same toggle natively; verify on the options screen or with Triangle+Cross at boot before doing any work.

| Game | Page | Primary build, CRCs | 480p | Donor build:CRC = group | In candidates doc |
|---|---|---|---|---|---|
| Spider-Man 2 | Action-adventure | SLUS-20776 E2DFCE12(F) | unknown | SLES-52493:599883D4 = 480p Mode<br>SLES-52447:0864B3F7 = 480p Mode<br>SLES-52372:6B68932C = 480p Mode |  |
| Fatal Frame II: Crimson Butterfly (US) / Project Zero II (EU) | Adventure | SLUS-20766 1C6C1B71 9A51B627 | unknown | SLES-50821:22E91837 = No-Interlacing / No-Interlacing alternative | yes |
| Resident Evil - Code: Veronica X | Adventure | SLUS-20184 24036809 | unknown | SLES-50306:6EA9DDA9 = No-Interlacing<br>SLES-50306:A5434CCF = No-Interlacing |  |
| Alien Hominid | Platformer | SLUS-21090 190DF20A | no | SLES-53139:14274DC3 = 480p Mode |  |
| Final Fantasy X / International | RPG | SLUS-20312 BB3D833A | unknown | SCES-50490:A39517AB = No-Interlacing<br>SCES-50492:941BB7D9 = No-Interlacing | yes |
| Shin Megami Tensei: Nocturne (US) / Shin Megami Tensei: Lucifer's Call (EU) | RPG | SLUS-20911 E8FCF8EC F0A31EE3 | unknown | SLES-53363:AE0DE7B7 = No-Interlacing |  |
| X-Men Legends | RPG | SLUS-20656 CE6A63BF | unknown | SLES-52624:69094734 = 480p Mode |  |
| X-Men Legends II: Rise of Apocalypse | RPG | SLUS-21138 0E707DA4 | unknown | SLES-53377:912C8E55 = 480p Mode |  |

## 3. Partly covered: some primary CRCs lack the group

| Game | Page | Primary build, CRCs | 480p | CRCs lacking | Covered CRCs = group | In candidates doc |
|---|---|---|---|---|---|---|
| Dynasty Warriors 5 / Xtreme Legends | Action-adventure | SLUS-21153 6677B437<br>SLUS-21299 A719D130(D) | unknown | SLUS-21153:6677B437 | SLUS-21299:A719D130 = No-Interlacing | yes |
| Grand Theft Auto: The Trilogy | Action-adventure | SLUS-20062 5E115FB6(DFB)<br>SLUS-20552 20B19E49(F) 248E6126(F) 9E312BAF(F)<br>SLUS-20946 2C6BE434(FB) 399A49CA(DFB) | unknown | SLUS-20552:20B19E49 SLUS-20552:248E6126 SLUS-20552:9E312BAF SLUS-20946:2C6BE434 | SLUS-20062:5E115FB6 = No-Interlacing<br>SLUS-20946:399A49CA = No-Interlacing |  |
| Legacy of Kain: Soul Reaver 2 | Action-adventure | SLUS-20165 1771BFE4 230CB71D(D) | unknown | SLUS-20165:1771BFE4 | SLUS-20165:230CB71D = No-Interlacing |  |
| Onimusha: Dawn of Dreams | Action-adventure | SLUS-21180 FE44479E(D)<br>SLUS-21362 BD17248E FFDE85E9(D) | unknown | SLUS-21362:BD17248E | SLUS-21180:FE44479E = No-Interlacing<br>SLUS-21362:FFDE85E9 = No-Interlacing |  |
| Marvel vs. Capcom 2 | Fighting | SLUS-20486 4D228733(D) 69B2071C | unknown | SLUS-20486:69B2071C | SLUS-20486:4D228733 = Native 480p / Full Frame Mode |  |
| Super Dragon Ball Z | Fighting | SLUS-21442 DE2DF62D(D) FABD7602 | unknown | SLUS-21442:FABD7602 | SLUS-21442:DE2DF62D = No-Interlacing |  |
| Shin Megami Tensei: Persona 3 FES | RPG | SLUS-21621 0033A2C2(D) 060D795D(D) 1D1F5BA9(D) 1EA75934(D) 94A82AAA(D) 970A82A2 97102837(D) | unknown | SLUS-21621:970A82A2 | SLUS-21621:0033A2C2 = Mode 480p<br>SLUS-21621:060D795D = Mode 480p<br>SLUS-21621:1D1F5BA9 = Mode 480p<br>SLUS-21621:1EA75934 = Mode 480p<br>SLUS-21621:94A82AAA = Mode 480p<br>SLUS-21621:97102837 = Mode 480p |  |
| Twisted Metal: Black | Simulation | SCUS-97101 073696DA(D)<br>SCUS-97164 CFCBDF0C<br>SCUS-97179 (no pnach) | unknown | SCUS-97164:CFCBDF0C | SCUS-97101:073696DA = No-Interlacing | yes |
| The Punisher | TPS | SLUS-20864 BC204346 BC2043A7(D) | unknown | SLUS-20864:BC204346 | SLUS-20864:BC2043A7 = No-Interlacing |  |

## 4. Open, and measured as a true field renderer (from [`fieldrender-gaps.tsv`](data/fieldrender-gaps.tsv))

| Game | Page | Primary build, CRCs | 480p | In candidates doc |
|---|---|---|---|---|
| Shadow of Destiny / Memories | Adventure | SLUS-20146 F14DFE0A | unknown |  |
| Final Fight: Streetwise | Beat 'em up | SLUS-21238 7985D894 | unknown |  |
| Mortal Kombat: Shaolin Monks | Beat 'em up | SLUS-21087 455DD546 | unknown | yes |
| 007: Agent Under Fire | FPS | SLUS-20265 79646C72 | unknown |  |
| Monster Rancher 4 | RPG | SLUS-20702 0EF3697B | unknown |  |
| Wild ARMs 3 | RPG | SCUS-97203 06441001<br>SCUS-97224 (no pnach) | unknown | yes |

## 5. Open, already tracked in [the candidates doc](no-interlacing-candidates.md)

| Game | Page | Primary build, CRCs | 480p |
|---|---|---|---|
| Yakuza (US) / Like A Dragon (JP) | Action-adventure | SLUS-21348 (no pnach) | no |
| Yakuza 2 (US) / Like A Dragon 2(JP) | Action-adventure | SLUS-21769 (no pnach) | no |
| Zone of the Enders: The 2nd Runner | Action-adventure | SLUS-20545 FD12A397 | unknown |
| TimeSplitters 2 | FPS | SLUS-20314 12532F1C | unknown |
| TimeSplitters: Future Perfect | FPS | SLUS-21148 (no pnach) | no |
| Atelier Iris: Eternal Mana | RPG | SLUS-21113 E3981DBB | unknown |
| Disgaea: Hour of Darkness | RPG | SLUS-20666 4D2CAC9D | no |
| Final Fantasy XII / International Zodiac Job System | RPG | SLUS-20963 0779FBDB<br>SLUS-21475 (no pnach) | no |
| Kingdom Hearts II / Final Mix+ | RPG | SLUS-21005 DA0535FD(FB) | unknown |
| Gradius III & IV | Shoot 'em up | SLUS-20040 (no pnach) | no |
| Front Mission 5: Scars of the War | Japan | SLPM-66205 2615F542 F60255AC<br>SLPM-66421 (no pnach)<br>SCAJ-20166 (no pnach) | unknown |

## 6. Open and untracked

Nothing here is measured unless a row says so. 'no pnach' means nobody has filed anything for the build; a widescreen-only file means someone opened the ELF and never wrote interlacing code. The ten-minute boot test in [the candidates doc](no-interlacing-candidates.md) still decides each one.

**Measured and rejected so far.** Six discs booted and measured on PCSX2 2.8.1 at 2x, each with an eight-frame screen-resolution burst scored at vertical shifts of -1/0/+1. Every one came back at shift 0 with flat comb energy, and none of them needs a deinterlacing group:

- **Samurai Western** `SLUS-21187` - 640x448, and already 60 fps natively, so it wants neither group.
- **Red Dead Revolver** `SLUS-20500` - 512x448; its 60 FPS group already ships upstream and, measured here, raises the present rate 30 -> 60 without switching field rendering on.
- **Dragon Quest VIII** `SLUS-21207` - 512x448, no half-offset helper in the image. Its dormant 480p mode is now **shipped** as `[No-Interlacing]`: three table words plus one NOP on a wait-for-even-field loop that `sceGsSyncV` can never satisfy in progressive mode. See [the devlog](devlog-SLUS-21207-dragon-quest-viii-no-interlacing.md).
- **Radiata Stories** `SLUS-21262` - genuinely native 480p, and the game prints the Triangle+Cross instruction on its own Screen menu, so the field-render row in the survey data is a 480i measurement. Its own progressive flag is now **shipped** as a one-line `[No-Interlacing]` group; 3D gameplay is the one check still open. See [the devlog](devlog-SLUS-21262-radiata-stories-no-interlacing.md).
- **Oni** `SLUS-20064` - 640x448, no half-offset helper in the image, and eight byte-identical frames of its static main menu.
- **Mortal Kombat: Shaolin Monks** `SLUS-21087` - listed in section 4 on a field-render measurement that did **not** reproduce: 1280x896 in Goro's Lair, and eight byte-identical pause-menu frames with PCSX2's interlace-offset handling tested both ways. Two scenes only, so reproduce before budgeting work.

See [the corrections](no-interlacing-candidates.md#corrections-and-shaky-claims). Frame rate was measured too - Samurai Western, Oni and Shaolin Monks already present 60, Red Dead Revolver and Radiata Stories present 30 - and the levers, and what they cost, are in [the frame-rate survey](../60fps/frame-rate-survey.md).

### Action-adventure

| Game | Page | Primary build, CRCs | 480p |
|---|---|---|---|
| BloodRayne | Action-adventure | SLUS-20461 17244B57(F) | unknown |
| Devil May Cry 3: Dante's Awakening - Special Edition | Action-adventure | SLUS-20964 0BED0AF9<br>SLUS-21361 25FC361B | unknown |
| Dog's Life | Action-adventure | SLUS-21018 35CB5180(FB) | no |
| Freedom Fighters | Action-adventure | SLUS-20658 (no pnach) | no |
| Mercenaries: Playground of Destruction | Action-adventure | SLUS-20932 23510F99 | unknown |
| Ōkami | Action-adventure | SLUS-21115 21068223 | unknown |
| Oni | Action-adventure | SLUS-20064 FD9CD8FC | unknown |
| Peter Jackson's King Kong | Action-adventure | SLUS-21311 2B1CC3FF | no |
| RAD: Robot Alchemic Drive | Action-adventure | SLUS-20445 25C68D58 | unknown |
| Raw Danger! | Action-adventure | SLUS-21501 2905C5C6 | unknown |
| Red Dead Revolver | Action-adventure | SLUS-20500 E169BAF8(FB) | no |
| Samurai Western | Action-adventure | SLUS-21187 9EE4D67B | unknown |
| S.L.A.I. - Steel Lancer Arena International | Action-adventure | SLUS-20969 A9A55B5E | unknown |
| Sniper Elite | Action-adventure | SLUS-21231 395779C5(F) | no |
| The Adventures of Darwin | Action-adventure | SLUS-21592 25E83ED5 | unknown |
| The Godfather | Action-adventure | SLUS-21385 D850707E(F)<br>SLUS-21406 D850707E(F) | unknown |
| The Lord of the Rings: The Two Towers | Action-adventure | SLUS-20578 C818BEC2 | unknown |
| Ultimate Spider-Man | Action-adventure | SLUS-20870 FDD12792(F)<br>SLUS-21285 FDD12792(F) | no |
| Under the Skin | Action-adventure | SLUS-20985 C54CC888 | unknown |
| Warriors Orochi 2 | Action-adventure | SLUS-21803 241C66AE | unknown |

### Adventure

| Game | Page | Primary build, CRCs | 480p |
|---|---|---|---|
| Clock Tower 3 | Adventure | SLUS-20633 274E5444 | unknown |
| Rule of Rose | Adventure | SLUS-21448 F3FD313E | unknown |
| Silent Hill 2: Director's Cut | Adventure | SLUS-20228 8E8E384B FE06A030(FB) | unknown |
| Silent Hill 3 | Adventure | SLUS-20622 2498951B(F) | unknown |
| The Thing | Adventure | SLUS-20371 1B9D49F3(F) 3F0DC9DC(F) | unknown |

### Beat 'em up

| Game | Page | Primary build, CRCs | 480p |
|---|---|---|---|
| Def Jam: Fight for NY | Beat 'em up | SLUS-21004 4538436F | unknown |
| God of War | Beat 'em up | SCUS-97399 D6385328<br>SCUS-97467 56EC00B5 DF3A5A5C | listed, unconfirmed |
| God of War II | Beat 'em up | SCUS-97481 2F123FD8 | listed, unconfirmed |
| The Red Star | Beat 'em up | SLUS-20885 ED4BF0D3 | no |

### Fighting

| Game | Page | Primary build, CRCs | 480p |
|---|---|---|---|
| Fatal Fury: Battle Archives / (volumes 1 and 2) | Fighting | SLUS-21537 (no pnach)<br>SLUS-21723 (no pnach) | unknown |
| Fire Pro Wrestling Returns | Fighting | SLUS-21702 63435086 | unknown |
| Galactic Wrestling: Featuring Ultimate Muscle | Fighting | SLUS-20822 8745F0BA | unknown |
| Guilty Gear XX Accent Core Plus | Fighting | SLUS-21847 (no pnach) | listed, unconfirmed |
| Samurai Shodown Anthology | Fighting | SLUS-21629 (no pnach) | unknown |
| SoulCalibur II | Fighting | SLUS-20643 (no pnach) | listed, unconfirmed |
| Street Fighter Anniversary Collection | Fighting | SLUS-20949 (no pnach) | unknown |
| Street Fighter Alpha Anthology | Fighting | SLUS-21317 72CE7A78(B) | listed, unconfirmed |
| The King of Fighters 2006 (US) / The King of Fighters: Maximum Impact 2 | Fighting | SLUS-21365 4EE93170 | unknown |
| The King of Fighters Collection: The Orochi Saga | Fighting | SLUS-21554 (no pnach) | unknown |
| War of the Monsters | Fighting | SCUS-97197 2EDE12D1<br>SCUS-97260 7CFD0559 | unknown |

### FPS

| Game | Page | Primary build, CRCs | 480p |
|---|---|---|---|
| 007: Nightfire | FPS | SLUS-20579 (no pnach) | unknown |
| Black | FPS | SLUS-21376 5C891FF1(FB) | no |
| Deus Ex: The Conspiracy | FPS | SLUS-20111 (no pnach) | unknown |
| Red Faction | FPS | SLUS-20073 FBF28175 | unknown |
| Red Faction II | FPS | SLUS-20442 8E7FF6F8 | unknown |
| XIII | FPS | SLUS-20677 FCD97245(F) | unknown |

### Platformer

| Game | Page | Primary build, CRCs | 480p |
|---|---|---|---|
| Ape Escape 2 | Platformer | SLUS-20685 BDD9F5E1 | no |
| Castlevania: Curse of Darkness | Platformer | SLUS-21168 3A446111 | unknown |
| Castlevania: Lament of Innocence | Platformer | SLUS-20733 28270F7D | unknown |
| Contra: Shattered Soldier | Platformer | SLUS-20306 582EED0D | unknown |
| Crash Twinsanity | Platformer | SLUS-20909 8CFAB4EA B318AA3C | no |
| Mega Man Anniversary Collection | Platformer | SLUS-20833 (no pnach) | unknown |
| Mega Man X Collection | Platformer | SLUS-21370 (no pnach) | no |
| Metal Slug Anthology | Platformer | SLUS-21550 (no pnach) | unknown |
| Psychonauts | Platformer | SLUS-21120 2373FD16(F) | unknown |
| Rayman 2: Revolution | Platformer | SLUS-20138 D2F77DF2(F) | unknown |
| Splatter Master | Platformer | SLES-53368 1D8EE3CF | unknown |
| SpongeBob SquarePants: Battle for Bikini Bottom | Platformer | SLUS-20680 FD7EEE96 | unknown |
| Stretch Panic (US) / Freak Out (EU) / Hippa Linda (JP) | Platformer | SLUS-20182 854D5885 | unknown |
| Viewtiful Joe | Platformer | SLUS-20951 080D5356 | unknown |
| Viewtiful Joe 2 | Platformer | SLUS-20939 1B7DA82A | unknown |
| Whiplash | Platformer | SLUS-20684 4D22DB95 | unknown |

### Puzzle

| Game | Page | Primary build, CRCs | 480p |
|---|---|---|---|
| Lumines Plus | Puzzle | SLUS-21553 (no pnach) | unknown |

### Racing

| Game | Page | Primary build, CRCs | 480p |
|---|---|---|---|
| IGPX: Immortal Grand Prix | Racing | SLUS-21430 F23579D9 | unknown |
| Test Drive: Eve of Destruction | Racing | SLUS-20910 5D0244D3 | unknown |
| Tokyo Road Race (EU) / Battle Gear 2 (JP) | Racing | SLES-50954 F880239B | unknown |

### RPG

| Game | Page | Primary build, CRCs | 480p |
|---|---|---|---|
| Ar Tonelico 2: Melody of Metafalica | RPG | SLUS-21788 F95F37EE | unknown |
| Atelier Iris 2: The Azoth of Destiny | RPG | SLUS-21327 9AC65D6A | unknown |
| Atelier Iris 3: Grand Phantasm | RPG | SLUS-21564 4CCC9212 | unknown |
| Baldur's Gate: Dark Alliance | RPG | SLUS-20035 773A8DAB | unknown |
| Baldur's Gate: Dark Alliance II | RPG | SLUS-20675 B0859096 | unknown |
| Chaos Wars | RPG | SLUS-21722 56AD161B | unknown |
| Dark Cloud 2 (US) / Dark Chronicle (EU) | RPG | SCUS-97213 1DF41F33(B)<br>SCUS-97229 (no pnach) | unknown |
| Disgaea 2: Cursed Memories | RPG | SLUS-21397 951555A0 | unknown |
| Dragon Quest VIII: The Journey of the Cursed King | RPG | SLUS-21207 (no pnach) | no |
| Final Fantasy X-2 / International + Last Mission | RPG | SLUS-20672 48FE0C71 | unknown |
| Front Mission 4 | RPG | SLUS-20888 EB3AC800 | unknown |
| Gladius | RPG | SLUS-20490 78ADCFB9 | unknown |
| Grandia II | RPG | SLUS-20194 160076FE | unknown |
| .hack://IMOQ / (quadrilogy) | RPG | SLUS-20267 38A894C6<br>SLUS-20562 43048DD4<br>SLUS-20563 0001171A<br>SLUS-20564 DF05D056 | unknown |
| .hack://G.U. / (trilogy) | RPG | SLUS-21258 89E303FC<br>SLUS-21488 0F26BB77<br>SLUS-21489 6364A466 | unknown |
| Kingdom Hearts / Final Mix | RPG | SLUS-20370 0F6B6315(FB) | unknown |
| Kingdom Hearts Re:Chain of Memories | RPG | SLUS-21799 A287DF74(F) | unknown |
| Makai Kingdom: Chronicles of the Sacred Tome | RPG | SLUS-21170 121AFAF5 | unknown |
| Mana-Khemia: Alchemists of Al-Revis | RPG | SLUS-21735 77B0236F | unknown |
| Mana-Khemia 2: Fall of Alchemy | RPG | SLUS-21890 433951E7 | unknown |
| Monster Hunter | RPG | SLUS-20896 0EF16A99 | unknown |
| Monster Rancher EVO | RPG | SLUS-21330 BDFB1507 | unknown |
| Odin Sphere | RPG | SLUS-21577 (no pnach) | unknown |
| Phantom Brave | RPG | SLUS-20955 B43000A1 | no |
| Rogue Galaxy | RPG | SCUS-97490 0643F90C<br>SCUS-97572 (no pnach) | unknown |
| Romancing SaGa | RPG | SLUS-21263 239CF68A | unknown |
| Shadow Hearts: Covenant / Director's Cut | RPG | SLUS-21041 F3BDB2E6(F)<br>SLUS-21044 F3BDB2E6 | unknown |
| Shadow Hearts: From the New World | RPG | SLUS-21326 C3D28EB9 | unknown |
| Shining Force EXA | RPG | SLUS-21567 C3F67CAF | unknown |
| Shin Megami Tensei: Devil Summoner - Raidou Kuzunoha vs. The Soulless Army | RPG | SLUS-21431 BD9EAA7A | unknown |
| Shin Megami Tensei: Devil Summoner 2 - Raidou Kuzunoha vs. King Abaddon | RPG | SLUS-21845 7FAE77BE<br>SLUS-21897 (no pnach) | unknown |
| Shin Megami Tensei: Persona 4 | RPG | SLUS-21782 DE61647A DEDC3B71 | unknown |
| Soul Nomad & the World Eaters | RPG | SLUS-21603 1F159541 | unknown |
| Suikoden III | RPG | SLUS-20387 5F3DD929 | unknown |
| Suikoden V | RPG | SLUS-21291 BCD0B7CD | unknown |
| Tales of the Abyss | RPG | SLUS-21386 045D77E9 14FE77F7 A616A6C2 B6B5A6DC | unknown |
| Xenosaga Episode I: Der Wille zur Macht | RPG | SLUS-20469 6D1276AB | unknown |
| Xenosaga Episode II: Jenseits von Gut und Böse | RPG | SLUS-20892 BBBAAF63 EB39ABEC<br>SLUS-21133 BBBAAF63 EB39ABEC | unknown |
| Xenosaga Episode III: Also sprach Zarathustra | RPG | SLUS-21389 2088950A<br>SLUS-21417 2088950A | unknown |

### Shoot 'em up

| Game | Page | Primary build, CRCs | 480p |
|---|---|---|---|
| Dragon Blaze (EU) | Shoot 'em up | SLES-53874 (no pnach) | unknown |
| Gradius V | Shoot 'em up | SLUS-20712 CDA95971 | unknown |
| Homura | Shoot 'em up | SLES-53964 (no pnach) | unknown |
| R-Type Final | Shoot 'em up | SLUS-20780 85E994DD | unknown |
| Silent Scope | Shoot 'em up | SLUS-20078 53CB5976 | unknown |

### Simulation

| Game | Page | Primary build, CRCs | 480p |
|---|---|---|---|
| BCV: Battle Construction Vehicles | Simulation | SLES-51714 (no pnach) | unknown |
| Jurassic Park: Operation Genesis | Simulation | SLUS-20380 A99B8FE7(F) | unknown |
| Sky Odyssey | Simulation | SLUS-20134 CD213E68 | unknown |

### Sports

| Game | Page | Primary build, CRCs | 480p |
|---|---|---|---|
| Disney Golf | Sports | SLUS-20532 79741C1B | unknown |
| SSX Tricky | Sports | SLUS-20326 (no pnach) | no |
| SSX3 | Sports | SLUS-20772 08FFF00D | unknown |
| Tony Hawk's Pro Skater 3 | Sports | SLUS-20013 EE2B2BAF F77E2FB5 | unknown |
| Tony Hawk's Pro Skater 4 | Sports | SLUS-20504 (no pnach) | no |
| Tony Hawk's Underground | Sports | SLUS-20731 (no pnach) | no |
| Tony Hawk's Underground 2 | Sports | SLUS-20965 (no pnach) | no |

### Stealth

| Game | Page | Primary build, CRCs | 480p |
|---|---|---|---|
| Headhunter | Stealth | SLUS-20416 6B64AB86 | unknown |
| Metal Gear Solid 2: Substance | Stealth | SLUS-20554 93B9A720 C539049D(F) | unknown |
| Metal Gear Solid 3: Subsistence | Stealth | SLUS-21243 01B2FA7F<br>SLUS-21359 053D2239(F)<br>SLUS-21360 (no pnach) | unknown |
| Mister Mosquito | Stealth | SLUS-20375 33D2AA72 | unknown |
| Second Sight | Stealth | SLUS-21033 16E3BE78 | unknown |

### Strategy

| Game | Page | Primary build, CRCs | 480p |
|---|---|---|---|
| GrimGrimoire | Strategy | SLUS-21604 8817166C | unknown |
| Mobile Suit Gundam: Zeonic Front | Strategy | SLUS-20233 23FFE14B | unknown |

### TPS

| Game | Page | Primary build, CRCs | 480p |
|---|---|---|---|
| 007: Everything or Nothing | TPS | SLUS-20751 6848699B | unknown |
| 10,000 Bullets | TPS | SLES-53481 EF97EC8F | unknown |
| Chikyuu Boueigun (JP) / Monster Attack (EU) | TPS | SLES-51856 0AA95F54 | unknown |
| Enter The Matrix | TPS | SLUS-20454 2A968F81 | unknown |
| Fur Fighters: Viggo's Revenge | TPS | SLUS-20088 (no pnach) | no |
| GunGrave: OverDose | TPS | SLUS-21020 83C9749E(F) | unknown |
| Ratchet & Clank | TPS | SCUS-97199 CE4933D0<br>SCUS-97209 (no pnach)<br>SCUS-97240 (no pnach) | unknown |
| Star Wars Battlefront II | TPS | SLUS-21240 02F4B541(FB) 249540F3(FB) 62390B9E | unknown |

### Other

| Game | Page | Primary build, CRCs | 480p |
|---|---|---|---|
| Dokapon Kingdom | Other | SLUS-21778 CDE9832D | unknown |
| Katamari Damacy | Other | SLUS-21008 FA7E3081 | unknown |
| Midway Arcade Treasures / (volumes 1, 2, 3) | Other | SLUS-20801 (no pnach)<br>SLUS-20997 (no pnach)<br>SLUS-21094 B843EAFB | unknown |
| Namco Museum: 50th Anniversary | Other | SLUS-21164 (no pnach) | unknown |
| Sega Classics Collection | Other | SLUS-21009 497DBC3C | unknown |
| Sonic Gems Collection | Other | SLES-53350 4A198252(F) 82DB1E89(F) | unknown |
| Sonic Mega Collection Plus | Other | SLUS-20917 (no pnach) | listed, unconfirmed |
| We ♥ Katamari | Other | SLUS-21230 337B927C | unknown |

### Japan

| Game | Page | Primary build, CRCs | 480p |
|---|---|---|---|
| Berserk: Millennium Falcon Hen Seima Senki no Shou | Japan | SLPM-65686 (no pnach)<br>SLPM-65688 9685E636 | unknown |
| Bust-A-Move: Dance Summit 2001 | Japan | SLPM-62029 F782A513 F881A604 | unknown |
| ChainDive | Japan | SCPS-15054 (no pnach)<br>SCAJ-20043 (no pnach) | unknown |
| Cho Aniki: Seinaru Protein Densetsu | Japan | SLPM-62360 (no pnach)<br>SLPM-62403 (no pnach) | unknown |
| Garouden Breakblow: Fist or Twist | Japan | SLPS-25747 246BD411 | unknown |
| Ibara | Japan | SLPM-66301 (no pnach)<br>TCPS-10131 (no pnach) | unknown |
| Initial D Special Stage | Japan | SLPM-60205 (no pnach)<br>SLPM-65268 A62EBC2C B9FA5764<br>SLPM-68509 (no pnach)<br>SLPM-74420 (no pnach)<br>SCAJ-25008 (no pnach)<br>SLAJ-25008 (no pnach) | unknown |
| NiGHTS Into Dreams... | Japan | SLPM-66926 (no pnach) | yes |
| Saru! Getchu! Million Monkeys | Japan | SCPS-15115 8EFDBAEB<br>SCPS-19325 (no pnach) | unknown |
| Sega Ages 2500: Fantasy Zone - Complete Collection | Japan | SLPM-62780 (no pnach) | unknown |
| Sega Ages 2500: Galaxy Force II - Special Extended Edition | Japan | SLPM-62766 (no pnach) | unknown |
| Sega Ages 2500: Last Bronx | Japan | SLPM-62687 80E809D0 | yes |
| Sega Ages 2500: Phantasy Star Generation 1 | Japan | SLPM-62362 (no pnach)<br>SLPM-62367 (no pnach)<br>SLPM-62666 (no pnach) | unknown |
| Sega Ages 2500: Phantasy Star Generation 2 | Japan | SLPM-62553 (no pnach) | unknown |
| The King of Fighters 2002: Unlimited Match (Tougeki ver.) | Japan | SLPS-25915 (no pnach)<br>SLKA-25457 (no pnach) | yes |
| Thunder Force VI | Japan | SLPM-55096 B5C43B61 | no |

## 7. 60 FPS: primary build lacks a group, another region has one

PAL groups named 50 FPS, 50/60 FPS or NTSC Mode are refresh-rate toggles, not frame-rate unlocks, and are excluded.

| Game | Primary build, CRCs | Donor build:CRC |
|---|---|---|
| Freedom Fighters | SLUS-20658 (no pnach) | SLPM-65548:9B9EFDC3 SLPM-65548:BADCA542 |

## 8. Native 480p, nothing to deinterlace

| Game | Page | Primary build, CRCs | 480p | Matched as |
|---|---|---|---|---|
| Beyond Good & Evil | Action-adventure | SLUS-20763 (no pnach) | yes | Beyond Good & Evil [exact] |
| Prince of Persia: The Sands of Time | Action-adventure | SLUS-20743 7F6EB3D0(FB) | yes | Prince of Persia: The Sands of Time [exact] |
| Prince of Persia: Warrior Within | Action-adventure | SLUS-21022 6B17B39F(FB) | yes | Prince of Persia: Warrior Within [exact] |
| Prince of Persia: The Two Thrones | Action-adventure | SLUS-21287 84F3309D(FB) | yes | Prince of Persia: The Two Thrones [exact] |
| Shadow of the Colossus | Action-adventure | SCUS-97472 (no pnach)<br>SCUS-97505 (no pnach) | yes | Shadow of the Colossus [exact] |
| The Incredible Hulk: Ultimate Destruction | Action-adventure | SLUS-20941 F17AF8BD(F) | yes | Incredible Hulk: Ultimate Destruction [exact] |
| Tomb Raider: Anniversary | Action-adventure | SLUS-21555 (no pnach) | yes | Tomb Raider: Anniversary [exact] |
| Tomb Raider: Legend | Action-adventure | SLUS-21203 (no pnach) | yes | Tomb Raider: Legend [exact] |
| Fatal Frame III: The Tormented (US) / Project Zero III (EU) | Adventure | SLUS-21244 2ADBA7BC(FB) | yes | Fatal Frame III: The Tormented [exact] |
| Haunting Ground | Adventure | SLUS-21075 901AAC09 | yes | Haunting Ground [exact] |
| Resident Evil 4 | Adventure | SLUS-21134 013E349D | yes | Resident Evil 4 [exact] |
| Dragon Ball Z: Budokai 3 | Fighting | SLUS-20998 2A4B60EB C97EF0A4<br>SLUS-21123 (no pnach) | yes | Dragon Ball Z: Budokai 3 [exact] |
| Neo Geo Battle Coliseum | Fighting | SLUS-21708 (no pnach) | yes | NeoGeo Battle Coliseum [fuzzy] |
| Soulcalibur III | Fighting | SLUS-21216 027C604C | yes | Soulcalibur III [exact] |
| The King of Fighters '98: Ultimate Match | Fighting | SLUS-21816 (no pnach) | yes | King of Fighters '98 Ultimate Match [exact] |
| The King of Fighters XI | Fighting | SLUS-21687 (no pnach) | yes | King of Fighters XI [exact] |
| Jak II | Platformer | SCUS-97265 9184AAF1 9E84AAF1<br>SCUS-97273 (no pnach)<br>SCUS-97274 (no pnach)<br>SCUS-97509 (no pnach) | yes | Jak II [exact] |
| Jak 3 | Platformer | SCUS-97330 644CFD03<br>SCUS-97412 (no pnach)<br>SCUS-97516 (no pnach) | yes | Jak 3 [exact] |
| Mega Man X 8 | Platformer | SLUS-20960 196DF4E5 | yes | Mega Man X8 / Rockman X8 (rgb) [serial] |
| Sonic Unleashed | Platformer | SLUS-21846 FB236A46(F) | yes | Sonic Unleashed [exact] |
| Jak X : Combat Racing | Racing | SCUS-97429 (no pnach)<br>SCUS-97486 (no pnach)<br>SCUS-97488 (no pnach)<br>SCUS-97574 (no pnach) | yes | Jak X: Combat Racing [exact] |
| OutRun 2006: Coast 2 Coast | Racing | SLUS-21274 (no pnach) | yes | OutRun 2006: Coast 2 Coast [exact] |
| Mega Man X: Command Mission | RPG | SLUS-20903 C3553F46 | yes | Mega Man X Command Mission [exact] |
| Radiata Stories | RPG | SLUS-21262 (no pnach) | yes | Radiata Stories [exact] |
| Star Ocean: Till the End of Time | RPG | SLUS-20488 (no pnach)<br>SLUS-20891 (no pnach) | yes | Star Ocean: Till the End of Time [exact] |
| Valkyrie Profile 2: Silmeria | RPG | SLUS-21452 (no pnach) | yes | Valkyrie Profile 2: Silmeria [exact] |
| Tony Hawk's American Wasteland | Sports | SLUS-21208 21278F5B(B)<br>SLUS-21295 21278F5B(B) | yes | Tony Hawk's American Wasteland [exact] |
| Hitman: Blood Money | Stealth | SLUS-21108 13E1AD6A(F) | yes | Hitman: Blood Money [exact] |
| Destroy All Humans! | TPS | SLUS-20945 67A29886(F) | yes | Destroy All Humans! [exact] |
| Kill Switch | TPS | SLUS-20706 ECC849C5 | yes | Kill Switch [exact] |
| Ratchet & Clank: Going Commando/Locked and Loaded | TPS | SCUS-97268 38996035 B3A71D10<br>SCUS-97322 (no pnach)<br>SCUS-97323 (no pnach)<br>SCUS-97374 (no pnach)<br>SCUS-97381 (no pnach)<br>SCUS-97513 (no pnach) | yes | Ratchet & Clank: Going Commando [prefix] |
| Ratchet & Clank: Up Your Arsenal! | TPS | SCUS-97353 45FE0CC4 49536F3F(F)<br>SCUS-97411 (no pnach)<br>SCUS-97413 (no pnach)<br>SCUS-97518 (no pnach) | yes | Ratchet & Clank: Up Your Arsenal [exact] |
| Ratchet: Deadlocked | TPS | SCUS-97465 9BFBCD42(F)<br>SCUS-97485 (no pnach)<br>SCUS-97487 (no pnach) | yes | Ratchet: Deadlocked [exact] |
| Syphon Filter: Dark Mirror | TPS | SCUS-97362 3D92EAFF<br>SCUS-97620 (no pnach) | yes | Syphon Filter: Dark Mirror [exact] |
| Capcom Classics Collection / (volumes 1 and 2) | Other | SLUS-21316 (no pnach)<br>SLUS-21473 (no pnach) | yes | Capcom Classics Collection Volume 2 (rgb) [serial] |

## 9. Already solved in the bundle

Groups named 480p Mode, Mode 480p, Autoboot in 480p or Force Progressive Scan autoboot a native progressive mode rather than deinterlace; either way there is nothing to write.

| Game | Page | Primary build, CRCs | 480p | Group |
|---|---|---|---|---|
| Bujingai: The Forsaken City | Action-adventure | SLUS-20895 521D40D2(D) | unknown | SLUS-20895:521D40D2 = No-Interlacing |
| Bully (US) / Canis Canem Edit (EU) | Action-adventure | SLUS-21269 28703748(DB) | no | SLUS-21269:28703748 = 480p Mode |
| Devil May Cry | Action-adventure | SLUS-20216 79B8A95F(DB) | unknown | SLUS-20216:79B8A95F = No-Interlacing |
| Ico | Action-adventure | SCUS-97113 6F8545DB(DF)<br>SCUS-97159 (no pnach) | no | SCUS-97113:6F8545DB = No-Interlacing |
| Legacy of Kain: Defiance | Action-adventure | SLUS-20773 728AB07C(D) | unknown | SLUS-20773:728AB07C = No-Interlacing |
| Michigan: Report from Hell | Action-adventure | SLES-53073 DCD7104E(D) | unknown | SLES-53073:DCD7104E = No-Interlacing |
| Onimusha: Warlords | Action-adventure | SLUS-20018 A07A5057(D) | unknown | SLUS-20018:A07A5057 = No-Interlacing |
| Onimusha 2: Samurai's Destiny | Action-adventure | SLUS-20393 5848889C(D) | unknown | SLUS-20393:5848889C = No-Interlacing |
| Onimusha 3: Demon Siege | Action-adventure | SLUS-20694 6BF11378(D) | unknown | SLUS-20694:6BF11378 = No-Interlacing |
| Psi-Ops: The Mindgate Conspiracy | Action-adventure | SLUS-20688 9C71B59E(DF) | unknown | SLUS-20688:9C71B59E = No-interlacing |
| Rygar: The Legendary Adventure | Action-adventure | SLUS-20471 3E2A42FA(D) | unknown | SLUS-20471:3E2A42FA = No-Interlacing |
| Shadow of Rome | Action-adventure | SLUS-20902 57818AF6(D) | yes | SLUS-20902:57818AF6 = No-Interlacing |
| The Simpsons Hit & Run | Action-adventure | SLUS-20624 FC99EC8C(DB) | no | SLUS-20624:FC99EC8C = 480p Mode |
| Way of the Samurai | Action-adventure | SLUS-20407 06157251(D) | unknown | SLUS-20407:06157251 = No-Interlacing |
| Zone of the Enders | Action-adventure | SLUS-20148 8CB179A6(D) | unknown | SLUS-20148:8CB179A6 = No-Interlacing |
| Chu♥lip | Adventure | SLUS-20742 25E1B231(D) | unknown | SLUS-20742:25E1B231 = No-Interlacing |
| Fatal Frame (US) / Project Zero (EU) | Adventure | SLUS-20388 339A0B8C(DB) | unknown | SLUS-20388:339A0B8C = No-Interlacing |
| God Hand | Beat 'em up | SLUS-21503 6FB69282(D) | unknown | SLUS-21503:6FB69282 = No-Interlacing |
| The Bouncer | Beat 'em up | SLUS-20069 FEE23E8F(D) | unknown | SLUS-20069:FEE23E8F = No-Interlacing |
| The Warriors | Beat 'em up | SLUS-21215 B99A75DE(D) | no | SLUS-21215:B99A75DE = 480p Mode |
| Urban Reign | Beat 'em up | SLUS-21209 BDD9BAAD(D) | yes | SLUS-21209:BDD9BAAD = Force Progressive Scan |
| Bloody Roar 3 | Fighting | SLUS-20212 AA4E5A35(D) | unknown | SLUS-20212:AA4E5A35 = No-Interlacing |
| Capcom vs. SNK 2: Mark of the Millenium | Fighting | SLUS-20246 15149318(D) | unknown | SLUS-20246:15149318 = Full Frame Mode |
| Street Fighter EX 3 | Fighting | SLUS-20130 72B3802A(DB) | unknown | SLUS-20130:72B3802A = No-Interlacing |
| Tekken 5 | Fighting | SLUS-21059 652050D2(D)<br>SLUS-21160 (no pnach) | yes | SLUS-21059:652050D2 = 480p Mode |
| Tekken Tag Tournament | Fighting | SLUS-20001 67454C1E(D) E84C9242(D) | unknown | SLUS-20001:67454C1E = No-Interlacing<br>SLUS-20001:E84C9242 = No-Interlacing |
| Virtua Fighter 4: Evolution | Fighting | SLUS-20616 C9DEF513(D) | unknown | SLUS-20616:C9DEF513 = No-Interlacing |
| DarkWatch | FPS | SLUS-21042 327053E8(DF) | unknown | SLUS-21042:327053E8 = No-Interlacing |
| Killzone | FPS | SCUS-97402 CAAEC49C(DB)<br>SCUS-97432 (no pnach)<br>SCUS-97517 (no pnach) | no | SCUS-97402:CAAEC49C = No-Interlacing |
| TimeSplitters | FPS | SLUS-20090 8966730F(D) B4A004F2(D) | unknown | SLUS-20090:8966730F = No-Interlacing<br>SLUS-20090:B4A004F2 = No-Interlacing |
| Ape Escape 3 | Platformer | SCUS-97501 7571AAEE(D)<br>SCUS-97548 (no pnach) | no | SCUS-97501:7571AAEE = No-Interlacing |
| Crash Bandicoot: The Wrath of Cortex | Platformer | SLUS-20238 103B5706(D) 5188ABCA(D) | unknown | SLUS-20238:103B5706 = No-Interlacing<br>SLUS-20238:5188ABCA = No-Interlacing |
| Jak and Daxter: The Precursor Legacy | Platformer | SCUS-97124 143976AB(D) 1B3976AB(D) 472E7699(D)<br>SCUS-97170 (no pnach)<br>SCUS-97171 (no pnach) | no | SCUS-97124:143976AB = No-Interlacing<br>SCUS-97124:1B3976AB = No-Interlacing<br>SCUS-97124:472E7699 = No-Interlacing |
| Klonoa 2: Lunatea's Veil | Platformer | SLUS-20151 2F56CBC9(D) | unknown | SLUS-20151:2F56CBC9 = No-Interlacing |
| Maximo: Ghosts to Glory | Platformer | SLUS-20017 0958556B(D) | unknown | SLUS-20017:0958556B = No-Interlacing |
| Maximo vs. Army of Zin | Platformer | SLUS-20722 8CF7CBC0(D) | unknown | SLUS-20722:8CF7CBC0 = No-Interlacing |
| Nightshade | Platformer | SLUS-20810 519E816B(D) | unknown | SLUS-20810:519E816B = No-Interlacing |
| Rayman 3: Hoodlum Havoc | Platformer | SLUS-20601 146F67E5(D) | yes | SLUS-20601:146F67E5 = 480p Mode |
| Shinobi | Platformer | SLUS-20459 BFCC3E7E(D) | unknown | SLUS-20459:BFCC3E7E = No-Interlacing |
| Sly Cooper and the Thievius Raccoonus | Platformer | SCUS-97198 C77AF2CA(DB)<br>SCUS-97210 EF7F0CE6(DB) | unknown | SCUS-97198:C77AF2CA = No-Interlacing<br>SCUS-97210:EF7F0CE6 = No-Interlacing |
| Sly 2: Band of Thieves | Platformer | SCUS-97316 07652DD9(DB) FDA1CBF6(DB)<br>SCUS-97415 5B93397F(DB)<br>SCUS-97457 B3E892E4(D)<br>SCUS-97519 (no pnach) | unknown | SCUS-97316:07652DD9 = No-Interlacing<br>SCUS-97316:FDA1CBF6 = No-Interlacing<br>SCUS-97415:5B93397F = No-Interlacing<br>SCUS-97457:B3E892E4 = No-Interlacing |
| Sly 3: Honor Among Thieves | Platformer | SCUS-97464 8BC95883(DB)<br>SCUS-97484 3130A4D3(DB)<br>SCUS-97527 35CCFA60(DB) | unknown | SCUS-97464:8BC95883 = No-Interlacing<br>SCUS-97484:3130A4D3 = No-Interlacing<br>SCUS-97527:35CCFA60 = No-Interlacing |
| The Adventures of Cookie & Cream (US) / Kuri Kuri Mix (JP/EU) | Puzzle | SLUS-20170 348CEAC4(D) | unknown | SLUS-20170:348CEAC4 = No-Interlacing |
| Burnout 3: Takedown | Racing | SLUS-21050 BEBF8793(DFB) | yes | SLUS-21050:BEBF8793 = Progressive Scan |
| Gran Turismo 4 | Racing | SCUS-90682 (no pnach)<br>SCUS-97328 77E61C8A(D)<br>SCUS-97436 32A1C752(D)<br>SCUS-97563 (no pnach) | yes | SCUS-97328:77E61C8A = Autoboot in 480p<br>SCUS-97436:32A1C752 = No-Interlacing |
| Kinetica | Racing | SCUS-97132 D39C08F5(D)<br>SCUS-97161 (no pnach) | unknown | SCUS-97132:D39C08F5 = No-Interlacing |
| Tokyo Xtreme Racer 3 (US) / Shutokō Battle 01 (JP) | Racing | SLUS-20831 0F932D81(D) 0F9348FF(D) | unknown | SLUS-20831:0F932D81 = No-Interlacing<br>SLUS-20831:0F9348FF = No-Interlacing |
| Ar Tonelico: Melody of Elemia | RPG | SLUS-21445 4437F4B1(D) | unknown | SLUS-21445:4437F4B1 = No-Interlacing |
| Breath of Fire: Dragon Quarter | RPG | SLUS-20499 588CC41B(D) | unknown | SLUS-20499:588CC41B = No-Interlacing |
| Champions of Norrath: Realms of EverQuest | RPG | SLUS-20565 90E66BC5(D) | unknown | SLUS-20565:90E66BC5 = No-Interlacing |
| Dark Cloud | RPG | SCUS-97111 A5C05C78(D)<br>SCUS-97152 (no pnach) | unknown | SCUS-97111:A5C05C78 = No-Interlacing |
| Drakengard | RPG | SLUS-20732 9679D44C(D) | unknown | SLUS-20732:9679D44C = No-Interlacing |
| Forever Kingdom | RPG | SLUS-20343 E3C4037C(D) | unknown | SLUS-20343:E3C4037C = No-Interlacing |
| Okage: Shadow King | RPG | SCUS-97129 E0426FC6(D) | unknown | SCUS-97129:E0426FC6 = No-Interlacing |
| Shadow Hearts | RPG | SLUS-20347 8BE3D7B2(D) | unknown | SLUS-20347:8BE3D7B2 = No-Interlacing |
| Shin Megami Tensei: Digital Devil Saga | RPG | SLUS-20974 D7273511(DB) | unknown | SLUS-20974:D7273511 = No Interlacing |
| Shin Megami Tensei: Digital Devil Saga 2 | RPG | SLUS-21152 D382C164(DB) | unknown | SLUS-21152:D382C164 = No Interlacing |
| Tales of Legendia | RPG | SLUS-21201 43AB7214(D) | unknown | SLUS-21201:43AB7214 = No-Interlacing |
| Ace Combat 04: / Shattered Skies (US) / Distant Thunder (EU) | Simulation | SLUS-20152 A32F7CD0(D) | no | SLUS-20152:A32F7CD0 = No-Interlacing |
| Ace Combat 5: / The Unsung War (US) / Squadron Leader (EU) | Simulation | SLUS-20851 39B574F0(D) | no | SLUS-20851:39B574F0 = No-Interlacing |
| Ace Combat Zero: The Belkan War | Simulation | SLUS-21346 65729657(D) | no | SLUS-21346:65729657 = No-Interlacing |
| SkyGunner | Simulation | SLUS-20384 A9461CB2(D) | unknown | SLUS-20384:A9461CB2 = No-Interlacing |
| Tenchu: Wrath of Heaven | Stealth | SLUS-20397 767E383D(D) | yes | SLUS-20397:767E383D = No-Interlacing |
| Armored Core: Nexus | TPS | SLUS-20986 7E5F690C(DB)<br>SLUS-21079 7E5F690C(DB) | unknown | SLUS-20986:7E5F690C = No-Interlacing<br>SLUS-21079:7E5F690C = No-Interlacing |
| GunGrave | TPS | SLUS-20493 BF5D9AEC(D) | unknown | SLUS-20493:BF5D9AEC = No-Interlacing |
| Gitaroo Man | Other | SLUS-20294 7130C553(D) | unknown | SLUS-20294:7130C553 = No-Interlacing |
| PaRappa the Rapper 2 | Other | SCUS-97167 2D368982(D) | unknown | SCUS-97167:2D368982 = No-Interlacing |
| Taito Legends / (volumes 1 and 2) | Other | SLUS-21122 (no pnach)<br>SLUS-21349 82651334(D) | unknown | SLUS-21349:82651334 = No-Interlacing |
| The King of Fighters '94 Re-Bout | Japan | SLPS-25448 E74F7C39(D)<br>SLPS-25449 (no pnach) | yes | SLPS-25448:E74F7C39 = No-Interlacing |

## 10. Japan page: English fan translations the wiki links

A translation patch changes the ELF CRC, so none of these translated builds can load a bundled pnach even where the Japanese base has one.

| Game | Primary build, CRCs | Translation | Category |
|---|---|---|---|
| Berserk: Millennium Falcon Hen Seima Senki no Shou | SLPM-65686 (no pnach)<br>SLPM-65688 9685E636 | [http://www.romhacking.net/translations/2837/ Link] | OPEN |
| Front Mission 5: Scars of the War | SLPM-66205 2615F542 F60255AC<br>SLPM-66421 (no pnach)<br>SCAJ-20166 (no pnach) | [http://www.romhacking.net/translations/1297/ Link] | OPEN |
| Saru! Getchu! Million Monkeys | SCPS-15115 8EFDBAEB<br>SCPS-19325 (no pnach) | [https://github.com/Gigahawk/sarugetchu_mm_patcher Link] | OPEN |
| Sega Ages 2500: Phantasy Star Generation 1 | SLPM-62362 (no pnach)<br>SLPM-62367 (no pnach)<br>SLPM-62666 (no pnach) | [https://www.pscave.com/psg1/download/ Link] | OPEN |
| Sega Ages 2500: Phantasy Star Generation 2 | SLPM-62553 (no pnach) | [https://www.pscave.com/psg2/download/ Link] | OPEN |

## Appendix: every entry

| Game | Page | Category | Primary build, CRCs | 480p | Deint donors | 60 FPS | Blur |
|---|---|---|---|---|---|---|---|
| Beyond Good & Evil | Action-adventure | NATIVE-480P | SLUS-20763 (no pnach) | yes |  |  |  |
| Blood Will Tell: Tezuka Osamu's Dororo | Action-adventure | REPO | SLES-52755 D78D3D1F | unknown |  |  |  |
| BloodRayne | Action-adventure | OPEN | SLUS-20461 17244B57(F) | unknown |  | yes |  |
| Bujingai: The Forsaken City | Action-adventure | DEINT-DONE | SLUS-20895 521D40D2(D) | unknown |  |  |  |
| Bully (US) / Canis Canem Edit (EU) | Action-adventure | DEINT-DONE | SLUS-21269 28703748(DB) | no | SLES-53561:C78A495D |  | yes |
| Devil May Cry | Action-adventure | DEINT-DONE | SLUS-20216 79B8A95F(DB) | unknown |  |  | yes |
| Devil May Cry 3: Dante's Awakening - Special Edition | Action-adventure | OPEN | SLUS-20964 0BED0AF9<br>SLUS-21361 25FC361B | unknown |  |  |  |
| Dog's Life | Action-adventure | OPEN | SLUS-21018 35CB5180(FB) | no |  | yes | yes |
| Dynasty Warriors 5 / Xtreme Legends | Action-adventure | DEINT-DONE (partial) | SLUS-21153 6677B437<br>SLUS-21299 A719D130(D) | unknown |  |  |  |
| Freedom Fighters | Action-adventure | OPEN | SLUS-20658 (no pnach) | no |  |  (donor SLPM-65548:9B9EFDC3 SLPM-65548:BADCA542) |  |
| Grand Theft Auto: The Trilogy | Action-adventure | DEINT-DONE (partial) | SLUS-20062 5E115FB6(DFB)<br>SLUS-20552 20B19E49(F) 248E6126(F) 9E312BAF(F)<br>SLUS-20946 2C6BE434(FB) 399A49CA(DFB) | unknown | SLES-52927:B61F872C SLES-50330:021396FD SLES-50330:581954FC SLES-51061:26954C46 SLES-51061:C498A04F SLES-51061:CFCB0D20 SLES-52541:A1B3F232 SLES-52541:B440A8FE | yes | yes |
| Ico | Action-adventure | DEINT-DONE | SCUS-97113 6F8545DB(DF)<br>SCUS-97159 (no pnach) | no | SCES-50760:5C991F4E SCPS-11003:B01A4C95 SCPS-19103:B1228D1E SCPS-56001:2DF2C1EA | yes |  |
| Legacy of Kain: Soul Reaver 2 | Action-adventure | DEINT-DONE (partial) | SLUS-20165 1771BFE4 230CB71D(D) | unknown |  |  |  |
| Legacy of Kain: Defiance | Action-adventure | DEINT-DONE | SLUS-20773 728AB07C(D) | unknown |  |  |  |
| Mercenaries: Playground of Destruction | Action-adventure | OPEN | SLUS-20932 23510F99 | unknown |  |  |  |
| Michigan: Report from Hell | Action-adventure | DEINT-DONE | SLES-53073 DCD7104E(D) | unknown |  |  |  |
| Ōkami | Action-adventure | OPEN | SLUS-21115 21068223 | unknown |  |  |  |
| Oni | Action-adventure | OPEN | SLUS-20064 FD9CD8FC | unknown |  |  |  |
| Onimusha: Warlords | Action-adventure | DEINT-DONE | SLUS-20018 A07A5057(D) | unknown |  |  |  |
| Onimusha 2: Samurai's Destiny | Action-adventure | DEINT-DONE | SLUS-20393 5848889C(D) | unknown |  |  |  |
| Onimusha 3: Demon Siege | Action-adventure | DEINT-DONE | SLUS-20694 6BF11378(D) | unknown |  |  |  |
| Onimusha: Dawn of Dreams | Action-adventure | DEINT-DONE (partial) | SLUS-21180 FE44479E(D)<br>SLUS-21362 BD17248E FFDE85E9(D) | unknown |  |  |  |
| Peter Jackson's King Kong | Action-adventure | OPEN | SLUS-21311 2B1CC3FF | no |  |  |  |
| Prince of Persia: The Sands of Time | Action-adventure | NATIVE-480P | SLUS-20743 7F6EB3D0(FB) | yes |  | yes | yes |
| Prince of Persia: Warrior Within | Action-adventure | NATIVE-480P | SLUS-21022 6B17B39F(FB) | yes |  | yes | yes |
| Prince of Persia: The Two Thrones | Action-adventure | NATIVE-480P | SLUS-21287 84F3309D(FB) | yes |  | yes | yes |
| Psi-Ops: The Mindgate Conspiracy | Action-adventure | DEINT-DONE | SLUS-20688 9C71B59E(DF) | unknown | SLES-52702:5E7EB5E2 SLES-52703:C08BE6C0 | yes |  |
| RAD: Robot Alchemic Drive | Action-adventure | OPEN | SLUS-20445 25C68D58 | unknown |  |  |  |
| Raw Danger! | Action-adventure | OPEN | SLUS-21501 2905C5C6 | unknown |  |  |  |
| Red Dead Revolver | Action-adventure | OPEN | SLUS-20500 E169BAF8(FB) | no |  | yes | yes |
| Rygar: The Legendary Adventure | Action-adventure | DEINT-DONE | SLUS-20471 3E2A42FA(D) | unknown |  |  |  |
| Samurai Western | Action-adventure | OPEN | SLUS-21187 9EE4D67B | unknown |  |  |  |
| Shadow of Rome | Action-adventure | DEINT-DONE | SLUS-20902 57818AF6(D) | yes | SLES-52950:B1995E29 |  |  |
| Shadow of the Colossus | Action-adventure | NATIVE-480P | SCUS-97472 (no pnach)<br>SCUS-97505 (no pnach) | yes |  |  |  |
| S.L.A.I. - Steel Lancer Arena International | Action-adventure | OPEN | SLUS-20969 A9A55B5E | unknown |  |  |  |
| Sniper Elite | Action-adventure | OPEN | SLUS-21231 395779C5(F) | no |  | yes |  |
| Spider-Man 2 | Action-adventure | TIER-D | SLUS-20776 E2DFCE12(F) | unknown | SLES-52493:599883D4 SLES-52447:0864B3F7 SLES-52372:6B68932C | yes |  |
| The Adventures of Darwin | Action-adventure | OPEN | SLUS-21592 25E83ED5 | unknown |  |  |  |
| The Godfather | Action-adventure | OPEN | SLUS-21385 D850707E(F)<br>SLUS-21406 D850707E(F) | unknown |  | yes |  |
| The Incredible Hulk: Ultimate Destruction | Action-adventure | NATIVE-480P | SLUS-20941 F17AF8BD(F) | yes |  | yes |  |
| The Lord of the Rings: The Two Towers | Action-adventure | OPEN | SLUS-20578 C818BEC2 | unknown |  |  |  |
| The Simpsons Hit & Run | Action-adventure | DEINT-DONE | SLUS-20624 FC99EC8C(DB) | no | SLES-51897:73E68475 |  | yes |
| Tomb Raider: Anniversary | Action-adventure | NATIVE-480P | SLUS-21555 (no pnach) | yes | SLES-54674:A629A376 |  |  |
| Tomb Raider: Legend | Action-adventure | NATIVE-480P | SLUS-21203 (no pnach) | yes | SLES-53908:05177ECE |  |  |
| Ultimate Spider-Man | Action-adventure | OPEN | SLUS-20870 FDD12792(F)<br>SLUS-21285 FDD12792(F) | no |  | yes |  |
| Under the Skin | Action-adventure | OPEN | SLUS-20985 C54CC888 | unknown |  |  |  |
| Warriors Orochi 2 | Action-adventure | OPEN | SLUS-21803 241C66AE | unknown |  |  |  |
| Way of the Samurai | Action-adventure | DEINT-DONE | SLUS-20407 06157251(D) | unknown |  |  |  |
| Way of the Samurai 2 | Action-adventure | REPO | SLUS-20893 158FA006 1B3EDC36 | unknown |  |  |  |
| Yakuza (US) / Like A Dragon (JP) | Action-adventure | OPEN | SLUS-21348 (no pnach) | no |  |  |  |
| Yakuza 2 (US) / Like A Dragon 2(JP) | Action-adventure | OPEN | SLUS-21769 (no pnach) | no |  |  |  |
| Zone of the Enders | Action-adventure | DEINT-DONE | SLUS-20148 8CB179A6(D) | unknown |  |  |  |
| Zone of the Enders: The 2nd Runner | Action-adventure | OPEN | SLUS-20545 FD12A397 | unknown |  |  |  |
| Chu♥lip | Adventure | DEINT-DONE | SLUS-20742 25E1B231(D) | unknown |  |  |  |
| Clock Tower 3 | Adventure | OPEN | SLUS-20633 274E5444 | unknown |  |  |  |
| Fatal Frame (US) / Project Zero (EU) | Adventure | DEINT-DONE | SLUS-20388 339A0B8C(DB) | unknown | SLES-50821:22E91837 SLPS-25074:9883194E |  | yes |
| Fatal Frame II: Crimson Butterfly (US) / Project Zero II (EU) | Adventure | TIER-D | SLUS-20766 1C6C1B71 9A51B627 | unknown | SLES-50821:22E91837 |  |  |
| Fatal Frame III: The Tormented (US) / Project Zero III (EU) | Adventure | NATIVE-480P | SLUS-21244 2ADBA7BC(FB) | yes | SLES-50821:22E91837 | yes | yes |
| Haunting Ground | Adventure | NATIVE-480P | SLUS-21075 901AAC09 | yes |  |  |  |
| Resident Evil - Code: Veronica X | Adventure | TIER-D | SLUS-20184 24036809 | unknown | SLES-50306:6EA9DDA9 SLES-50306:A5434CCF |  |  |
| Resident Evil 4 | Adventure | NATIVE-480P | SLUS-21134 013E349D | yes |  |  |  |
| Rule of Rose | Adventure | OPEN | SLUS-21448 F3FD313E | unknown |  |  |  |
| Shadow of Destiny / Memories | Adventure | OPEN | SLUS-20146 F14DFE0A | unknown |  |  |  |
| Silent Hill 2: Director's Cut | Adventure | OPEN | SLUS-20228 8E8E384B FE06A030(FB) | unknown |  | yes | yes |
| Silent Hill 3 | Adventure | OPEN | SLUS-20622 2498951B(F) | unknown |  | yes |  |
| The Thing | Adventure | OPEN | SLUS-20371 1B9D49F3(F) 3F0DC9DC(F) | unknown |  | yes |  |
| Def Jam: Fight for NY | Beat 'em up | OPEN | SLUS-21004 4538436F | unknown |  |  |  |
| Final Fight: Streetwise | Beat 'em up | OPEN | SLUS-21238 7985D894 | unknown |  |  |  |
| God of War | Beat 'em up | OPEN | SCUS-97399 D6385328<br>SCUS-97467 56EC00B5 DF3A5A5C | listed, unconfirmed |  |  |  |
| God Hand | Beat 'em up | DEINT-DONE | SLUS-21503 6FB69282(D) | unknown |  |  |  |
| God of War II | Beat 'em up | OPEN | SCUS-97481 2F123FD8 | listed, unconfirmed |  |  |  |
| Mortal Kombat: Shaolin Monks | Beat 'em up | OPEN | SLUS-21087 455DD546 | unknown |  |  |  |
| The Bouncer | Beat 'em up | DEINT-DONE | SLUS-20069 FEE23E8F(D) | unknown |  |  |  |
| The Red Star | Beat 'em up | OPEN | SLUS-20885 ED4BF0D3 | no |  |  |  |
| The Warriors | Beat 'em up | DEINT-DONE | SLUS-21215 B99A75DE(D) | no | SLES-53443:FA3C1346 |  |  |
| Urban Reign | Beat 'em up | DEINT-DONE | SLUS-21209 BDD9BAAD(D) | yes |  |  |  |
| Bloody Roar 3 | Fighting | DEINT-DONE | SLUS-20212 AA4E5A35(D) | unknown | SLPM-62055:4D6DBB75 SLPM-62055:64328775 |  |  |
| Capcom vs. SNK 2: Mark of the Millenium | Fighting | DEINT-DONE | SLUS-20246 15149318(D) | unknown | SLPM-65047:B54C0319 |  |  |
| Dragon Ball Z: Budokai 3 | Fighting | NATIVE-480P | SLUS-20998 2A4B60EB C97EF0A4<br>SLUS-21123 (no pnach) | yes | SLES-52730:CD787D68 SLES-53346:4E0D7BDE |  |  |
| Fatal Fury: Battle Archives / (volumes 1 and 2) | Fighting | OPEN | SLUS-21537 (no pnach)<br>SLUS-21723 (no pnach) | unknown |  |  |  |
| Fire Pro Wrestling Returns | Fighting | OPEN | SLUS-21702 63435086 | unknown |  |  |  |
| Galactic Wrestling: Featuring Ultimate Muscle | Fighting | OPEN | SLUS-20822 8745F0BA | unknown |  |  |  |
| Guilty Gear XX Accent Core Plus | Fighting | OPEN | SLUS-21847 (no pnach) | listed, unconfirmed |  |  |  |
| Marvel vs. Capcom 2 | Fighting | DEINT-DONE (partial) | SLUS-20486 4D228733(D) 69B2071C | unknown |  |  |  |
| Namco Classic Fighter Collection | Fighting | UNMATCHED |  | unknown |  |  |  |
| Neo Geo Battle Coliseum | Fighting | NATIVE-480P | SLUS-21708 (no pnach) | yes |  |  |  |
| Samurai Shodown Anthology | Fighting | OPEN | SLUS-21629 (no pnach) | unknown |  |  |  |
| SoulCalibur II | Fighting | OPEN | SLUS-20643 (no pnach) | listed, unconfirmed |  |  |  |
| Soulcalibur III | Fighting | NATIVE-480P | SLUS-21216 027C604C | yes | SCES-53312:3BA95B70 SCES-53312:BC5480A3 |  |  |
| Street Fighter Anniversary Collection | Fighting | OPEN | SLUS-20949 (no pnach) | unknown |  |  |  |
| Street Fighter Alpha Anthology | Fighting | OPEN | SLUS-21317 72CE7A78(B) | listed, unconfirmed |  |  | yes |
| Street Fighter EX 3 | Fighting | DEINT-DONE | SLUS-20130 72B3802A(DB) | unknown | SLPS-20003:63642E9F |  | yes |
| Super Dragon Ball Z | Fighting | DEINT-DONE (partial) | SLUS-21442 DE2DF62D(D) FABD7602 | unknown | SLPS-25642:197E9907 |  |  |
| Tekken 5 | Fighting | DEINT-DONE | SLUS-21059 652050D2(D)<br>SLUS-21160 (no pnach) | yes | SCES-53202:1F88BECD SCES-53202:C2D29D42 |  |  |
| Tekken Tag Tournament | Fighting | DEINT-DONE | SLUS-20001 67454C1E(D) E84C9242(D) | unknown | SCES-50001:0DD8941C SCES-50001:D07E8F35 SLPS-20015:06979F19 |  |  |
| The King of Fighters 2006 (US) / The King of Fighters: Maximum Impact 2 | Fighting | OPEN | SLUS-21365 4EE93170 | unknown |  |  |  |
| The King of Fighters Collection: The Orochi Saga | Fighting | OPEN | SLUS-21554 (no pnach) | unknown |  |  |  |
| The King of Fighters '98: Ultimate Match | Fighting | NATIVE-480P | SLUS-21816 (no pnach) | yes |  |  |  |
| The King of Fighters XI | Fighting | NATIVE-480P | SLUS-21687 (no pnach) | yes |  |  |  |
| Virtua Fighter 4: Evolution | Fighting | DEINT-DONE | SLUS-20616 C9DEF513(D) | unknown | SLES-51616:81CA29BE SLPM-65270:AB01411F |  |  |
| War of the Monsters | Fighting | OPEN | SCUS-97197 2EDE12D1<br>SCUS-97260 7CFD0559 | unknown |  |  |  |
| 007: Agent Under Fire | FPS | OPEN | SLUS-20265 79646C72 | unknown |  |  |  |
| 007: Nightfire | FPS | OPEN | SLUS-20579 (no pnach) | unknown |  |  |  |
| Black | FPS | OPEN | SLUS-21376 5C891FF1(FB) | no |  | yes | yes |
| DarkWatch | FPS | DEINT-DONE | SLUS-21042 327053E8(DF) | unknown |  | yes |  |
| Deus Ex: The Conspiracy | FPS | OPEN | SLUS-20111 (no pnach) | unknown |  |  |  |
| Killzone | FPS | DEINT-DONE | SCUS-97402 CAAEC49C(DB)<br>SCUS-97432 (no pnach)<br>SCUS-97517 (no pnach) | no |  |  | yes |
| Red Faction | FPS | OPEN | SLUS-20073 FBF28175 | unknown |  |  |  |
| Red Faction II | FPS | OPEN | SLUS-20442 8E7FF6F8 | unknown |  |  |  |
| TimeSplitters | FPS | DEINT-DONE | SLUS-20090 8966730F(D) B4A004F2(D) | unknown |  |  |  |
| TimeSplitters 2 | FPS | OPEN | SLUS-20314 12532F1C | unknown |  |  |  |
| TimeSplitters: Future Perfect | FPS | OPEN | SLUS-21148 (no pnach) | no |  |  |  |
| XIII | FPS | OPEN | SLUS-20677 FCD97245(F) | unknown |  | yes |  |
| Alien Hominid | Platformer | TIER-D | SLUS-21090 190DF20A | no | SLES-53139:14274DC3 |  |  |
| Ape Escape 2 | Platformer | OPEN | SLUS-20685 BDD9F5E1 | no |  |  |  |
| Ape Escape 3 | Platformer | DEINT-DONE | SCUS-97501 7571AAEE(D)<br>SCUS-97548 (no pnach) | no |  |  |  |
| Castlevania: Curse of Darkness | Platformer | OPEN | SLUS-21168 3A446111 | unknown |  |  |  |
| Castlevania: Lament of Innocence | Platformer | OPEN | SLUS-20733 28270F7D | unknown |  |  |  |
| Contra: Shattered Soldier | Platformer | OPEN | SLUS-20306 582EED0D | unknown |  |  |  |
| Crash Bandicoot: The Wrath of Cortex | Platformer | DEINT-DONE | SLUS-20238 103B5706(D) 5188ABCA(D) | unknown | SLES-50386:35D70452 SLES-50386:3A03D62F |  |  |
| Crash Twinsanity | Platformer | OPEN | SLUS-20909 8CFAB4EA B318AA3C | no |  |  |  |
| Jak and Daxter: The Precursor Legacy | Platformer | DEINT-DONE | SCUS-97124 143976AB(D) 1B3976AB(D) 472E7699(D)<br>SCUS-97170 (no pnach)<br>SCUS-97171 (no pnach) | no | SCES-50361:9C712FF0 |  |  |
| Jak II | Platformer | NATIVE-480P | SCUS-97265 9184AAF1 9E84AAF1<br>SCUS-97273 (no pnach)<br>SCUS-97274 (no pnach)<br>SCUS-97509 (no pnach) | yes |  |  |  |
| Jak 3 | Platformer | NATIVE-480P | SCUS-97330 644CFD03<br>SCUS-97412 (no pnach)<br>SCUS-97516 (no pnach) | yes | SCES-52460:12804727 |  |  |
| Klonoa 2: Lunatea's Veil | Platformer | DEINT-DONE | SLUS-20151 2F56CBC9(D) | unknown |  |  |  |
| Maximo: Ghosts to Glory | Platformer | DEINT-DONE | SLUS-20017 0958556B(D) | unknown |  |  |  |
| Maximo vs. Army of Zin | Platformer | DEINT-DONE | SLUS-20722 8CF7CBC0(D) | unknown |  |  |  |
| Mega Man Anniversary Collection | Platformer | OPEN | SLUS-20833 (no pnach) | unknown |  |  |  |
| Mega Man X Collection | Platformer | OPEN | SLUS-21370 (no pnach) | no |  |  |  |
| Mega Man X 8 | Platformer | NATIVE-480P | SLUS-20960 196DF4E5 | yes |  |  |  |
| Metal Slug Anthology | Platformer | OPEN | SLUS-21550 (no pnach) | unknown |  |  |  |
| Nightshade | Platformer | DEINT-DONE | SLUS-20810 519E816B(D) | unknown |  |  |  |
| Psychonauts | Platformer | OPEN | SLUS-21120 2373FD16(F) | unknown |  | yes |  |
| Rayman 2: Revolution | Platformer | OPEN | SLUS-20138 D2F77DF2(F) | unknown |  | yes |  |
| Rayman 3: Hoodlum Havoc | Platformer | DEINT-DONE | SLUS-20601 146F67E5(D) | yes | SLKA-25078:90E927F3 |  |  |
| Shinobi | Platformer | DEINT-DONE | SLUS-20459 BFCC3E7E(D) | unknown |  |  |  |
| Sly Cooper and the Thievius Raccoonus | Platformer | DEINT-DONE | SCUS-97198 C77AF2CA(DB)<br>SCUS-97210 EF7F0CE6(DB) | unknown |  |  | yes |
| Sly 2: Band of Thieves | Platformer | DEINT-DONE | SCUS-97316 07652DD9(DB) FDA1CBF6(DB)<br>SCUS-97415 5B93397F(DB)<br>SCUS-97457 B3E892E4(D)<br>SCUS-97519 (no pnach) | unknown | SCES-52529:15DD1F6F SCES-52529:FDA1CBF6 |  | yes |
| Sly 3: Honor Among Thieves | Platformer | DEINT-DONE | SCUS-97464 8BC95883(DB)<br>SCUS-97484 3130A4D3(DB)<br>SCUS-97527 35CCFA60(DB) | unknown |  |  | yes |
| Sonic Unleashed | Platformer | NATIVE-480P | SLUS-21846 FB236A46(F) | yes | SLES-55380:8C913264 | yes |  |
| Splatter Master | Platformer | OPEN | SLES-53368 1D8EE3CF | unknown |  |  |  |
| SpongeBob SquarePants: Battle for Bikini Bottom | Platformer | OPEN | SLUS-20680 FD7EEE96 | unknown |  |  |  |
| Stretch Panic (US) / Freak Out (EU) / Hippa Linda (JP) | Platformer | OPEN | SLUS-20182 854D5885 | unknown |  |  |  |
| Viewtiful Joe | Platformer | OPEN | SLUS-20951 080D5356 | unknown |  |  |  |
| Viewtiful Joe 2 | Platformer | OPEN | SLUS-20939 1B7DA82A | unknown |  |  |  |
| Whiplash | Platformer | OPEN | SLUS-20684 4D22DB95 | unknown |  |  |  |
| Lumines Plus | Puzzle | OPEN | SLUS-21553 (no pnach) | unknown |  |  |  |
| The Adventures of Cookie & Cream (US) / Kuri Kuri Mix (JP/EU) | Puzzle | DEINT-DONE | SLUS-20170 348CEAC4(D) | unknown |  |  |  |
| Burnout 3: Takedown | Racing | DEINT-DONE | SLUS-21050 BEBF8793(DFB) | yes | SLES-52584:75BECC18 | yes | yes |
| Gran Turismo 4 | Racing | DEINT-DONE | SCUS-90682 (no pnach)<br>SCUS-97328 77E61C8A(D)<br>SCUS-97436 32A1C752(D)<br>SCUS-97563 (no pnach) | yes | SCES-51719:44A61C8F |  |  |
| IGPX: Immortal Grand Prix | Racing | OPEN | SLUS-21430 F23579D9 | unknown |  |  |  |
| Jak X : Combat Racing | Racing | NATIVE-480P | SCUS-97429 (no pnach)<br>SCUS-97486 (no pnach)<br>SCUS-97488 (no pnach)<br>SCUS-97574 (no pnach) | yes |  |  |  |
| Kinetica | Racing | DEINT-DONE | SCUS-97132 D39C08F5(D)<br>SCUS-97161 (no pnach) | unknown |  |  |  |
| OutRun 2006: Coast 2 Coast | Racing | NATIVE-480P | SLUS-21274 (no pnach) | yes |  |  |  |
| Test Drive: Eve of Destruction | Racing | OPEN | SLUS-20910 5D0244D3 | unknown |  |  |  |
| Tokyo Road Race (EU) / Battle Gear 2 (JP) | Racing | OPEN | SLES-50954 F880239B | unknown |  |  |  |
| Tokyo Xtreme Racer 3 (US) / Shutokō Battle 01 (JP) | Racing | DEINT-DONE | SLUS-20831 0F932D81(D) 0F9348FF(D) | unknown | SLPM-65308:DD70E38F |  |  |
| Ar Tonelico: Melody of Elemia | RPG | DEINT-DONE | SLUS-21445 4437F4B1(D) | unknown |  |  |  |
| Ar Tonelico 2: Melody of Metafalica | RPG | OPEN | SLUS-21788 F95F37EE | unknown |  |  |  |
| Atelier Iris: Eternal Mana | RPG | OPEN | SLUS-21113 E3981DBB | unknown |  |  |  |
| Atelier Iris 2: The Azoth of Destiny | RPG | OPEN | SLUS-21327 9AC65D6A | unknown |  |  |  |
| Atelier Iris 3: Grand Phantasm | RPG | OPEN | SLUS-21564 4CCC9212 | unknown |  |  |  |
| Baldur's Gate: Dark Alliance | RPG | OPEN | SLUS-20035 773A8DAB | unknown |  |  |  |
| Baldur's Gate: Dark Alliance II | RPG | OPEN | SLUS-20675 B0859096 | unknown |  |  |  |
| Breath of Fire: Dragon Quarter | RPG | DEINT-DONE | SLUS-20499 588CC41B(D) | unknown |  |  |  |
| Champions of Norrath: Realms of EverQuest | RPG | DEINT-DONE | SLUS-20565 90E66BC5(D) | unknown | SLES-52325:75D86958 |  |  |
| Chaos Wars | RPG | OPEN | SLUS-21722 56AD161B | unknown |  |  |  |
| Crimson Tears | RPG | REPO | SLUS-20948 D31904C2(D) | yes |  |  |  |
| Dark Cloud | RPG | DEINT-DONE | SCUS-97111 A5C05C78(D)<br>SCUS-97152 (no pnach) | unknown | SCES-50295:0BAA8DD8 |  |  |
| Dark Cloud 2 (US) / Dark Chronicle (EU) | RPG | OPEN | SCUS-97213 1DF41F33(B)<br>SCUS-97229 (no pnach) | unknown |  |  | yes |
| Disgaea: Hour of Darkness | RPG | OPEN | SLUS-20666 4D2CAC9D | no |  |  |  |
| Disgaea 2: Cursed Memories | RPG | OPEN | SLUS-21397 951555A0 | unknown |  |  |  |
| Dragon Quest VIII: The Journey of the Cursed King | RPG | OPEN | SLUS-21207 (no pnach) | no |  |  |  |
| Drakengard | RPG | DEINT-DONE | SLUS-20732 9679D44C(D) | unknown | SLES-52322:79585776 |  |  |
| Final Fantasy X / International | RPG | TIER-D | SLUS-20312 BB3D833A | unknown | SCES-50490:A39517AB SCES-50492:941BB7D9 |  |  |
| Final Fantasy X-2 / International + Last Mission | RPG | OPEN | SLUS-20672 48FE0C71 | unknown |  |  |  |
| Final Fantasy XII / International Zodiac Job System | RPG | OPEN | SLUS-20963 0779FBDB<br>SLUS-21475 (no pnach) | no |  |  |  |
| Forever Kingdom | RPG | DEINT-DONE | SLUS-20343 E3C4037C(D) | unknown |  |  |  |
| Front Mission 4 | RPG | OPEN | SLUS-20888 EB3AC800 | unknown |  |  |  |
| Gladius | RPG | OPEN | SLUS-20490 78ADCFB9 | unknown |  |  |  |
| Grandia II | RPG | OPEN | SLUS-20194 160076FE | unknown |  |  |  |
| .hack://IMOQ / (quadrilogy) | RPG | OPEN | SLUS-20267 38A894C6<br>SLUS-20562 43048DD4<br>SLUS-20563 0001171A<br>SLUS-20564 DF05D056 | unknown |  |  |  |
| .hack://G.U. / (trilogy) | RPG | OPEN | SLUS-21258 89E303FC<br>SLUS-21488 0F26BB77<br>SLUS-21489 6364A466 | unknown |  |  |  |
| Kingdom Hearts / Final Mix | RPG | OPEN | SLUS-20370 0F6B6315(FB) | unknown |  | yes | yes |
| Kingdom Hearts II / Final Mix+ | RPG | OPEN | SLUS-21005 DA0535FD(FB) | unknown |  | yes | yes |
| Kingdom Hearts Re:Chain of Memories | RPG | OPEN | SLUS-21799 A287DF74(F) | unknown |  | yes |  |
| Makai Kingdom: Chronicles of the Sacred Tome | RPG | OPEN | SLUS-21170 121AFAF5 | unknown |  |  |  |
| Mana-Khemia: Alchemists of Al-Revis | RPG | OPEN | SLUS-21735 77B0236F | unknown |  |  |  |
| Mana-Khemia 2: Fall of Alchemy | RPG | OPEN | SLUS-21890 433951E7 | unknown |  |  |  |
| Mega Man X: Command Mission | RPG | NATIVE-480P | SLUS-20903 C3553F46 | yes |  |  |  |
| Monster Hunter | RPG | OPEN | SLUS-20896 0EF16A99 | unknown |  |  |  |
| Monster Rancher 4 | RPG | OPEN | SLUS-20702 0EF3697B | unknown |  |  |  |
| Monster Rancher EVO | RPG | OPEN | SLUS-21330 BDFB1507 | unknown |  |  |  |
| Odin Sphere | RPG | OPEN | SLUS-21577 (no pnach) | unknown |  |  |  |
| Okage: Shadow King | RPG | DEINT-DONE | SCUS-97129 E0426FC6(D) | unknown |  |  |  |
| Phantom Brave | RPG | OPEN | SLUS-20955 B43000A1 | no |  |  |  |
| Radiata Stories | RPG | NATIVE-480P | SLUS-21262 (no pnach) | yes |  |  |  |
| Rogue Galaxy | RPG | OPEN | SCUS-97490 0643F90C<br>SCUS-97572 (no pnach) | unknown |  |  |  |
| Romancing SaGa | RPG | OPEN | SLUS-21263 239CF68A | unknown |  |  |  |
| Shadow Hearts | RPG | DEINT-DONE | SLUS-20347 8BE3D7B2(D) | unknown |  |  |  |
| Shadow Hearts: Covenant / Director's Cut | RPG | OPEN | SLUS-21041 F3BDB2E6(F)<br>SLUS-21044 F3BDB2E6 | unknown |  | yes |  |
| Shadow Hearts: From the New World | RPG | OPEN | SLUS-21326 C3D28EB9 | unknown |  |  |  |
| Shining Force EXA | RPG | OPEN | SLUS-21567 C3F67CAF | unknown |  |  |  |
| Shin Megami Tensei: Devil Summoner - Raidou Kuzunoha vs. The Soulless Army | RPG | OPEN | SLUS-21431 BD9EAA7A | unknown |  |  |  |
| Shin Megami Tensei: Devil Summoner 2 - Raidou Kuzunoha vs. King Abaddon | RPG | OPEN | SLUS-21845 7FAE77BE<br>SLUS-21897 (no pnach) | unknown |  |  |  |
| Shin Megami Tensei: Digital Devil Saga | RPG | DEINT-DONE | SLUS-20974 D7273511(DB) | unknown |  |  | yes |
| Shin Megami Tensei: Digital Devil Saga 2 | RPG | DEINT-DONE | SLUS-21152 D382C164(DB) | unknown |  |  | yes |
| Shin Megami Tensei: Nocturne (US) / Shin Megami Tensei: Lucifer's Call (EU) | RPG | TIER-D | SLUS-20911 E8FCF8EC F0A31EE3 | unknown | SLES-53363:AE0DE7B7 |  |  |
| Shin Megami Tensei: Persona 3 FES | RPG | DEINT-DONE (partial) | SLUS-21621 0033A2C2(D) 060D795D(D) 1D1F5BA9(D) 1EA75934(D) 94A82AAA(D) 970A82A2 97102837(D) | unknown |  |  |  |
| Shin Megami Tensei: Persona 4 | RPG | OPEN | SLUS-21782 DE61647A DEDC3B71 | unknown |  |  |  |
| Soul Nomad & the World Eaters | RPG | OPEN | SLUS-21603 1F159541 | unknown |  |  |  |
| Star Ocean: Till the End of Time | RPG | NATIVE-480P | SLUS-20488 (no pnach)<br>SLUS-20891 (no pnach) | yes |  |  |  |
| Suikoden III | RPG | OPEN | SLUS-20387 5F3DD929 | unknown |  |  |  |
| Suikoden V | RPG | OPEN | SLUS-21291 BCD0B7CD | unknown |  |  |  |
| Tales of Legendia | RPG | DEINT-DONE | SLUS-21201 43AB7214(D) | unknown | SLPS-25533:1F8640E0 |  |  |
| Tales of the Abyss | RPG | OPEN | SLUS-21386 045D77E9 14FE77F7 A616A6C2 B6B5A6DC | unknown |  |  |  |
| The Sword of Etheria | RPG | REPO | SLES-53768 88E95888 | unknown |  |  |  |
| Valkyrie Profile 2: Silmeria | RPG | NATIVE-480P | SLUS-21452 (no pnach) | yes |  |  |  |
| Wild ARMs 3 | RPG | OPEN | SCUS-97203 06441001<br>SCUS-97224 (no pnach) | unknown |  |  |  |
| Xenosaga Episode I: Der Wille zur Macht | RPG | OPEN | SLUS-20469 6D1276AB | unknown |  |  |  |
| Xenosaga Episode II: Jenseits von Gut und Böse | RPG | OPEN | SLUS-20892 BBBAAF63 EB39ABEC<br>SLUS-21133 BBBAAF63 EB39ABEC | unknown |  |  |  |
| Xenosaga Episode III: Also sprach Zarathustra | RPG | OPEN | SLUS-21389 2088950A<br>SLUS-21417 2088950A | unknown |  |  |  |
| X-Men Legends | RPG | TIER-D | SLUS-20656 CE6A63BF | unknown | SLES-52624:69094734 |  |  |
| X-Men Legends II: Rise of Apocalypse | RPG | TIER-D | SLUS-21138 0E707DA4 | unknown | SLES-53377:912C8E55 |  |  |
| Dragon Blaze (EU) | Shoot 'em up | OPEN | SLES-53874 (no pnach) | unknown |  |  |  |
| Gradius III & IV | Shoot 'em up | OPEN | SLUS-20040 (no pnach) | no |  |  |  |
| Gradius V | Shoot 'em up | OPEN | SLUS-20712 CDA95971 | unknown |  |  |  |
| Homura | Shoot 'em up | OPEN | SLES-53964 (no pnach) | unknown |  |  |  |
| R-Type Final | Shoot 'em up | OPEN | SLUS-20780 85E994DD | unknown |  |  |  |
| Silent Scope | Shoot 'em up | OPEN | SLUS-20078 53CB5976 | unknown |  |  |  |
| Ace Combat 04: / Shattered Skies (US) / Distant Thunder (EU) | Simulation | DEINT-DONE | SLUS-20152 A32F7CD0(D) | no |  |  |  |
| Ace Combat 5: / The Unsung War (US) / Squadron Leader (EU) | Simulation | DEINT-DONE | SLUS-20851 39B574F0(D) | no |  |  |  |
| Ace Combat Zero: The Belkan War | Simulation | DEINT-DONE | SLUS-21346 65729657(D) | no |  |  |  |
| BCV: Battle Construction Vehicles | Simulation | OPEN | SLES-51714 (no pnach) | unknown |  |  |  |
| Jurassic Park: Operation Genesis | Simulation | OPEN | SLUS-20380 A99B8FE7(F) | unknown |  | yes |  |
| SkyGunner | Simulation | DEINT-DONE | SLUS-20384 A9461CB2(D) | unknown |  |  |  |
| Sky Odyssey | Simulation | OPEN | SLUS-20134 CD213E68 | unknown |  |  |  |
| Twisted Metal: Black | Simulation | DEINT-DONE (partial) | SCUS-97101 073696DA(D)<br>SCUS-97164 CFCBDF0C<br>SCUS-97179 (no pnach) | unknown |  |  |  |
| Disney Golf | Sports | OPEN | SLUS-20532 79741C1B | unknown |  |  |  |
| SSX Tricky | Sports | OPEN | SLUS-20326 (no pnach) | no |  |  |  |
| SSX3 | Sports | OPEN | SLUS-20772 08FFF00D | unknown |  |  |  |
| Tony Hawk's Pro Skater 3 | Sports | OPEN | SLUS-20013 EE2B2BAF F77E2FB5 | unknown |  |  |  |
| Tony Hawk's Pro Skater 4 | Sports | OPEN | SLUS-20504 (no pnach) | no |  |  |  |
| Tony Hawk's Underground | Sports | OPEN | SLUS-20731 (no pnach) | no |  |  |  |
| Tony Hawk's Underground 2 | Sports | OPEN | SLUS-20965 (no pnach) | no |  |  |  |
| Tony Hawk's American Wasteland | Sports | NATIVE-480P | SLUS-21208 21278F5B(B)<br>SLUS-21295 21278F5B(B) | yes |  |  | yes |
| Headhunter | Stealth | OPEN | SLUS-20416 6B64AB86 | unknown |  |  |  |
| Hitman: Blood Money | Stealth | NATIVE-480P | SLUS-21108 13E1AD6A(F) | yes |  | yes |  |
| Metal Gear Solid 2: Substance | Stealth | OPEN | SLUS-20554 93B9A720 C539049D(F) | unknown |  | yes |  |
| Metal Gear Solid 3: Subsistence | Stealth | OPEN | SLUS-21243 01B2FA7F<br>SLUS-21359 053D2239(F)<br>SLUS-21360 (no pnach) | unknown |  | yes |  |
| Mister Mosquito | Stealth | OPEN | SLUS-20375 33D2AA72 | unknown |  |  |  |
| Second Sight | Stealth | OPEN | SLUS-21033 16E3BE78 | unknown |  |  |  |
| Tenchu: Wrath of Heaven | Stealth | DEINT-DONE | SLUS-20397 767E383D(D) | yes | SLES-51400:7FA1510D |  |  |
| GrimGrimoire | Strategy | OPEN | SLUS-21604 8817166C | unknown |  |  |  |
| Mobile Suit Gundam: Zeonic Front | Strategy | OPEN | SLUS-20233 23FFE14B | unknown |  |  |  |
| 007: Everything or Nothing | TPS | OPEN | SLUS-20751 6848699B | unknown |  |  |  |
| 10,000 Bullets | TPS | OPEN | SLES-53481 EF97EC8F | unknown |  |  |  |
| Armored Core: Nexus | TPS | DEINT-DONE | SLUS-20986 7E5F690C(DB)<br>SLUS-21079 7E5F690C(DB) | unknown | SLES-82036:F3A5EC6F SLES-82037:F3A5EC6F SLPS-25338:26D1C561 SLPS-25339:26D1C561 |  | yes |
| Chikyuu Boueigun (JP) / Monster Attack (EU) | TPS | OPEN | SLES-51856 0AA95F54 | unknown |  |  |  |
| Chikyuu Boueigun 2 (JP) / Global Defence Force (EU) | TPS | REPO | SLES-54464 DD35AC9F<br>SLES-54589 (no pnach) | unknown |  |  |  |
| Destroy All Humans! | TPS | NATIVE-480P | SLUS-20945 67A29886(F) | yes |  | yes |  |
| Enter The Matrix | TPS | OPEN | SLUS-20454 2A968F81 | unknown |  |  |  |
| Fur Fighters: Viggo's Revenge | TPS | OPEN | SLUS-20088 (no pnach) | no |  |  |  |
| GunGrave | TPS | DEINT-DONE | SLUS-20493 BF5D9AEC(D) | unknown | SLPM-65153:C3B568F8 |  |  |
| GunGrave: OverDose | TPS | OPEN | SLUS-21020 83C9749E(F) | unknown |  | yes |  |
| Kill Switch | TPS | NATIVE-480P | SLUS-20706 ECC849C5 | yes | SCES-52124:91A65EAE |  |  |
| Ratchet & Clank | TPS | OPEN | SCUS-97199 CE4933D0<br>SCUS-97209 (no pnach)<br>SCUS-97240 (no pnach) | unknown |  |  |  |
| Ratchet & Clank: Going Commando/Locked and Loaded | TPS | NATIVE-480P | SCUS-97268 38996035 B3A71D10<br>SCUS-97322 (no pnach)<br>SCUS-97323 (no pnach)<br>SCUS-97374 (no pnach)<br>SCUS-97381 (no pnach)<br>SCUS-97513 (no pnach) | yes |  |  |  |
| Ratchet & Clank: Up Your Arsenal! | TPS | NATIVE-480P | SCUS-97353 45FE0CC4 49536F3F(F)<br>SCUS-97411 (no pnach)<br>SCUS-97413 (no pnach)<br>SCUS-97518 (no pnach) | yes |  | yes |  |
| Ratchet: Deadlocked | TPS | NATIVE-480P | SCUS-97465 9BFBCD42(F)<br>SCUS-97485 (no pnach)<br>SCUS-97487 (no pnach) | yes |  | yes |  |
| Star Wars Battlefront II | TPS | OPEN | SLUS-21240 02F4B541(FB) 249540F3(FB) 62390B9E | unknown |  | yes | yes |
| Syphon Filter: Dark Mirror | TPS | NATIVE-480P | SCUS-97362 3D92EAFF<br>SCUS-97620 (no pnach) | yes | SCES-54794:EF9459D0 |  |  |
| The Punisher | TPS | DEINT-DONE (partial) | SLUS-20864 BC204346 BC2043A7(D) | unknown | SLES-53049:5AC5D875 SLES-53203:C493D552 |  |  |
| Capcom Classics Collection / (volumes 1 and 2) | Other | NATIVE-480P | SLUS-21316 (no pnach)<br>SLUS-21473 (no pnach) | yes |  |  |  |
| Dokapon Kingdom | Other | OPEN | SLUS-21778 CDE9832D | unknown |  |  |  |
| Gitaroo Man | Other | DEINT-DONE | SLUS-20294 7130C553(D) | unknown |  |  |  |
| Katamari Damacy | Other | OPEN | SLUS-21008 FA7E3081 | unknown |  |  |  |
| Midway Arcade Treasures / (volumes 1, 2, 3) | Other | OPEN | SLUS-20801 (no pnach)<br>SLUS-20997 (no pnach)<br>SLUS-21094 B843EAFB | unknown |  |  |  |
| Namco Museum: 50th Anniversary | Other | OPEN | SLUS-21164 (no pnach) | unknown |  |  |  |
| PaRappa the Rapper 2 | Other | DEINT-DONE | SCUS-97167 2D368982(D) | unknown | SCES-50408:326339BF |  |  |
| Sega Classics Collection | Other | OPEN | SLUS-21009 497DBC3C | unknown |  |  |  |
| Sonic Gems Collection | Other | OPEN | SLES-53350 4A198252(F) 82DB1E89(F) | unknown |  | yes |  |
| Sonic Mega Collection Plus | Other | OPEN | SLUS-20917 (no pnach) | listed, unconfirmed |  |  |  |
| Taito Legends / (volumes 1 and 2) | Other | DEINT-DONE | SLUS-21122 (no pnach)<br>SLUS-21349 82651334(D) | unknown |  |  |  |
| We ♥ Katamari | Other | OPEN | SLUS-21230 337B927C | unknown |  |  |  |
| Beatmania IIDX series | Japan | UNMATCHED |  | no |  |  |  |
| Berserk: Millennium Falcon Hen Seima Senki no Shou | Japan | OPEN | SLPM-65686 (no pnach)<br>SLPM-65688 9685E636 | unknown |  |  |  |
| Bust-A-Move: Dance Summit 2001 | Japan | OPEN | SLPM-62029 F782A513 F881A604 | unknown |  |  |  |
| ChainDive | Japan | OPEN | SCPS-15054 (no pnach)<br>SCAJ-20043 (no pnach) | unknown |  |  |  |
| Cho Aniki: Seinaru Protein Densetsu | Japan | OPEN | SLPM-62360 (no pnach)<br>SLPM-62403 (no pnach) | unknown |  |  |  |
| Front Mission 5: Scars of the War | Japan | OPEN | SLPM-66205 2615F542 F60255AC<br>SLPM-66421 (no pnach)<br>SCAJ-20166 (no pnach) | unknown |  |  |  |
| Garouden Breakblow: Fist or Twist | Japan | OPEN | SLPS-25747 246BD411 | unknown |  |  |  |
| Ibara | Japan | OPEN | SLPM-66301 (no pnach)<br>TCPS-10131 (no pnach) | unknown |  |  |  |
| Initial D Special Stage | Japan | OPEN | SLPM-60205 (no pnach)<br>SLPM-65268 A62EBC2C B9FA5764<br>SLPM-68509 (no pnach)<br>SLPM-74420 (no pnach)<br>SCAJ-25008 (no pnach)<br>SLAJ-25008 (no pnach) | unknown |  |  |  |
| NiGHTS Into Dreams... | Japan | OPEN | SLPM-66926 (no pnach) | yes |  |  |  |
| Pop'n Music series | Japan | UNMATCHED |  | unknown |  |  |  |
| Saru! Getchu! Million Monkeys | Japan | OPEN | SCPS-15115 8EFDBAEB<br>SCPS-19325 (no pnach) | unknown |  |  |  |
| Sega Ages 2500 | Japan | UNMATCHED |  | unknown |  |  |  |
| Sega Ages 2500: Fantasy Zone - Complete Collection | Japan | OPEN | SLPM-62780 (no pnach) | unknown |  |  |  |
| Sega Ages 2500: Galaxy Force II - Special Extended Edition | Japan | OPEN | SLPM-62766 (no pnach) | unknown |  |  |  |
| Sega Ages 2500: Last Bronx | Japan | OPEN | SLPM-62687 80E809D0 | yes |  |  |  |
| Sega Ages 2500: Phantasy Star Generation 1 | Japan | OPEN | SLPM-62362 (no pnach)<br>SLPM-62367 (no pnach)<br>SLPM-62666 (no pnach) | unknown |  |  |  |
| Sega Ages 2500: Phantasy Star Generation 2 | Japan | OPEN | SLPM-62553 (no pnach) | unknown |  |  |  |
| The King of Fighters '94 Re-Bout | Japan | DEINT-DONE | SLPS-25448 E74F7C39(D)<br>SLPS-25449 (no pnach) | yes |  |  |  |
| The King of Fighters 2002: Unlimited Match (Tougeki ver.) | Japan | OPEN | SLPS-25915 (no pnach)<br>SLKA-25457 (no pnach) | yes |  |  |  |
| Thunder Force VI | Japan | OPEN | SLPM-55096 B5C43B61 | no |  |  |  |
