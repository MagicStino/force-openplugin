#!/bin/sh
set -eu
umask 077
mkdir -p /data/openplugin/ssh /run/sshd
chmod 700 /data/openplugin /data/openplugin/ssh
KEY=/data/openplugin/ssh/ssh_host_ed25519_key
if [ ! -s "$KEY" ]; then
    ssh-keygen -q -t ed25519 -N '' -f "$KEY.new"
    mv "$KEY.new" "$KEY"
    mv "$KEY.new.pub" "$KEY.pub"
fi
chmod 600 "$KEY"
