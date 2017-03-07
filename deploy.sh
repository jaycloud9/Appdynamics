#!/bin/bash

if [[ $1 != "" ]]; then
  provider=$1
  shift
  if [[ $provider == 'aws' || $provider == 'azure' ]]; then
    echo "Executing against provider: $provider"
    echo "Executing provisioning"
    service=$1
    env=$2
    python infra_provision.py create $provider $service $env
    if [[ $provider == "aws" ]]; then
      export AWS_ACCESS_KEY_ID='AKIAJBA2IIPAYO3ESTKA'
      export AWS_SECRET_ACCESS_KEY='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'
      user="ec2-user"
      inventory= "../inventory/ec2.py"
    else
      user=mpadmin
      inventory="../inventory/azure_rm.py"
    fi
    playbook=$3
    echo "Running configuration"
    chmod 400 ../keys/key.pem
    export ANSIBLE_HOST_KEY_CHECKING=False
    ansible-playbook -i $inventory $playbook  -u $user --private-key=../keys/key.pem --extra-vars "platform=$provider" --limit $service-$env-build --vault-password-file ~/vault-password
  else
    echo "Please specify a valid provider: aws | azure"
    exit 1
  fi
else
  echo "Please specify an infrastructure provider. Valid options are: aws | azure"
  exit 1
fi
