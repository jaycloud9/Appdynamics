#!/bin/bash

tf_root=./terraform/providers/


if [[ $1 != "" ]]; then
  provider=$1
  region="ukwest"
  team="marketplace"
  purpose="oscp"
  shift

  if [[ $provider == 'aws' || $provider == 'azure' ]]; then
    echo "Executing against provider: $provider"
    if [[ $1 != "" ]]; then
      env=$1
      shift
      platform=$region"_"$env"_"$team"_"$purpose
      echo "Platform: $platform"

      tf_path=$tf_root$provider/$platform

      echo "Working directory is $tf_path"
      if [[ $provider == "aws" ]]; then
        export AWS_ACCESS_KEY_ID='AKIAJBA2IIPAYO3ESTKA'
        export AWS_SECRET_ACCESS_KEY='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'
        user="ec2-user"
        inventory= "inventory/ec2.py"
      else
        user="tfadmin"
        inventory="inventory/azure_rm.py"
      fi



			if [[ $1 == "--force" ]]; then
				echo "Forcing remove of servers with out attempting to unsubscribe"
				echo "Are you sure you wish to continue? Type 'yes' to continue"
				read ans
				if [ $ans == 'yes' ]; then
					terraform destroy -state=$tf_path/terraform.tfstate -var-file=$tf_path/terraform.tfvars $tf_path
				fi
			else
				echo "Removing subscriptions from ALL HOSTS"
				ansible -i $inventory all -u $user --private-key=keys/key.pem -m shell -a "subscription-manager remove --all; subscription-manager unregister"
				rc=$?
				if [[ $rc == "0" ]]; then
					echo "Success"
					echo "Stopping Instances prior to termination"
					ansible -i $inventory all -u $user --private-key=keys/key.pem -m shell -a "shutdown -h now"
					terraform destroy -state=$tf_path/terraform.tfstate -var-file=$tf_path/terraform.tfvars $tf_path
				else
					echo "Failed to unsubscribe all hosts or they are already unsubscribed."
					echo "Ensure all systems unsubscribed and then add the --force option"
				fi
			fi
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
