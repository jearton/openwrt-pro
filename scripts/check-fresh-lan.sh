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
lan+=,hostfwd=tcp:127.0.0.1:18443-192.168.1.1:443
lan+=,hostfwd=tcp:127.0.0.1:17681-192.168.1.1:7681
lan+=,hostfwd=tcp:127.0.0.1:29999-192.168.1.1:19999
lan+=,hostfwd=tcp:127.0.0.1:15380-192.168.1.1:5380
lan+=,hostfwd=udp:127.0.0.1:10553-192.168.1.1:53
lan+=,hostfwd=tcp:127.0.0.1:10553-192.168.1.1:53
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
luci_http=http://127.0.0.1:18080
terminal_path=/cgi-bin/luci/terminal-session/
terminal_http="http://127.0.0.1:17681$terminal_path"
status() {
    curl -ksS --noproxy '*' --connect-timeout 2 --max-time 5 -o /dev/null -w '%{http_code}' "$@"
}

until [[ $(status "$luci_http/cgi-bin/luci/" 2>/dev/null) = 403 ]] &&
    [[ $(status "$terminal_http" 2>/dev/null) = 403 ]] &&
    fetch 29999/v3/ "$test_dir/netdata.html" 2>/dev/null &&
    fetch 29999/api/v1/charts "$test_dir/charts.json" 2>/dev/null &&
    jq -e '.charts["system.cpu"] != null' "$test_dir/charts.json" >/dev/null &&
    fetch 15380/ "$test_dir/technitium.html" 2>/dev/null &&
    grep -qi 'Technitium' "$test_dir/technitium.html" &&
    [[ $(dig @127.0.0.1 -p 10553 openwrt.lan A +short +time=1 +tries=1) = 192.168.1.1 ]]; do
    kill -0 "$vm_pid"
    if (( SECONDS >= deadline )); then
        echo 'Fresh LAN boot did not serve LuCI, ttyd, Netdata and native DNS' >&2
        exit 1
    fi
    sleep 3
done

login() {
    curl -ksS --noproxy '*' --connect-timeout 2 --max-time 5 \
        --cookie-jar "$2" --data 'luci_username=root&luci_password=' "$1/cgi-bin/luci/" -o /dev/null
}

login "$luci_http" "$test_dir/http.cookies"
curl -kfsS --noproxy '*' -b "$test_dir/http.cookies"     "$luci_http/cgi-bin/luci/admin/services/technitium" -o "$test_dir/technitium-luci.html"
grep -Eq 'technitium[./]status' "$test_dir/technitium-luci.html"
[[ $(dig @127.0.0.1 -p 10553 openwrt.lan A +short +tcp +time=2 +tries=1) = 192.168.1.1 ]]
[[ $(dig @127.0.0.1 -p 10553 -x 192.168.1.1 +short +time=2 +tries=1) = openwrt.lan. ]]
login https://127.0.0.1:18443 "$test_dir/https.cookies"
for scheme in http https; do
    cookie="$(awk -v name="sysauth_$scheme" '$6 == name { print $6 "=" $7 }' "$test_dir/$scheme.cookies")"
    test -n "$cookie"
    curl -kfsS --noproxy '*' -b "$cookie" "$scheme://127.0.0.1:17681$terminal_path" \
        -o "$test_dir/terminal.html"
    grep -qi ttyd "$test_dir/terminal.html"
done
[[ $(status -b "$cookie" "$terminal_http") = 403 ]]

/usr/bin/python3 - "$test_dir/http.cookies" "$terminal_path" <<'PY'
import sys
import time
from contextlib import closing

import websocket

with open(sys.argv[1]) as cookies:
    session, = (line.split()[-1] for line in cookies if "\tsysauth_http\t" in line)
url = 'ws://127.0.0.1:17681' + sys.argv[2] + 'ws'
origin = 'http://127.0.0.1:17681'
cookie = 'sysauth_http=' + session

def connect(value=None, source=origin):
    return websocket.create_connection(url, cookie=value, origin=source, subprotocols=['tty'], timeout=4)

for invalid, source in [(None, origin), ('sysauth_http=' + '0' * 32, origin), (cookie, 'http://example.invalid')]:
    try:
        with closing(connect(invalid, source)):
            raise AssertionError('Unauthorized WebSocket upgrade was accepted')
    except (websocket.WebSocketBadStatusException, websocket.WebSocketConnectionClosedException):
        pass

with closing(connect(cookie)) as terminal:
    terminal.send_binary(b'{"columns":80,"rows":24,"AuthToken":""}')
    deadline = time.monotonic() + 12
    commands_sent = False
    output = b''
    while time.monotonic() < deadline:
        frame = terminal.recv()
        if not isinstance(frame, bytes) or not frame.startswith(b'0'):
            continue
        output += frame[1:]
        if not commands_sent:
            terminal.send_binary(b"0printf '\\nTTyD-SESSION-%s\\n' \"$(id -u)\"\n")
            commands_sent = True
        if b'\nTTyD-SESSION-0\r\n' in output:
            break
    else:
        raise AssertionError('LuCI session did not open a root shell')
PY
echo 'Fresh isolated IPv4 boot verified LuCI, Netdata, authorized ttyd, and the Technitium console and DNS on UDP/TCP'
