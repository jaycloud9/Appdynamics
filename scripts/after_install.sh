#!/bin/bash

cd /root/
curl -L https://raw.githubusercontent.com/pyenv/pyenv-installer/master/bin/pyenv-installer | bash
export PATH="/root/.pyenv/bin:$PATH" >> /etc/profile
cd /opt/PlatformInfra
export PATH="/root/.pyenv/bin:$PATH"; eval "$(pyenv virtualenv-init -)"
pyenv install 3.5.1
pyenv shell 3.5.1
make setup
