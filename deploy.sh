#!/bin/bash

if [[ $1 != "" ]]; then
  provider=$1
  user="ec2-user"
  shift

  if [[ $provider == 'aws' || $provider == 'azure' ]]; then
    echo "Executing against provider: $provider"
    if [[ $1 != "" ]]; then
      env=$1
      shift
      export AWS_ACCESS_KEY_ID='AKIAJBA2IIPAYO3ESTKA'
      export AWS_SECRET_ACCESS_KEY='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'
      terraform apply ./plans/$provider
      ansible-playbook playbook.yml -u $user --private-key=keys/key.pem
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
