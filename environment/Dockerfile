# Official devkitPro image, pinned to the resolved registry digest.
FROM devkitpro/devkitarm:20260610@sha256:116afba8df8453961de2936ffab20dd441edf4d682856c1ec8b0e53d7ed0bbf5
RUN dkp-pacman -S --needed --noconfirm 3ds-sdl && dkp-pacman -Q > /toolchain-packages.txt
RUN apt-get update && apt-get install -y --no-install-recommends autoconf automake libtool && rm -rf /var/lib/apt/lists/*
COPY vendor/SDL-1.2.15.tar.gz vendor/SDL-1.2.15-sdk.patch patches/SDL-1.2.15-render-lock.patch /tmp/SDL-source/
COPY build-sdl.sh /tmp/build-sdl.sh
RUN bash /tmp/build-sdl.sh && rm -rf /tmp/SDL-source
WORKDIR /build
COPY build.sh /usr/local/bin/build-openttd
RUN chmod +x /usr/local/bin/build-openttd
ENTRYPOINT ["/usr/local/bin/build-openttd"]
