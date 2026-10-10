#!/bin/sh
# Called before MPC starts. sync.sh backs up and validates the settings edit.
set -eu
if pidof MPC >/dev/null 2>&1; then
    echo 'OpenPlugin registration requires MPC to be stopped' >&2
    exit 1
fi
mkdir -p /data/openplugin/previews
for row in 1 2 3; do
    file="/data/openplugin/previews/row${row}.png"
    if [ ! -f "$file" ]; then cp /usr/share/openplugin/bundled-previews/fallback-row.png "$file"; fi
done
exec /bin/sh /usr/share/openplugin/sync.sh -y -n -t /usr/share/Akai/Content/Synths
