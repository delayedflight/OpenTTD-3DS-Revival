#!/bin/bash
set -euo pipefail
cd "$(dirname "$0")/.."
profile="${1:-repair-r3c-play}"
case "$profile" in repair-r3c-play|repair-r3b-play|repair-r3a-play|repair-r3-play|repair-r1-play|emulator-session|large-1024|limit-2048|recovered-autosave|recovered-no-autosave|recovered-1980|recovered-ai-removal-repro) ;; *) echo "Unknown test profile"; exit 1;; esac
emudir="$PWD/work/emulator/azahar-macos-arm64-2126.2"
if [[ -L "$emudir/user" ]]; then unlink "$emudir/user"; elif [[ -e "$emudir/user" ]]; then echo "User directory is not a test symlink; stopping"; exit 1; fi
ln -s "$PWD/work/tests/$profile/user" "$emudir/user"
rom="$PWD/work/tests/$profile/user/sdmc/3ds/openttd/openttd.3dsx"
if [[ "$profile" = repair-r1-play ]]; then rom="$PWD/work/tests/$profile/user/sdmc/3ds/openttd-revival-r1/openttd-revival-r1.3dsx"; fi
if [[ "$profile" = repair-r3-play ]]; then rom="$PWD/work/tests/$profile/user/sdmc/3ds/openttd-revival-r3/openttd-revival-r3.3dsx"; fi
if [[ "$profile" = repair-r3a-play ]]; then rom="$PWD/work/tests/$profile/user/sdmc/3ds/openttd-revival-r3/openttd-revival-r3.3dsx"; fi
if [[ "$profile" = repair-r3b-play ]]; then rom="$PWD/work/tests/$profile/user/sdmc/3ds/openttd-revival-r3/openttd-revival-r3.3dsx"; fi
if [[ "$profile" = repair-r3c-play ]]; then rom="$PWD/work/tests/$profile/user/sdmc/3ds/openttd-revival-r3/openttd-revival-r3.3dsx"; fi
exec "$emudir/Azahar.app/Contents/MacOS/azahar" "$rom"
