# WARNING!

This repo is temporary, we need to re-factor ansible to use the correct folder structure and roles

# Ansible

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

# Deploying a new Openshift

You will need the following before running the scripts
- Network configured
- Loadbalancers
- Servers
- SSH configuration for the servers
- Servers named correctly
- Ansible hosts file (as ansible/hosts/ansible-hosts-c2)
- DNS for each load balancer
  - cluster*X*.temenosgroup.com A record to Loadbalancer with master nodes attached (https, persistant connection by IP & protocol)
  - apps.cluster*X*.temenosgroup.com A record to Loadbalancer with appcontr nodes attached (https, persistant connection by IP & protocol)
- SSL
  - Static for cluster*X*.temenosgroup.com
  - wildcard for apps.cluster*X*.temenosgroup.com

Once that has been considered, follow [This Readme](deployscripts/README.md)
