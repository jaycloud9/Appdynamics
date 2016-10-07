#!/bin/bash

source cluster-hosts.env

for host in $ALL_HOSTS
do

ssh -tt $host sudo reboot

done
