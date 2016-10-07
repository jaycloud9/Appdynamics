# Temenos-PaaS

*Requirements*

You will need the hosts defined in ansible/hosts in your ssh config with password less auth configured

This repository contains some automation for the PaaS in dtion to the standard redhat install with ansible.

to run the plays here do the following

```
ansible-playbook -b <playbook>
```
 
For example
```
cd ansible
ansible-playbook -b playbook/rhos-base.yaml

```

*NB* This will only currently work on cluster1, to use cluster2 use the following (untested)

```
ansible-playbook -b ansible-hosts-c2 playbook/rhos-pase.yaml
```

# WARNING!

This repo is temporary, we need to re-factor ansible to use the correct folder structure and roles
