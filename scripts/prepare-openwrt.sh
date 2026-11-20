#!/usr/bin/env bash
# SPDX-License-Identifier: GPL-3.0-or-later
set -euo pipefail

repo=$(cd -- "$(dirname -- "$0")/.." && pwd)
if [[ $# != 1 || -e $1 ]]; then
    echo "Usage: $0 NEW_OPENWRT_DIRECTORY" >&2
    exit 2
fi
target=$1
upstream=$(python3 -c 'import json,sys; print(json.load(open(sys.argv[1]))["source"]["url"])' "$repo/sources.lock.json")
ref=$(python3 -c 'import json,sys; print(json.load(open(sys.argv[1]))["source"]["ref"])' "$repo/sources.lock.json")
commit=$(python3 -c 'import json,sys; print(json.load(open(sys.argv[1]))["source"]["commit"])' "$repo/sources.lock.json")

git clone --depth 1 --branch "$ref" "$upstream" "$target"
cd -- "$target"
test "$(git rev-parse HEAD)" = "$commit"
python3 - "$repo/sources.lock.json" > feeds.conf <<'PY'
import json
import sys

with open(sys.argv[1]) as source:
    for feed in json.load(source)["feeds"]:
        print(feed["upstream_definition"])
PY
./scripts/feeds update -a
./scripts/feeds install -a
for package in luci-app-weechat netdata; do
    ./scripts/feeds uninstall "$package"
done
mkdir -p package/custom
cp -a "$repo/packages/netdata" package/custom/
for patch in netdata-config-readable netdata-container-network netdata-overview; do
    git apply --check "$repo/patches/custom-ipv4/$patch.patch"
    git apply "$repo/patches/custom-ipv4/$patch.patch"
done
cp "$repo/profiles/netdata.config" .config
make defconfig
grep -Fx 'CONFIG_USE_APK=y' .config
grep -Fx 'CONFIG_GRUB_BOOTOPTS="ipv6.disable=1"' .config
for package in netdata dockerd docker-compose adguardhome; do
    grep -Fx "CONFIG_PACKAGE_$package=y" .config
done
