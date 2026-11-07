# Repaired SDL source inputs

SDL1.2.15 from https://www.libsdl.org/release/SDL-1.2.15.tar.gz:
SHA256 d6d316a793e5e348155f0dd93b979798933fb98aa1edebcc108829d6474aad00.
SDL-COPYING.txt contains its GNU LGPL2.1 license; see the tarball for notices.

DevkitPro's 3ds-sdl1.2.15-19 platform patch from
https://raw.githubusercontent.com/devkitPro/pacman-packages/master/3ds/SDL/SDL-1.2.15.patch:
SHA256 83941419c8fc87a280b1d45db595b720fe190959a0094c727a566d2b9de20804.
The original patch is preserved without changes; its source retains SDL notices.

The separately identified revival modification is
../patches/SDL-1.2.15-render-lock.patch, dated 7 November 2026: one shared libctru
LightLock serializes Citro3D upload/texture setup with private-thread rendering.
It is a modification to the LGPL SDL library, provided under the same LGPL2.1-or-later
terms as that library. Rebuild instructions are ../build-sdl.sh and ../Dockerfile.
The complete OpenTTD source/build recipe is supplied so the executable can be
rebuilt/relinked with this or a modified SDL. No private game/audio assets are here.
