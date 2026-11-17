#!/usr/bin/env bash
# SPDX-License-Identifier: GPL-3.0-or-later
set -euo pipefail

test_dir=$(mktemp -d)
vm_pid=
cleanup() {
    status=$?
    if [[ -n $vm_pid ]]; then
        kill "$vm_pid" 2>/dev/null || :
        wait "$vm_pid" 2>/dev/null || :
    fi
    if [[ $status != 0 && -f "$test_dir/serial.log" ]]; then
        tail -n 80 "$test_dir/serial.log"
    fi
    find "$test_dir" -type f -delete
    rmdir "$test_dir"
}
trap cleanup EXIT

gzip -dc "$1" > "$test_dir/disk.img"
cp /usr/share/OVMF/OVMF_VARS_4M.fd "$test_dir/vars.fd"
lan=user,id=lan,restrict=on,ipv6=off,net=192.168.1.0/24,host=192.168.1.2
lan+=,hostfwd=tcp:127.0.0.1:18080-192.168.1.1:80
lan+=,hostfwd=tcp:127.0.0.1:17681-192.168.1.1:7681
lan+=,hostfwd=tcp:127.0.0.1:29999-192.168.1.1:19999
qemu-system-x86_64 -machine q35 -accel kvm -accel tcg -smp 2 -m 1024 \
    -display none -monitor none -serial "file:$test_dir/serial.log" \
    -drive if=pflash,format=raw,readonly=on,file=/usr/share/OVMF/OVMF_CODE_4M.fd \
    -drive "if=pflash,format=raw,file=$test_dir/vars.fd" \
    -drive "if=ide,format=raw,file=$test_dir/disk.img" \
    -netdev "$lan" -device e1000,netdev=lan &
vm_pid=$!

fetch() {
    curl -fsSL --noproxy '*' --connect-timeout 2 --max-time 5 \
        "http://127.0.0.1:$1" -o "$2"
}

deadline=$((SECONDS + 300))
until fetch 18080/cgi-bin/luci/ "$test_dir/luci.html" 2>/dev/null &&
    fetch 17681/ "$test_dir/terminal.html" 2>/dev/null &&
    fetch 29999/v3/ "$test_dir/netdata.html" 2>/dev/null &&
    fetch 29999/api/v1/charts "$test_dir/charts.json" 2>/dev/null &&
    jq -e '.charts["system.cpu"] != null' "$test_dir/charts.json" >/dev/null; do
    kill -0 "$vm_pid"
    if (( SECONDS >= deadline )); then
        echo 'Fresh LAN boot did not serve LuCI, ttyd and Netdata' >&2
        exit 1
    fi
    sleep 3
done

grep -qi luci "$test_dir/luci.html"
grep -qi ttyd "$test_dir/terminal.html"
echo 'Fresh UEFI boot served LuCI, ttyd and Netdata charts via the isolated IPv4 LAN'
