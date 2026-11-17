#!/usr/bin/env bash
# SPDX-License-Identifier: GPL-3.0-or-later
set -euo pipefail

if [[ $# != 1 || ! -d $1 ]]; then
    echo "Usage: $0 DIRECTORY_WITH_FIRMWARE_BUNDLE" >&2
    exit 2
fi

repo=$(cd -- "$(dirname -- "$0")/.." && pwd)
cd -- "$1"
image=openwrt-x86-64-generic-squashfs-combined-efi.img.gz
manifest=openwrt-x86-64-generic.manifest
cmp SHA256SUMS "$repo/manifests/SHA256SUMS"
cmp "$manifest" "$repo/manifests/$manifest"
sha256sum --strict -c SHA256SUMS
gzip -t "$image"
