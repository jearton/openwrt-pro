#!/bin/sh
set -eu

asset=$1
destination=$2
# The pinned makeself asset has an 830-line shell header.
offset=$(head -n 830 "$asset" | wc -c)
tail -c "+$((offset + 1))" "$asset" |
	tar -xz -C "$destination" \
		./bin/srv/netdata ./usr/lib/netdata/conf.d ./usr/share/netdata/web
test -x "$destination/bin/srv/netdata"
test -s "$destination/usr/share/netdata/web/index.html"
