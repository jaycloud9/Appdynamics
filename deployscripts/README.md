# WARNING!
# WARNING!
### THIS IS UNTESTED 
# WARNING!
# WARNING!

## Pre-Requisites

1, subscribe-hosts.sh
2, install-prereqs.sh
3, configure-storage.sh
4, enable-start-docker.sh

*NB* It will be necessary to find a better way to do the disks (ansible) as each class of host has different requires


## Install

checkout https://github.com/openshift/openshift-ansible and switch to the branch 'release-1.3'
from the ansible directory
```
ansible-playbook -i hosts/ansible-hosts-cX ../openshift-ansible/playbooks/byo/config.yml
```

## Post-installation steps
The creation of PV's in the original deployment document doesn't work

instead use the following 

*Create a template file*

```
apiVersion: v1
kind: PersistentVolume
metadata:
  name: %pv
spec:
  capacity:
    storage: %size
  accessModes:
    -  ReadWriteMany
    -  ReadWriteOnce
  persistentVolumeReclaimPolicy: Recycle
  nfs:
    path: /exports/pv/%pv
    server: c2-rhos-master-1
```

*Create a template file for each PV*
*NB* I don't know why the commenrted line wouldn't work for me when doing it within the original script so creating seperate files seemed to work

```
#!/bin/bash
size=2Gi
for vol in $(seq 1 20)
do
   pv=pv$vol
   sed s/%pv/$pv/g pv-template.yaml | sed s/%size/$size/g > $pv.yaml
   #sed s/%pv/$pv/g pv-template.yaml | sed s/%size/$size/g | oc create ­f ­
done

```

*Create PV's*

```
for i in $(seq 1 20); do cat pv$i.yaml | oc create -f -; done
```
Run ansible
*NB* Will not work eith out modification yet... getting to it...
