#!/bin/bash

source cluster-hosts.env

for host in $ALL_HOSTS
do

ssh -tt $host "sudo systemctl enable docker; sudo systemctl restart docker; sudo docker info"

done
