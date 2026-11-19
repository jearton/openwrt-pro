#!/usr/bin/env python3
# SPDX-License-Identifier: GPL-3.0-or-later
"""Reject packed root filesystems that prevent non-root services from starting."""

import subprocess
import sys


def check(unsquash, image):
    listing = subprocess.check_output([unsquash, "-ll", image], text=True)
    modes = {}
    for line in listing.splitlines():
        fields = line.split(None, 5)
        if len(fields) != 6 or not fields[5].startswith("squashfs-root"):
            continue
        path = fields[5].split(" -> ", 1)[0].removeprefix("squashfs-root").lstrip("/")
        modes[path] = fields[0]

    directories = ("", "bin", "sbin", "lib", "usr", "usr/bin", "usr/sbin",
                   "usr/lib", "usr/share", "etc", "etc/init.d", "www", "www/cgi-bin")
    for path in directories:
        mode = modes.get(path, "")
        if len(mode) != 10 or mode[0] != "d" or mode[7] != "r" or mode[9] not in "xt":
            raise SystemExit(f"Non-root services cannot read/traverse /{path}: {mode or 'missing'}")
        if mode[8] == "w":
            raise SystemExit(f"Public system directory is writable by everyone: /{path}")
    for path in ("sbin/ubusd", "etc/passwd", "etc/group", "www/cgi-bin/luci"):
        mode = modes.get(path, "")
        if len(mode) != 10 or mode[7] != "r":
            raise SystemExit(f"Non-root services cannot read /{path}: {mode or 'missing'}")
    # Do not fix permissions recursively: credentials and state must stay private.
    shadow = modes.get("etc/shadow", "")
    if len(shadow) != 10 or shadow[7:9] != "--":
        raise SystemExit("The packaged shadow file is missing or readable/writable by everyone")
    print("Packed rootfs public paths are accessible; shadow remains private")


if __name__ == "__main__":
    if len(sys.argv) != 3:
        raise SystemExit("Usage: check-rootfs-permissions.py UNSQUASHFS ROOT.SQUASHFS")
    check(*sys.argv[1:])
