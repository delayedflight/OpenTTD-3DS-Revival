#!/bin/bash
set -euo pipefail
# Copy into a disposable container filesystem; upstream configure breaks on spaces.
tar -C /source --exclude=./.git --exclude=./builds --exclude=./logs -cf - . | tar -C /build -xf -
cd /build
export SOURCE_DATE_EPOCH=1593332519
cp /toolchain-packages.txt /artifacts/toolchain-packages.txt
./configure --os=N3DS --host "$DEVKITARM/bin/arm-none-eabi" --enable-static --prefix-dir="$DEVKITPRO" --with-sdl="$DEVKITPRO/portlibs/3ds/bin/sdl-config" --without-png --without-threads --disable-network --disable-unicode --without-libfontconfig --without-zlib --without-libfreetype --without-icu
make -j2
mkdir -p /artifacts/repair-r3q
"$DEVKITPRO/tools/bin/3dsxtool" bin/openttd /artifacts/repair-r3q/openttd.3dsx
cp bin/openttd /artifacts/repair-r3q/openttd.elf
cp -a bin/lang /artifacts/repair-r3q/
cp /toolchain-packages.txt /artifacts/repair-r3q/
