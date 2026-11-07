# OpenTTD 3DS Revival

Build a transport empire on your Nintendo 3DS. This project continues
[EnergeticBark’s OpenTTD-3DS port](https://github.com/EnergeticBark/OpenTTD-3DS),
with a focus on making the game more comfortable to play across both screens.

It runs **OpenTTD 0.7.0** and targets the original **Nintendo 3DS and 3DS XL**.
The revival keeps that engine and builds on the original port with new menus,
controls, audio and stability fixes. You can also read the
[original port README](docs/revival/UPSTREAM-README.md) for its history.

## What’s working

The current playable beta is
[`r3r`](https://github.com/delayedflight/OpenTTD-3DS-Revival/tree/revival-r3r-beta).
It includes:

- The map on the upper screen, with native menus on the touchscreen and the
  option to move menus to the upper screen.
- Separate map, construction and pointer controls.
- A train depot and purchase window that can share the two screens, with
  vehicle counts and wagon dragging.
- Streamed WAV music, autoplay and OpenSFX sound effects.
- Stability fixes, including a graphics threading repair in r3r.

Initial hardware feedback has been positive, with no crashes reported so far on
r3r, and the beta is ready for wider playtesting. That feedback does not yet
cover a documented long session or every feature. Train-depot interactions,
music autoplay, sound quality and longer games still need more testing on real
hardware. The [beta checklist](docs/revival/BETA-TESTING.md) is a good place to start
if you’d like to help.

Networking is disabled, and AI behaviour may still be unreliable. We haven’t
established a safe maximum map size or measured performance on the console.
For known issues and the evidence behind the fixes, see [STATUS.md](STATUS.md)
and the [graphics repair notes](docs/revival/GRAPHICS-QUEUE-VALIDATION.md).

## Installing or updating

**There isn’t a downloadable build on GitHub yet.** The beta source is public,
but the prepared update and source packages are currently kept locally by the
project. This repository does not include everything needed for a fresh install.

The executable update needs a 3DS homebrew launcher and an existing working r3
installation, including its graphics, language files and converted OpenSFX bank.
WAV music is optional. If you’re starting from scratch, you’ll need compatible
base assets separately; instructions for modern OpenTTD may not apply to this
0.7.0 port.

If you already have the beta update:

1. Back up your game folder, including the old executable, configuration and saves.
2. Replace **only** `/3ds/openttd-revival-r3/openttd-revival-r3.3dsx` with the
   beta executable.
3. Keep your `data/`, `gm/` and `lang/` folders, configuration and saves.
   **Don’t replace the whole data folder with the update.**
4. Try a copy of your save before continuing an important game.

The [beta checklist](docs/revival/BETA-TESTING.md) includes the executable’s
checksum so you can identify the build. Private or commercial WAV soundtracks
and original Transport Tycoon Deluxe assets must not be redistributed.

## Controls

Use the touchscreen for the lower menus. In normal map mode, the Circle Pad
scrolls the map and L/R zoom in and out. X or Select switches construction mode.
Keep an eye on the on-screen labels: some buttons change roles with the mode.

Upper-screen menus use a pointer. When the train depot is above and the shop is
below, X/Y/Select switches between depot control and shopping. In depot control,
the Circle Pad moves the pointer, A/L clicks or holds, and D-pad up/down scrolls.
The [architecture notes](ARCHITECTURE.md#rendering-ui-and-input) explain how the
screen and input modes fit together.

## Building from source

Install and start Docker Desktop, then run this from the repository folder:

```sh
bash environment/build.command
```

The build compiles both the modified SDL library and the game. It leaves the
source untouched and puts the results in `builds/repair-r3r/`, with logs in
`logs/`. Setting up the Docker image and toolchain needs an internet connection;
the game itself is compiled with networking disabled. You’ll still need to
supply the base assets and any optional music separately.

See the [Docker recipe](environment/Dockerfile),
[SDL source and patch notes](environment/vendor/README.md) and
[beta build record](docs/revival/BUILD-r3r.json) for details. The toolchain versions
are recorded, but a rebuild is not guaranteed to produce an identical executable.

## Testing and reporting problems

Useful reports tell us which build you ran, which console and launcher/CFW you
used, how long you played, and what happened. Include the map size, the action
that triggered the problem, what you expected, and whether music was playing.
The [reporting checklist](docs/revival/BETA-TESTING.md#report-failures-usefully)
explains which logs and crash dumps to keep.

The fork’s public issue tracker is currently disabled. If you’re already testing
with the project, use your existing contact to share reports. There isn’t a public
reporting channel yet. Check attachments for private information before sharing;
a copied save can help, but don’t worry if the crash happened before you could save.

## Contributing

Start with [AGENTS.md](AGENTS.md) and [STATUS.md](STATUS.md). For more detail, see:

- [Architecture](ARCHITECTURE.md) — how the port works.
- [Benchmarks and testing](BENCHMARKS.md) — measurements and test conditions.
- [Maintenance and releases](docs/revival/PROJECT-ORGANISATION.md#documentation-and-release-maintenance)
  — how to group changes and prepare meaningful beta milestones.
- [Release registry](docs/revival/RELEASES.json) — the history of the saved source
  snapshots and beta builds.

The 21 recovered snapshot tags and current beta tag preserve the project’s
history; they aren’t published GitHub Releases. Existing history and tags stay intact.

## Credits and licenses

Thanks to EnergeticBark for the original 3DS port, the upstream OpenTTD developers,
and the OpenGFX, OpenSFX, SDL and devkitPro contributors whose work makes this possible.

- Game source: GNU GPLv2. See [COPYING](COPYING) and the
  [OpenTTD documentation](readme.openttd).
- Modified SDL: LGPL 2.1-or-later. See its [license](environment/vendor/SDL-COPYING.txt)
  and [source and modification notices](environment/vendor/README.md).
- Converted OpenSFX collection: CC BY-SA 3.0. Keep the
  [conversion notice](docs/revival/OPENSFX-CONVERSION.txt),
  [credits](docs/revival/OPENSFX-CREDITS.txt) and
  [licenses](docs/revival/OPENSFX-LICENSE.txt) with the bank when redistributing it.

Graphics, music and other third-party assets keep their own licenses and credit
requirements. Please retain the relevant notices when sharing a build.
