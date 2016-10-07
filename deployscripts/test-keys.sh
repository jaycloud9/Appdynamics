#!/bin/bash

source cluster-hosts.env

for host in $ALL_HOSTS
do

ssh $host echo "OK"
[ $? -ne 0 ] && echo "** FAIL **"

done
