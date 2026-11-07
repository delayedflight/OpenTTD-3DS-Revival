# OpenTTD 3DS Revival

A continuation of [EnergeticBark’s OpenTTD-3DS port](https://github.com/EnergeticBark/OpenTTD-3DS),
bringing the transport simulation **OpenTTD 0.7.0** to the original Nintendo
3DS and 3DS XL. The revival focuses on dual-screen controls, usable menus,
audio and stability within the original console’s limits; it retains the legacy
engine. The [original port README](docs/revival/UPSTREAM-README.md) is preserved
as historical documentation.

## Playable beta

The current beta source is tagged
[`revival-r3r-beta`](https://github.com/delayedflight/OpenTTD-3DS-Revival/tree/revival-r3r-beta).
It is approved for wider playtesting after an initial user hardware pass: no
crash reported so far, with session duration and exact coverage unspecified.
Extended hardware testing remains open; this is not a feature-complete release.
[Current status and known issues](STATUS.md) records the evidence and next checks.

Implemented features include:

- An upper-screen map and native lower-screen menus, with optional upper menus.
- Map/construction and upper-pointer input modes, plus paired train depot and
  purchase screens, vehicle counts and wagon dragging.
- Streamed WAV music with autoplay and compatible OpenSFX sound effects.
- Stability repairs, including r3r’s shared graphics lock for SDL texture upload
  and rendering. Host/build and emulator checks pass; extended hardware coverage
  is still needed. See [graphics repair validation](docs/revival/GRAPHICS-QUEUE-VALIDATION.md).

Verification varies by feature. Train-workshop interactions, full-playlist music,
sound quality and longer sessions still need hardware coverage. Networking is
disabled, and healthy AI operation is not promised. **No map size is certified
safe.** Emulator results are not console performance benchmarks. The earlier
r3p ordinary-play crash on a 256×256 map was a graphics-queue panic; RAM exhaustion
was not established.

## Installation and safe updates

**There are currently no downloadable GitHub Release assets or public binary
release listing.** The source tags are public; the selected beta update and
complete source packages are retained locally by the project. This repository
is source and documentation, not a complete fresh installation.

To use the executable update, you need a 3DS homebrew launcher and an existing
working r3 installation with compatible graphics, language files and the converted
OpenSFX bank. WAV music is optional. For a fresh installation, compatible base
assets must be obtained separately; the update alone is insufficient. Modern
OpenTTD asset-installation instructions may not apply to this 0.7.0 port.

1. Back up the existing game folder, executable, configuration and saves.
2. Replace **only** `/3ds/openttd-revival-r3/openttd-revival-r3.3dsx` with the
   matching beta executable.
3. Preserve `data/`, `gm/`, `lang/`, configuration and saves. Do not replace the
   whole data folder with an executable-only update.
4. Test with disposable copies of saves before continuing an important game.

See the [beta checklist](docs/revival/BETA-TESTING.md) for executable identity,
suggested sessions and crash evidence. Do not redistribute private/commercial
WAV soundtracks or original Transport Tycoon Deluxe assets.

## Controls at a glance

Use the touchscreen for lower-screen menus. In normal map mode, the Circle Pad
scrolls the map and L/R zoom. X or Select switches construction control mode;
follow the on-screen mode labels because button roles change with focus.
Optional upper menus use pointer controls. With a paired upper depot and lower
shop, X/Y/Select switches depot control and shopping; the Circle Pad moves the
upper pointer, A/L clicks or holds, and D-pad up/down scrolls.
See [screen ownership and input modes](ARCHITECTURE.md#rendering-ui-and-input)
for the implementation overview.

## Build from source

Install and start Docker Desktop, then run from this checkout:

```sh
bash environment/build.command
```

The contained build rebuilds the modified SDL library and game, mounts source
read-only and writes artifacts to `builds/repair-r3r/` plus logs to `logs/`.
Initial image/toolchain setup needs network access; game compilation runs with
network disabled. See the [recipe](environment/Dockerfile),
[SDL source and patch notices](environment/vendor/README.md) and
[recorded beta provenance](docs/revival/BUILD-r3r.json). Recorded toolchain
inventory supports reproducibility checks; byte-identical rebuilds are not guaranteed.
Base assets and optional music must still be supplied separately.

## Testing, bugs and contributions

The public fork’s issue tracker is currently disabled. Prepare reproducible
reports using the checklist below and share them through your existing project
contact; no public reporting channel is currently advertised here.
Include the tag or executable hash, console model, launcher/CFW, session length,
map size, exact action, expected result and whether audio was active. Follow the
[reporting checklist](docs/revival/BETA-TESTING.md#report-failures-usefully) for
logs and crash dumps. Review attachments for private information before posting.
A save is helpful when available, but is not required if the crash preceded saving.

Contributors should start with [AGENTS.md](AGENTS.md) and [STATUS.md](STATUS.md),
then consult [ARCHITECTURE.md](ARCHITECTURE.md), [BENCHMARKS.md](BENCHMARKS.md)
and the [maintenance/release convention](docs/revival/PROJECT-ORGANISATION.md#documentation-and-release-maintenance).
The [release registry](docs/revival/RELEASES.json) records source provenance;
21 recovered snapshot tags and the current beta tag are not published GitHub
Releases. Existing history and tags are preserved.

## Credits and licenses

Thanks to EnergeticBark for the original 3DS port, the upstream OpenTTD developers,
and the OpenGFX, OpenSFX, SDL and devkitPro contributors whose work supports it.

- Game source: GNU GPLv2; see [COPYING](COPYING) and the retained
  [OpenTTD documentation](readme.openttd).
- Modified SDL: LGPL 2.1-or-later; see its [license](environment/vendor/SDL-COPYING.txt)
  and [source/modification notices](environment/vendor/README.md).
- Converted OpenSFX collection: CC BY-SA 3.0; retain the
  [conversion notice](docs/revival/OPENSFX-CONVERSION.txt),
  [credits](docs/revival/OPENSFX-CREDITS.txt) and
  [licenses](docs/revival/OPENSFX-LICENSE.txt) when redistributing the bank.

Base graphics, music and other third-party assets retain their own licenses and
attribution requirements. Preserve applicable notices when distributing a build.
