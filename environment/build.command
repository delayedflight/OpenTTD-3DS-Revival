#!/bin/bash
set -euo pipefail
cd "$(dirname "$0")/.."
DOCKER_BIN=$(command -v docker || true)
if [[ -z "$DOCKER_BIN" ]]; then DOCKER_BIN=/Applications/Docker.app/Contents/Resources/bin/docker; fi
mkdir -p builds logs
SOURCE_DIR="$PWD/work/r3q-source"
if [[ -d "$PWD/src" ]]; then SOURCE_DIR="$PWD"; fi
if [[ -d "$PWD/source" ]]; then SOURCE_DIR="$PWD/source"; fi
SOURCE_DIR="${OPENTTD_SOURCE_DIR:-$SOURCE_DIR}"
IMAGE_TAG="${OPENTTD_IMAGE_TAG:-openttd3ds-revival:r3r}"
"$DOCKER_BIN" build -t "$IMAGE_TAG" environment 2>&1 | tee logs/container-build.log
"$DOCKER_BIN" run --rm --network none --mount "type=bind,src=$SOURCE_DIR,dst=/source,readonly" --mount "type=bind,src=$PWD/builds,dst=/artifacts" "$IMAGE_TAG" 2>&1 | tee logs/game-build.log
