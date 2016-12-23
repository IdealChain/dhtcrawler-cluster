#!/bin/bash -eu
if [[ -z "${1:-}" ]]; then
    read -p "EC2 collector instance hostname/IP: " -e REMOTE
else
    REMOTE="$1"
fi
rsync -zthrP --rsync-path="nice rsync" $REMOTE:/home/ec2-user/torrents/. .
