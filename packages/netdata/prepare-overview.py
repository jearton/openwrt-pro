#!/usr/bin/env python3
# SPDX-License-Identifier: GPL-3.0-or-later
"""Keep the bundled native dashboard local, including its optional resources."""
import pathlib
import shutil
import sys

root = pathlib.Path(sys.argv[1]) / 'v3'
index = root / 'index.html'
text = index.read_text()
policy = ("default-src 'self' data: blob:; script-src 'self' 'unsafe-inline' 'unsafe-eval' blob:; "
          "style-src 'self' 'unsafe-inline'; connect-src 'self'; img-src 'self' data: blob:; "
          "font-src 'self' data:; worker-src 'self' blob:; object-src 'none'; base-uri 'self'")
marker = 'id="openwrt-local-resources"'
if marker not in text:
    if text.count('<head>') != 1:
        raise SystemExit('Unexpected bundled Netdata HTML: missing unique head')
    text = text.replace('<head>', '<head><meta ' + marker +
                        ' http-equiv="Content-Security-Policy" content="' + policy + '">', 1)
    index.write_text(text)

# The bundled native UI requests these font names at the agent root even when
# opened below /v3/. Supply the original local fonts there for offline rendering.
for font in root.glob('*'):
    if font.suffix not in ('.woff', '.woff2', '.ttf', '.eot'):
        continue
    target = root.parent / font.name
    if target.exists() and target.read_bytes() != font.read_bytes():
        raise SystemExit('Conflicting bundled font: ' + font.name)
    if not target.exists():
        shutil.copyfile(font, target)
