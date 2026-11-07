# Git and output organisation

Canonical repository: overarching project/source. Branch: revival/main.
Remote origin is the public fork https://github.com/delayedflight/OpenTTD-3DS-Revival,
with revival/main as its default branch. The upstream remote retains the public
EnergeticBark/OpenTTD-3DS source with push disabled. Revival history and release
source tags (including revival-r3r-beta) are uploaded. Private evidence, soundtrack
and generated builds are excluded. Binary release assets have not been published.
Author identity on the recovery commits is the repository-local project name
OpenTTD 3DS Revival <revival@localhost>, not a claim of upstream authorship.

Original upstream commits are preserved. Twenty-one recovery commits import
r1, r1b, r2, r3 and r3a–r3q from the exact corresponding source archives.
Tags revival-r1 through revival-r3q identify those source trees. Recovery dates
are current; these are not the original implementation-time commits. Read
RELEASES.json for archive hashes, commit IDs and available executable hashes.
Tags identify source snapshots; each preserved source archive also contains its
historical build environment. The following maintenance commit adds the current
contained build environment and project handover without altering game code.
The old revival/stability worktree and all work/r*-source copies are preserved.

## Daily workflow

```sh
git status
git switch -c fix/short-description
# make focused source/doc changes; run appropriate existing tests
git diff --check
git diff
git add <specific files>
git commit -m "Describe concrete behavior change"
```

Review before merging back into revival/main. Create an annotated release tag
only for a recorded release, and keep that release's executable, matching ELF,
source, test results and checksums. Update PROJECT-HANDOVER.md at milestones.
Do not overwrite or move existing release tags to a new build.

Private saves, scenarios, crash dumps, soundtrack, generated binaries, logs and
build directories are ignored. The canonical checkout starts without these;
ignores are not a substitute for reviewing staged files. Upstream public code
assets remain in its original history. No game/source archive was modified by
output tidying. A file-by-file SHA256 relocation inventory verifies preservation.

## Outputs

- latest -> releases/r3q (convenient pointer, not a second release).
- releases/<release>/packages: distribution ZIPs.
- releases/<release>/source: corresponding-source archives and review patches.
- releases/<release>/notes, screenshots, logs: release evidence and instructions.
- releases/<release>/unpacked: previously extracted packages, retained intact.
- reports: general investigations and baseline tests.
- guides: current implementation, organisation and handover documents.
- private-test-data: disposable save ZIP, explicitly not public release material.
- organisation/output-migration.json: old/new paths and checked file hashes.

Six recent-download aliases preserve the latest chat links. Older chat links
can be located through the migration inventory. No historical artifacts were
deleted. Temporary tools, emulator profiles, private evidence, logs and existing
builds remain in their original project locations so diagnostic scripts and
Docker mounts keep working. New development uses source/ only.

## Local backup

organisation/OpenTTD-3DS-Revival-history.bundle contains all canonical Git refs
and history at the organisation checkpoint. It excludes untracked private
material. A bundle in the same folder is convenient recovery, not an off-device
backup. Copy it to your own backup location as appropriate. Restore with:

```sh
git clone OpenTTD-3DS-Revival-history.bundle revival-restored
git -C revival-restored switch revival/main
```

The public fork now backs up committed revival source/tags. Local build/ELF and
private evidence backups remain separate responsibilities.
