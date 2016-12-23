#!/bin/bash -eu
find . -name "*.torrent" -print0 | xargs -0 aria2c -S | gzip > torrents.txt.gz
zcat torrents.txt.gz | grep ^Name | sort | gzip > torrent-names.txt.gz
