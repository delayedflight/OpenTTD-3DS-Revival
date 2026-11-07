# OpenTTD 3DS Revival

A continuation of [EnergeticBark's OpenTTD-3DS port](https://github.com/EnergeticBark/OpenTTD-3DS),
retaining OpenTTD 0.7.0 for the original Nintendo 3DS / 3DS XL.
The original author's README is preserved below.

**Current beta:** [`revival-r3r-beta`](https://github.com/delayedflight/OpenTTD-3DS-Revival/tree/revival-r3r-beta).
The revival adds an upper-screen map, native lower-screen menus, optional upper
windows, train-depot/purchase screen pairing, streamed WAV music, OpenSFX effects
and stability repairs. The beta has an initial user hardware pass; extended
playtesting is ongoing. No map size is certified safe. Networking and healthy AI
support are not promised. The original TODO list below is historical.

## Start here

- [Current status and known issues](STATUS.md)
- [Beta installation and playtest checklist](docs/revival/BETA-TESTING.md)
- [Architecture](ARCHITECTURE.md) and [measurements/testing](BENCHMARKS.md)
- [Build provenance](docs/revival/BUILD-r3r.json) and [graphics repair validation](docs/revival/GRAPHICS-QUEUE-VALIDATION.md)
- [Contributor/agent entry point](AGENTS.md)

Start Docker Desktop, then run `bash environment/build.command` from this checkout.
The contained recipe rebuilds the modified SDL library and game; outputs go into
builds/repair-r3r/. The source includes SDL's original source/platform patch and
the separate graphics-lock repair. Game code is GPLv2; SDL is LGPL2.1-or-later.
See COPYING and environment/vendor/SDL-COPYING.txt.

This repository contains source and documentation. It does not bundle the private
WAV soundtrack, user saves, crash dumps or a complete console installation. The
beta executable update requires an existing working graphics/language installation;
keep those asset folders when replacing the executable. See the beta checklist.

The branch revival/main retains upstream history plus labelled recovery commits
for 21 saved releases and the committed r3r beta. The recovery commits document
saved snapshots, rather than pretending to be the original implementation timeline.
Use small focused changes and relevant tests; include build/device details in bug
reports, and keep personal evidence out of public source commits.

---

## Original port README (historical)

# OpenTTD port for the 3DS
A port of OpenTTD v0.7.0 to the Nintendo 3DS
## Installation
* Download the latest version of openttd.zip from the releases page.
* Extract its contents to /3ds/ on your SD card.
## Building

I've only tried compiling this on Linux so I'm not sure if it will work on a non-Unix-like OS.
* Install the 3ds-sdl library using (dkp-)pacman
* From the root of the project directory, run:
```bash
./configure --os=N3DS --host $DEVKITARM/bin/arm-none-eabi --enable-static --prefix-dir=$DEVKITPRO --with-sdl --without-png --without-threads --disable-network --disable-unicode --without-libfontconfig --without-zlib --without-libfreetype --without-icu
```
* Type:
```bash
make
```
* Then, in ./bin/ run:
```bash
$DEVKITPRO/tools/bin/3dsxtool openttd openttd.3dsx
```
I don't know really what I'm doing when it come to writing configure files lol. If anyone has advice I'll gladly take it.
## Why 0.7.0 instead of a later version?
Memory restrictions. The later versions I tried would always crash, even with a small map, because they simply wouldn't fit into the application memory of the 3DS. (The OLD 3DS at least. I don't own a NEW model I could test with.)
One of the other reasons I picked 0.7.0 specifically, is it's the version that the DS port uses. This gives me something I can borrow some ideas from.
It also has plenty of the features you would expect from OpenTTD, like OpenGFX support.
## To do
- [x] Resize UI elements to better fit the 3DS's low screen resolution. 
- [ ] Put a viewport on the top screen, right now it's used as a console.
- [ ] Networking support.
- [ ] Fix music.
- [ ] (maybe) Move to a slightly newer version of OpenTTD??????
