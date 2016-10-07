#!/bin/bash

source cluster-hosts.env

for host in $MASTER_HOSTS
do

scp htpasswd $host:
ssh -tt $host sudo cp $HOME/htpasswd /etc/origin/master/

done
