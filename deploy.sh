#!/bin/bash
export AWS_ACCESS_KEY_ID='AKIAJBA2IIPAYO3ESTKA'
export AWS_SECRET_ACCESS_KEY='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'

terraform apply ./plans/
ansible-playbook playbook.yml -u ec2-user --private-key=keys/key.pem