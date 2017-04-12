node {
  git branch: 'master', credentialsId: '6a40fcf8-c20b-463d-bd69-d483304049f2', url: 'git@github.com:temenostech/Temenos-PaaS-config.git'
  stage 'Build T24'

    dir('roles/t24') {
            git branch: 'master', credentialsId: '6a40fcf8-c20b-463d-bd69-d483304049f2', url: 'git@github.com:temenostech/Temenos-PaaS-app.git'
            }

    dir('infra') {
            git branch: 'master', credentialsId: '6a40fcf8-c20b-463d-bd69-d483304049f2', url: 'git@github.com:temenostech/Temenos-PaaS-infra.git'
    }

 stage 'Deploy'
 sh 'chmod 400 ./keys/key.pem; export ANSIBLE_ROLES_PATH="../roles"'
 sh 'export ANSIBLE_CONFIG="ansible.cfg"'
 sh 'export ANSIBLE_HOST_KEY_CHECKING=False;export AZURE_INI_PATH=./new.ini;ansible-playbook -i ./inventory/ansible_hosts --vault-password-file ~/vault-password --limit Type_t24  -u mpadmin --private-key=./infra/keys/key.pem master.yml'
}
