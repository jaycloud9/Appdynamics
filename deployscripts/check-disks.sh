#!/bin/bash

source cluster-hosts.env

for host in $ALL_HOSTS
do

echo "***************************"
echo "********* $host ***********"

ssh -tt $host sudo fdisk -l | grep sdc

echo "**                       **"
echo "**                       **"
echo "***************************"
echo "***************************"

done
