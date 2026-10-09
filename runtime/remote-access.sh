#!/bin/sh
# Device-local credentials. No passwords in the shared image or process arguments.
set -eu
umask 077
D=/data/openplugin/ssh
mkdir -p "$D" /run/sshd
chmod 700 /data/openplugin "$D"
prepare() {
    [ ! -f "$D/disabled" ] || exit 1
    if [ ! -s "$D/ssh_host_ed25519_key" ]; then
        ssh-keygen -q -t ed25519 -N '' -f "$D/ssh_host_ed25519_key"
    fi
    if [ ! -s "$D/password" ]; then
        od -An -N12 -tx1 /dev/urandom | tr -d ' \n' > "$D/password.new"
        [ "$(wc -c < "$D/password.new")" -eq 24 ]
        mv "$D/password.new" "$D/password"
    fi
    if [ ! -s "$D/original-root-hash" ]; then
        awk -F: '$1=="root" {print $2}' /etc/shadow > "$D/original-root-hash"
    fi
    openssl passwd -6 -stdin < "$D/password" > "$D/hash"
    replace_hash "$D/hash"
}
replace_hash() {
    # Rootfs is read-only. Bind a private writable shadow file over the stock file.
    awk -F: 'BEGIN {OFS=":"} NR==FNR {hash=$0; next} $1=="root" {$2=hash} {print}' "$1" /etc/shadow > "$D/shadow.new"
    chmod 600 "$D/shadow.new"
    chown 0:0 "$D/shadow.new"
    if [ -f /run/openplugin-shadow-mounted ]; then
        umount /etc/shadow
        rm -f /run/openplugin-shadow-mounted
    fi
    mv "$D/shadow.new" "$D/shadow"
    mount --bind "$D/shadow" /etc/shadow
    touch /run/openplugin-shadow-mounted
}
restore_shadow() {
    if [ -f /run/openplugin-shadow-mounted ]; then
        umount /etc/shadow
        rm -f /run/openplugin-shadow-mounted
    fi
}
case "${1:-}" in
    prepare) prepare ;;
    enable)
        rm -f "$D/disabled"
        if ! systemctl start openplugin-remote.service; then
            touch "$D/disabled"
            restore_shadow
            exit 1
        fi ;;
    disable)
        touch "$D/disabled"
        systemctl stop openplugin-remote.service
        restore_shadow ;;
    *) exit 2 ;;
esac
