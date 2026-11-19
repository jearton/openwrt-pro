#!/usr/bin/env python3
# SPDX-License-Identifier: GPL-3.0-or-later
"""Manage only the disposable, localhost-forwarded CI VM used by check-fresh-lan."""

from pathlib import Path
import socket
import subprocess
import sys
import time


class Guest:
    def __init__(self, directory):
        self.directory = Path(directory)

    def options(self):
        return ["-i", str(self.directory / "key"), "-p", "10022",
                "-o", "BatchMode=yes", "-o", "ConnectTimeout=3",
                "-o", "StrictHostKeyChecking=accept-new",
                "-o", "UserKnownHostsFile=" + str(self.directory / "known_hosts"),
                "-o", "LogLevel=ERROR"]

    def run(self, script, timeout=60):
        result = subprocess.run(
            ["ssh", *self.options(), "root@127.0.0.1", "sh -se"],
            input="set -eu\n" + script, text=True, capture_output=True, timeout=timeout)
        if result.returncode:
            raise RuntimeError(result.stdout + result.stderr)
        return result.stdout

    def upload(self, files):
        options = self.options()
        options[options.index("-p")] = "-P"
        subprocess.run(["scp", "-O", *options, *map(str, files),
                        "root@127.0.0.1:/tmp/technitium-test/"], check=True, timeout=120)

    def wait(self, previous_boot=None):
        deadline = time.monotonic() + 150
        while time.monotonic() < deadline:
            try:
                boot = self.run("cat /proc/sys/kernel/random/boot_id", timeout=5).strip()
                if previous_boot is None or previous_boot != boot:
                    return
            except (RuntimeError, subprocess.TimeoutExpired):
                pass
            time.sleep(2)
        raise RuntimeError("The isolated VM did not provide a new test SSH session")


def bootstrap(directory):
    key = directory / "key"
    subprocess.run(["ssh-keygen", "-q", "-t", "ed25519", "-N", "", "-f", str(key)], check=True)
    public_key = key.with_suffix(".pub").read_text().strip()
    deadline = time.monotonic() + 180
    serial = socket.socket(socket.AF_UNIX)
    while time.monotonic() < deadline:
        try:
            serial.connect(str(directory / "serial.sock"))
            break
        except (FileNotFoundError, ConnectionRefusedError):
            time.sleep(1)
    else:
        raise RuntimeError("The disposable VM serial socket did not open")
    with serial:
        serial.settimeout(2)
        output = b""
        sent = False
        while time.monotonic() < deadline:
            try:
                chunk = serial.recv(65536)
                if not chunk:
                    raise RuntimeError("The VM closed its serial console")
                output = (output + chunk)[-32768:]
            except socket.timeout:
                serial.sendall(b"\n")
                continue
            if b"Press Enter" in output or b"press Enter" in output:
                serial.sendall(b"\n")
            if b"root@OpenWrt" in output and not sent:
                command = (
                    "mkdir -p /etc/dropbear; printf '%s\\n' '" + public_key + "' "
                    ">> /etc/dropbear/authorized_keys; chmod 600 /etc/dropbear/authorized_keys; "
                    "/etc/init.d/dropbear start; printf '\\nBOOTSTRAP-%s\\n' READY\n")
                serial.sendall(command.encode())
                sent = True
            if b"BOOTSTRAP-READY" in output:
                Guest(directory).wait()
                return
    raise RuntimeError("Unable to bootstrap the disposable VM console")


def fixture(guest, packages, repo):
    """Reproduce first initialization separately from the exact-image acceptance."""
    guest.run("""
until test -e /etc/technitium/provisioned; do sleep 1; done
mkdir -p /tmp/technitium-test
""", timeout=150)
    apks = list(packages.glob("*.apk"))
    assert len(apks) == 3
    guest.upload(apks)
    # These two source files share a basename, so stream them to distinct paths.
    for source, target in [("etc/init.d/technitium-provision", "/etc/init.d/technitium-provision"),
                           ("usr/libexec/technitium-provision", "/usr/libexec/technitium-provision")]:
        content = (repo / "sources/full/files" / source).read_text()
        guest.run("cat > " + target + " <<'TECHNITIUM_CI_SOURCE'\n" + content +
                  "\nTECHNITIUM_CI_SOURCE\nchmod 755 " + target)
    guest.run("""
apk --no-network --repositories-file /dev/null --allow-untrusted add /tmp/technitium-test/*.apk
/etc/init.d/technitium stop
mv /etc/technitium /root/technitium-before-ci-firstboot
/etc/init.d/technitium enable
/etc/init.d/technitium-provision enable
""")
    boot = guest.run("cat /proc/sys/kernel/random/boot_id").strip()
    try:
        guest.run("reboot", timeout=10)
    except (RuntimeError, subprocess.TimeoutExpired):
        pass
    guest.wait(previous_boot=boot)
    print("The new packages and firmware initializer are running with fresh DNS state.", flush=True)


def diagnose(guest):
    print(guest.run(r"""
set +e
printf '\nCI guest boot and process state\n'
cat /proc/cmdline
ubus call service list '{"name":"technitium"}'
ubus call service list '{"name":"technitium-provision"}'
test -e /etc/technitium/provisioned && echo INITIALIZATION_COMPLETE
printf '\nListening sockets\n'
netstat -lntup
printf '\nLAN and dnsmasq configuration\n'
uci -q get network.lan.ipaddr
uci -q show dhcp
printf '\nTechnitium startup messages\n'
logread | grep -Ei 'technitium|dnsmasq|procd' | tail -n 60
for logfile in /tmp/technitium-logs/*.log; do
    test ! -f "$logfile" || tail -n 35 "$logfile"
done
printf '\nLocal DNS queries\n'
timeout 6 nslookup openwrt.lan 127.0.0.1
timeout 6 nslookup openwrt.lan 192.168.1.1
timeout 6 nslookup openwrt.lan 127.0.0.1:5353
printf '\nLAN firewall and routes\n'
nft list chain inet fw4 input
nft list chain inet fw4 input_lan
ip -4 route
printf '\nNative DNS configuration via API\n'
token=$(curl -fsS --max-time 5 -G http://127.0.0.1:5380/api/user/login \
  --data-urlencode user=admin --data-urlencode pass@/etc/technitium/setup-password | jsonfilter -e '@.token')
if test -n "$token"; then
    curl -fsS --max-time 5 -H "Authorization: Bearer $token" http://127.0.0.1:5380/api/settings/get |
      jsonfilter -e '@.response.dnsServerLocalEndPoints' -e '@.response.recursion' -e '@.response.preferIPv6'
    curl -fsS --max-time 5 -H "Authorization: Bearer $token" http://127.0.0.1:5380/api/zones/list |
      jsonfilter -e '@.response.zones[*].name'
    curl -fsS --max-time 5 -H "Authorization: Bearer $token" http://127.0.0.1:5380/api/user/logout >/dev/null
fi
true
""", timeout=50), flush=True)


if __name__ == "__main__":
    action, temporary = sys.argv[1:3]
    guest = Guest(temporary)
    if action == "bootstrap":
        bootstrap(Path(temporary))
    elif action == "fixture":
        fixture(guest, Path(sys.argv[3]), Path(__file__).resolve().parent.parent)
    elif action == "diagnose":
        diagnose(guest)
    else:
        raise SystemExit("Unknown disposable VM action")
