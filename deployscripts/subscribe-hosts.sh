#!/bin/bash

source cluster-hosts.env

for host in $ALL_HOSTS
do

ssh -tt $host "sudo subscription-manager register --username=$RHN_USER --password=$RHN_PASSWORD; 
sudo subscription-manager attach --pool=$POOL_ID;
sudo subscription-manager repos --disable=*;
sudo subscription-manager repos --enable='rhel-7-server-rpms' --enable='rhel-7-server-extras-rpms' --enable='rhel-7-server-ose-3.3-rpms' "

[ $? -ne 0 ] && echo "** FAIL **"

done
