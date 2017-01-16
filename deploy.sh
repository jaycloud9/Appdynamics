#!/bin/bash

if [[ $1 != "" ]]; then
  provider=$1
  shift
  if [[ $provider == 'aws' || $provider == 'azure' ]]; then
    echo "Executing against provider: $provider"
    echo "Executing provisioning"
    python oscp_infra.py create
    if [[ $provider == "aws" ]]; then
      export AWS_ACCESS_KEY_ID='AKIAJBA2IIPAYO3ESTKA'
      export AWS_SECRET_ACCESS_KEY='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'
      user="ec2-user"
      inventory= "inventory/ec2.py"
    else
      user=mpadmin
      inventory="inventory/azure_rm.py"
    fi
    echo "Running configuration"
#    ansible-playbook -i $inventory playbook.yml -u $user --private-key=keys/key.pem --extra-vars "platform=$provider"
  else
    echo "Please specify a valid provider: aws | azure"
    exit 1
  fi
else
  echo "Please specify an infrastructure provider. Valid options are: aws | azure"
  exit 1
fi
