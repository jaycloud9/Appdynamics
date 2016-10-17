#!/bin/bash

source cluster-hosts.env

DEV=/dev/sdb

for host in $ALL_HOSTS
do

## enable lvm services
ssh -tt $host "sudo systemctl enable lvm2-lvmetad.service;sudo systemctl start lvm2-lvmetad.service;
sudo systemctl enable lvm2-lvmpolld.service; sudo systemctl start lvm2-lvmpolld.service; sudo /sbin/swapoff /mnt/resource/swapfile; sudo umount /mnt/resource; (echo d; echo w) | sudo /sbin/fdisk $DEV"

# create a VG from the above device and create a vg for /var/lib/docker
ssh -tt $host "sudo pvcreate $DEV; sudo vgcreate vg_ocp $DEV; sudo lvcreate -L 200G vg_ocp --name docker_var; sudo mkfs.xfs /dev/mapper/vg_ocp-docker_var"

#read -p "press any key"

# add mountpoint to fstab
ssh -tt $host "sudo bash -c \"echo '/dev/mapper/vg_ocp-docker_var /var/lib/docker xfs defaults 0 0' >> /etc/fstab\" "
ssh -tt $host "sudo mkdir -p /var/lib/docker; sudo mount /var/lib/docker"

#read -p "press any key"

## if this is a master, then add a mount point for etcd
if [[ "$host" == *"master"* ]] ; then 
   ssh -tt $host "sudo lvcreate -L 15G vg_ocp --name etcd; sudo mkfs.xfs /dev/mapper/vg_ocp-etcd "
   ssh -tt $host "sudo bash -c \"echo '/dev/mapper/vg_ocp-etcd /var/lib/etcd xfs defaults 0 0' >> /etc/fstab\" "
   ssh -tt $host "sudo mkdir -p /var/lib/etcd; sudo mount /var/lib/etcd"
   
   #read -p "press any key"
fi

# configure Docker Storage Setup to use this VG
ssh -tt $host "sudo bash -c \"echo \"VG=vg_ocp\" > /etc/sysconfig/docker-storage-setup\" ; sudo docker-storage-setup "

#read -p "press any key"

done
