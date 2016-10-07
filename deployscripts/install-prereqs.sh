#!/bin/bash

source cluster-hosts.env

for host in $ALL_HOSTS
do

ssh -tt $host "sudo yum install deltarpm -y; sudo yum install -y docker wget git net-tools bind-utils iptables-services bridge-utils bash-completion atomic-openshift-utils; sudo yum update -y"

[ $? -ne 0 ] && echo "** FAIL **"

done
