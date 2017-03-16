#!/bin/bash -e

useradd mpadmin
mkdir /home/mpadmin/.ssh
wget --no-check-certificate \
    'https://raw.githubusercontent.com/temenostech/Temenos-PaaS-infra/master/keys/key.pub?token=AD72V3JsBcJ1wvkYRor9hbkYOPN_g8okks5YyTbfwA%3D%3D' \
    -O /home/mpadmin/.ssh/authorized_keys
chmod 755 /home/mpadmin/.ssh
chmod 400 /home/mpadmin/.ssh/authorized_keys
chown -R mpadmin /home/mpadmin/.ssh
