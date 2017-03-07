#!/bin/bash

if [[ $1 != "" ]]; then
  provider=$1
  shift

  if [[ $provider == 'aws' || $provider == 'azure' ]]; then
    echo "Executing against provider: $provider"
    if [[ $provider == "aws" ]]; then
      export AWS_ACCESS_KEY_ID='AKIAJBA2IIPAYO3ESTKA'
      export AWS_SECRET_ACCESS_KEY='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'
      user="ec2-user"
      inventory= "inventory/ec2.py"
    else
      user="mpadmin"
      inventory="inventory/azure_rm.py"
    fi
    if [[ $3 == "--force" ]]; then
      echo "Forcing remove of servers with out attempting to unsubscribe"
      echo "Are you sure you wish to continue? Type 'yes' to continue"
      read ans
      if [ $ans == 'yes' ]; then
        service=$1
        env=$2
        python oscp_infra.py destroy $provider $service $env
      fi
    else
      echo "Removing subscriptions from ALL HOSTS"
      ansible -i $inventory all -u $user --private-key=keys/key.pem -m shell -a "subscription-manager remove --all; subscription-manager unregister"
      rc=$?
      if [[ $rc == "0" ]]; then
        echo "Success"
        echo "Stopping Instances prior to termination"
        ansible -i $inventory all -u $user --private-key=keys/key.pem -m shell -a "shutdown -h now"
        service=$1
        env=$2
        python oscp_infra.py destroy $provider $service $env
      else
        echo "Failed to unsubscribe all hosts or they are already unsubscribed."
        echo "Ensure all systems unsubscribed and then add the --force option"
      fi
		fi
  else
    echo "Please specify a valid provider: aws | azure"
    exit 1
	fi
else
  echo "Please specify an infrastructure provider. Valid options are: aws | azure"
  exit 1
fi
