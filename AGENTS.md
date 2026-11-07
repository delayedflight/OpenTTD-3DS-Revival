# OpenTTD 3DS Revival — session entry point

Run `git status` first; preserve all existing changes. This is the canonical
checkout (`source/` in the overarching project), branch `revival/main`.
Read [STATUS.md](STATUS.md) to resume; read [ARCHITECTURE.md](ARCHITECTURE.md)
only for affected systems and [BENCHMARKS.md](BENCHMARKS.md) for measurements.
Detailed historical evidence is in `docs/revival/`; do not reread it all by default.

## Build and test

- Engine: OpenTTD 0.7.0; target original 3DS / 3DS XL, not New-3DS-only features.
- Start Docker Desktop; run `bash environment/build.command` from this checkout.
  It mounts source read-only, compiles in `/build`, and writes `builds/repair-r3r/`
  plus `logs/`. The parent-project launcher uses the same source with parent outputs.
- `environment/Dockerfile` pins devkitPro; recorded r3q packages include devkitARM
  r68-1, libctru 2.7.0-1 and 3ds-sdl 1.2.15-19. Initial image/package setup needs
  network; game compilation has network disabled. Full inventory accompanies builds.
- Run existing focused Python tests using host Python 3 and clang++ with sanitizers:
  `python3 docs/revival/tests/train-workspace.py /tmp/ottd-trains` is one example.
  See BENCHMARKS.md for UI, scroll and private-asset audio test commands.
- Host tests extract real functions into mocks; they do not replace complete
  compilation, emulator checks or hardware tests. Match crash addresses to the
  exact executable's ELF. Never resolve using another build's symbols.

## Constraints and precautions

Preserve private saves/dumps/audio outside Git. Never write to device/SD or
original saves; test disposable copies only. Keep existing release tags immutable.
Do not commit, push or publish without user authorization. Historical work/r*-source
copies and release archives are evidence, not active editing locations.

Prefer N3DS-guarded changes preserving other platforms and existing language IDs.
Respect legacy header ordering: stdafx / required type headers before n3ds_ui.h.
Use shared screen ownership helpers for drawing, hit testing and cached scrolling;
paired screens must not acquire conflicting ownership or held-button state.
No disk I/O in the audio callback; preserve worker/lock/shutdown ordering.
Do not remove compiler workarounds or switch SDL software surfaces without
reproducing the faults they guard. No engine upgrade or simulated-world unloading
without explicit scope. Original-console RAM headroom is unmeasured; no map size
is certified safe and a Luma exception alone does not establish out-of-memory.

## Maintenance

Update only affected documentation: STATUS for state/next steps, ARCHITECTURE for
implementation/design changes, BENCHMARKS for actual results and conditions.
Keep detailed logs/validation in docs/revival or local artifacts, linking rather
than duplicating. Record failed approaches that would prevent repeated work.
Keep the historical handover as a navigation/evidence record, not a second status.
