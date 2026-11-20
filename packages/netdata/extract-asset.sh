#!/bin/sh
set -eu

asset=$1
destination=$2
# Read the archive boundary as data. Never execute the upstream installer.
header_lines=$(LC_ALL=C awk '
    NR > 200 { exit }
    /^skip="?[0-9]+"?$/ { gsub(/[^0-9]/, ""); print; exit }
' "$asset")
case "$header_lines" in
    ''|*[!0-9]*) echo 'Missing makeself archive boundary' >&2; exit 1 ;;
esac
test "$header_lines" -ge 1 && test "$header_lines" -le 4096
offset=$(head -n "$header_lines" "$asset" | wc -c)
tail -c "+$((offset + 1))" "$asset" |
	tar -xz -C "$destination" \
		./bin/srv/netdata ./usr/lib/netdata/conf.d ./usr/share/netdata/web
test -x "$destination/bin/srv/netdata"
test -s "$destination/usr/share/netdata/web/index.html"
