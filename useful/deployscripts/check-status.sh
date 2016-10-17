#!/bin/bash

source cluster-hosts.env

echo "*** Testing LB"
for tryit in $(seq 0 9)
do
   echo "Test $tryit: $(curl -skI --connect-timeout 3 https://cluster1.temenosgroup.com | grep HTTP)"
done

for host in $MASTER_HOSTS
do
   echo "*** Testing API availability $host"
   
   for tryit in $(seq 0 9)
   do
      echo "Test $host $tryit: $(curl -skI --connect-timeout 3 https://$host | grep HTTP)"
   done

done

for host in $ALL_HOSTS
do

echo "***********************************"
echo "***********************************"
echo "**** $host"
echo "****"
echo "**** Node health"
   ssh -tt $host "sudo systemctl status atomic-openshift-node" 2>/dev/null | grep "Active:"

if [[ "$host" == *"master"* ]] ; then
   echo "**** Master health"
   ssh -tt $host "sudo systemctl status atomic-openshift-master-api; sudo systemctl status atomic-openshift-master-controllers" 2>/dev/null | grep "Active:"

   echo "**** etcd directory "
   ssh -tt $host "sudo bash -c 'df -h /var/lib/etcd'" 2>/dev/null
fi

   echo "**** root filesystem and docker metadata "
   ssh -tt $host "sudo bash -c 'df -h /;df -h /var/lib/docker; vgs; lvs'" 2>/dev/null

   ssh -tt $host "sudo docker info" 2>/dev/null   
   

echo "***********************************"
echo "***********************************"

done
