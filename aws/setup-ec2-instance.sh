#!/bin/bash -eu
yum update -y && yum install -y rsync
mkdir -m 777 -p /home/ec2-user/torrents

CONF=/etc/sysctl.d/99-overcommit-memory.conf
if [ "`sysctl -n vm.overcommit_memory`" == "0" ]; then
    echo "Setting vm.overcommit_memory to 1 for Redis persistence"
    echo "creating $CONF (see https://redis.io/topics/admin)"
    echo "vm.overcommit_memory = 1" > $CONF
    sysctl -p $CONF
fi
