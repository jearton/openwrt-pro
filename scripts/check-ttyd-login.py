#!/usr/bin/env python3
# SPDX-License-Identifier: GPL-3.0-or-later
"""Exercise both authorization gates on a disposable LAN test VM."""

from contextlib import closing
from pathlib import Path
import sys
import time

import websocket


def check(cookies, password_file, mode):
    session, = (line.split()[-1] for line in Path(cookies).read_text().splitlines()
                if "\tsysauth_http\t" in line)
    cookie = "sysauth_http=" + session
    url = "ws://192.168.1.1:7681/cgi-bin/luci/terminal-session/ws"
    origin = "http://192.168.1.1:7681"

    def connect(value=cookie, source=origin):
        terminal = websocket.create_connection(url, cookie=value, origin=source,
                                               subprotocols=["tty"], timeout=4)
        terminal.send_binary(b'{"columns":80,"rows":24,"AuthToken":""}')
        return terminal

    def read_until(terminal, expected, timeout=15):
        output = b""
        deadline = time.monotonic() + timeout
        while time.monotonic() < deadline:
            try:
                frame = terminal.recv()
            except websocket.WebSocketConnectionClosedException:
                break
            if isinstance(frame, bytes) and frame.startswith(b"0"):
                output += frame[1:]
                if expected in output:
                    return output
        raise AssertionError("Terminal did not reach the expected authentication stage")

    if mode == "empty":
        with closing(connect()) as terminal:
            read_until(terminal, b"Set a system password in LuCI before using the terminal.")
        print("An empty system password cannot open a terminal shell", flush=True)
        return
    if mode != "password":
        raise SystemExit("Unknown terminal test mode")

    for invalid, source in [(None, origin), ("sysauth_http=" + "0" * 32, origin),
                            (cookie, "http://example.invalid")]:
        try:
            with closing(connect(invalid, source)):
                raise AssertionError("Unauthorized WebSocket upgrade was accepted")
        except (websocket.WebSocketBadStatusException, websocket.WebSocketConnectionClosedException):
            pass

    password = Path(password_file).read_text()
    assert password and "\n" not in password
    with closing(connect()) as terminal:
        read_until(terminal, b"login:")
        terminal.send_binary(b"0root\n")
        read_until(terminal, b"Password:")
        terminal.send_binary(b"0" + password.encode() + b"\n")
        read_until(terminal, b"root@OpenWrt")
        terminal.send_binary(b"0printf '\\nTTyD-PASSWORD-%s\\n' \"$(id -u)\"\n")
        read_until(terminal, b"\nTTyD-PASSWORD-0\r\n")

    # A previous successful terminal login must not authorize a new terminal.
    with closing(connect()) as terminal:
        read_until(terminal, b"login:")
    print("Each terminal requires a system login; authenticated root commands and LuCI/Origin denials passed", flush=True)


if __name__ == "__main__":
    if len(sys.argv) != 4:
        raise SystemExit("Usage: check-ttyd-login.py COOKIE_FILE PASSWORD_FILE empty|password")
    check(*sys.argv[1:])
