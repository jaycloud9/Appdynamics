def pubip
node {
  stage 'Git Checkout'
  git branch: 'shobin/jenkins-pipeline', credentialsId: 'c45cd60b-fda6-4137-84a3-530860ca3d5e', url: 'git@github.com:temenostech/Temenos-PaaS-infra.git'
  stage 'Build Infra'
  sh 'python infra_provision.py create azure t24dev $BUILD_NUMBER'
  stage 'Checkout T24'
  dir('roles/t24') {
  git credentialsId: 'c45cd60b-fda6-4137-84a3-530860ca3d5e', url: 'git@github.com:temenostech/Temenos-PaaS-app.git'
   }
  sh 'export ANSIBLE_ROLES_PATH="$(pwd)/roles"'
  sh 'export ANSIBLE_CONFIG="ansible.cfg"'
  sh 'python inventory/azure_rm.py --list --resource-groups t24dev-$BUILD_NUMBER-t24 | python -m json.tool | grep public_ip | head -1 | cut -d ":" -f2 | cut -d "\\"" -f2 > .resource'
  env.PUBIP = readFile('.resource').trim()
  stage 'Deploy T24'
  sh """cat <<EOF > ./temenos-host
[temenos-t24]
${env.PUBIP} ansible_ssh_user=mpadmin ansible_ssh_private_key_file=/var/lib/jenkins/.ssh/temenos.key.pem ansible_ssh_common_args='-o UserKnownHostsFile=/dev/null -o StrictHostKeyChecking=no -i /var/lib/jenkins/.ssh/temenos.key.pem'
EOF"""
 sh 'ansible-playbook -i temenos-host  t24.yml'
 stage 'Destroy Infra'
 sh 'python infra_provision.py destroy azure t24dev $BUILD_NUMBER'

}