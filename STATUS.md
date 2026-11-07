# Current project status

Reviewed against source and existing evidence: 7 November 2026.

## Source and release identity

Selected beta: **r3r**, approved for wider playtesting on 7 November 2026.
Integration branch: `revival/main`; release tag: `revival-r3r-beta`.
The tag identifies committed source; the executable was built before that commit
from the same application/build inputs. Documentation was subsequently updated.
Do not assume a future rebuild is byte-identical.

Beta executable SHA256:
`b99a2027f3c1381986b7fb2507c8ec48dbab2f13c02357d46a702478cd7e2112`.
Matching ELF: parent `builds/repair-r3r/openttd.elf`. See
[build provenance](docs/revival/BUILD-r3r.json) and
[release registry](docs/revival/RELEASES.json).

User reports r3r has not crashed so far and considers the major features working
well enough for other testers. Duration, exact map/actions and extended coverage
were not supplied. This is an initial hardware pass, not long-run certification.

## Implementation and evidence

| Area | Current state | Verification boundary |
|---|---|---|
| Initial AI/pool stability fixes | Implemented; automatic AI-debug popup suppressed | Earlier affected game ran beyond the following year on user's hardware; not proof of healthy AI or all crash causes fixed |
| Upper map, lower UI, native menus, editor/New Game | Implemented | Host/emulator checks and iterative user hardware feedback; not every window/action combination certified |
| WAV streaming and autoplay (r3n/r3o) | Implemented; 22-track mapping complete | Host full-album read and emulator autoplay/track changes pass; user confirmed r3n manual playback, full-album/autoplay hardware coverage pending |
| Sound effects (r3p) | Implemented using converted OpenSFX bank | Parser/mixer concurrency tests and emulator triggers pass; hardware sound quality/balance/stress pending |
| Train workshop (r3q) | Native depot/purchase layouts, counts, optional paired screens, bounded dragging | 15 host suites plus scrolling oracles pass; development emulator purchases pass. Final exact binary loads/opens depot, but final touch purchase repeat blocked by desktop automation; hardware tests pending |

Detailed limits: [train validation](docs/revival/TRAIN-WORKSPACE-VALIDATION.txt),
[music validation](docs/revival/WAV-VALIDATION-r3o.txt),
[effects validation](docs/revival/SOUND-EFFECTS-VALIDATION.txt).

## Open issues and immediate next steps

1. **Hardware crash narrowed:** dump00000008, user-confirmed r3p, 256x256,
   ordinary play before a chance to save. r3p ELF code bytes match; immediate fault
   is an intentional gxCmdQueueClear panic while its queue is running. SDL's
   transfer/render threading is a race candidate, not a confirmed root cause.
   [Analysis and repair investigation](docs/revival/CRASH-00000008.md). r3r now adds shared SDK graphics locking;
   [validation](docs/revival/GRAPHICS-QUEUE-VALIDATION.md) records passing host/build
   and emulator checks. User reports no crash so far on r3r; extended hardware
   testing remains pending. No map size is certified safe.
2. Finish r3q hardware checks: repeated buying/counts, long consist scrolling,
   pin/unpin, pointer focus and wagon dragging, closing depot, map scrolling.
3. Validate music autoplay/full playlist and effects alongside saving/loading
   and a longer hardware session; capture logs and actual memory/performance.
4. Establish the controlled baseline in BENCHMARKS before choosing optimisations.

r3r is the selected playable beta, with controlled overlap/build/emulator passes
and an initial user hardware pass. Next: wider playtesting and reproducible reports.
No performance optimisation has begun.
Networking is build-disabled; later engine upgrades and AI expansion are outside
current scope. Memory savings are the priority, but there is no approved measured
optimisation list yet. The latest game is a beta, not feature-complete certification.

## Documentation discrepancies resolved or retained

- The supplied planning prompt's “music nearing completion” is outdated: source
  includes working WAV driver, autoplay, track mapping and effects implementation.
- IMPLEMENTATION.md opens with r3d-era wording but contains later sections through
  r3q. Treat its opening as historical; use this file for current state.
- `readme.md` is the public revival introduction. The original port README is
  preserved in [UPSTREAM-README.md](docs/revival/UPSTREAM-README.md); its TODOs
  and download/build instructions are historical, not current revival guidance.
- Configure disables the engine's general thread backend, but the N3DS WAV driver
  explicitly creates a libctru reader thread; “without-threads” is not no threads.
- Toolchain base is digest-pinned; `dkp-pacman` still resolves 3ds-sdl at image-build
  time. Recorded inventory is the evidence; universal bit-for-bit reproduction
  has not been established. Existing mixed-enum linker warnings remain unresolved.

At task completion, update only affected rows/issues and their evidence links.
