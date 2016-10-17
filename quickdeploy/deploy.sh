
export AWS_ACCESS_KEY_ID='AKIAJBA2IIPAYO3ESTKA'
export AWS_SECRET_ACCESS_KEY='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'

terraform apply
ansible-playbook playbook.yml -i inventory/ec2.py