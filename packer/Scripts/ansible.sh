#!/bin/bash -eux


# Install EPEL repository.
rpm -ivh http://dl.fedoraproject.org/pub/epel/7/x86_64/e/epel-release-7-9.noarch.rpm

# Install Python Pip
yum -y install python-pip gcc openssl-devel python-devel python-lxml libffi-devel

#Upgrade Pip
pip install --upgrade pip

# Install Ansible.
pip install ansible
