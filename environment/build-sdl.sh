#!/bin/bash
set -euo pipefail
cd /tmp/SDL-source
printf '%s\n' 'd6d316a793e5e348155f0dd93b979798933fb98aa1edebcc108829d6474aad00  SDL-1.2.15.tar.gz' '83941419c8fc87a280b1d45db595b720fe190959a0094c727a566d2b9de20804  SDL-1.2.15-sdk.patch' | sha256sum -c -
tar -xzf SDL-1.2.15.tar.gz
cd SDL-1.2.15
source /opt/devkitpro/3dsvars.sh
patch -p1 < ../SDL-1.2.15-sdk.patch
patch -p1 < ../SDL-1.2.15-render-lock.patch
./autogen.sh
# The 2012 platform detector predates Apple-silicon Docker hosts.
cp /usr/share/misc/config.guess /usr/share/misc/config.sub build-scripts/
./configure --prefix="$PORTLIBS_PREFIX" --host=arm-none-eabi --disable-shared --enable-static --enable-n3ds
make -j2
make install
sha256sum /opt/devkitpro/portlibs/3ds/lib/libSDL.a > /sdl-render-lock.sha256
