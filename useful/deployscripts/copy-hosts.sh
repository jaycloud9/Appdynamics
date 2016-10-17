#!/bin/bash

source cluster-hosts.env

for host in $ALL_HOSTS
do

scp hosts $host:
ssh -tt $host sudo cp ~/hosts /etc/hosts
[ $? -ne 0 ] && echo "** FAIL **"

done
