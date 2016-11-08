#!/bin/bash
export AWS_ACCESS_KEY_ID='AKIAJBA2IIPAYO3ESTKA'
export AWS_SECRET_ACCESS_KEY='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'



if [[ $1 == "--force" ]]; then
  echo "Forcing remove of servers with out attempting to unsubscribe"
  echo "Are you sure you wish to continue? Type 'yes' to continue"
  read ans
  if [ $ans == 'yes' ]; then
    terraform destroy ./plans/
  fi
else
  echo "Removing subscriptions from ALL HOSTS"
  ansible all -u ec2-user --private-key=keys/key.pem -m shell -a "subscription-manager remove --all; subscription-manager unregister"
  rc=$?
  if [[ $rc == "0" ]]; then
    echo "Success"
    echo "Stopping Instances prior to termination"
    ansible all -u ec2-user --private-key=keys/key.pem -m shell -a "shutdown -h now"
    terraform destroy ./plans/
  else
    echo "Failed to unsubscribe all hosts or they are already unsubscribed."
    echo "Ensure all systems unsubscribed and then add the --force option"
  fi
fi
