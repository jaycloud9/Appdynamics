#!/bin/bash

tf_root=./terraform/providers/


if [[ $1 != "" ]]; then
  provider=$1
  shift

  if [[ $provider == 'aws' || $provider == 'azure' ]]; then
    
    echo "Executing against provider: $provider"
    if [[ $1 != "" ]]; then
      env=$1
      shift
      echo "Executing provisioning"
      #terraform apply -state=$tf_path/terraform.tfstate -var-file=$tf_path/terraform.tfvars $tf_path
      python oscp_infra.py
      if [[ $provider == "aws" ]]; then
        export AWS_ACCESS_KEY_ID='AKIAJBA2IIPAYO3ESTKA'
        export AWS_SECRET_ACCESS_KEY='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'
        user="ec2-user"
        inventory= "inventory/ec2.py"
      else
        user=tfadmin
        inventory="inventory/azure_rm.py"
      fi
      ansible-playbook -i $inventory playbook.yml -K -u $user --private-key=keys/key.pem --extra-vars "platform=$provider"
    else
      echo "You must specify an environment"
      exit 1
    fi
  else
    echo "Please specify a valid provider: aws | azure"
    exit 1
  fi
else
  echo "Please specify an infrastructure provider. Valid options are: aws | azure"
  exit 1
fi
