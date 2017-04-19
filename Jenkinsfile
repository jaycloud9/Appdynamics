#!/usr/bin/env groovy

def pyshell(command) {
  sh """
    export PATH=${PYTHON_PATH}/bin:$PATH
    export LD_LIBRARY_PATH=${PYTHON_PATH}/lib
    echo $PATH
    alias python=python3.5
    alias pip=pip3.5
    ${command}
  """
}

if (env.BRANCH_NAME == 'master') {
  stage('package') {
    node {
    sh 'rm -rf platform_infra_api*.rpm'
    sh 'bash -l -c "rvm use 1.9.3;fpm --rpm-os linux  -s dir -t rpm -n platform_infra_api --after-install ./scripts/after_install.sh --version $BUILD_NUMBER ./PlatformInfra=/opt"'
    }
  }
  stage('Promote') {
    sh 'chmod 400 infra/keys/key.pem ; scp -o StrictHostKeyChecking=no -o UserKnownHostsFile=/dev/null -i infra/keys/key.pem infra/platform_infra_api*.rpm mpadmin@51.141.31.84:/home/mpadmin/'
    sh 'ssh -o StrictHostKeyChecking=no -o UserKnownHostsFile=/dev/null -i infra/keys/key.pem mpadmin@51.141.31.84 "sudo mv /home/mpadmin/*.rpm /temenos-artificats ;sudo chown root:root /temenos-artificats/*.rpm; sudo createrepo --update /temenos-artificats/"'
  }
} else if (env.BRANCH_NAME == 'stable') {
  stage('Deploy') {
    git branch: 'master', credentialsId: '6a40fcf8-c20b-463d-bd69-d483304049f2', url: 'git@github.com:temenostech/Temenos-PaaS-config.git'
    sh 'chmod 400 ./keys/key.pem;export ANSIBLE_ROLES_PATH="../roles"'
    sh 'export ANSIBLE_CONFIG="ansible.cfg"'
    sh """cat <<EOF > ./new.ini
    [azure]
    tags=uuid:${env.UUID}
    EOF"""
    sh 'export ANSIBLE_HOST_KEY_CHECKING=False;export AZURE_INI_PATH=./new.ini;ansible-playbook -i ./inventory/azure_rm.py --vault-password-file ~/vault-password  -u mpadmin --private-key=./infra/keys/key.pem master.yml'
  }
} else {
  stage('Install Python 3.5') {
    node {
      deleteDir()
      PYTHON_PATH = '/tmp/py3.5.1'
      def folder = new File( PYTHON_PATH )
      if ( !folder.exists() ) {
        sh 'wget https://www.python.org/ftp/python/3.5.1/Python-3.5.1.tgz'
        sh 'tar -xzvf Python-3.5.1.tgz'
        dir('Python-3.5.1') {
          sh "./configure --prefix=${PYTHON_PATH}"
          sh 'make'
          sh 'make altinstall'
        }
      } else {
        echo "Python 3.5 already installed"
      }

      pyshell('python --version')
    }
  }

  stage('Install PlatformInfra Dependencies') {
    node{
      dir('platformInfraApi') {
        checkout scm
        dir('PlatformInfra') {
          pyshell('pip install -e .')
        }
      }
    }
  }
  stage('test') {
    node {
      dir('platformInfraApi') {
        dir('PlatformInfra') {
          pyshell('python -W ignore setup.py test')
        }
      }
    }
  }
}
