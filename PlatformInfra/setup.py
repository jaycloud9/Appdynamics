"""Set's up the platforminfra app."""
import sys
from setuptools import setup

if sys.version_info < (3, 5):
    sys.exit('Python < 3.5 is not supported')

setup(
    name='platforminfra',
    packages=['platforminfra'],
    version='0.0.4',
    include_package_data=True,
    install_requires=[
        'flask',
        'azure-common',
        'msrest',
        'msrestazure',
        'azure-mgmt-storage',
        'azure-storage',
        'azure-mgmt-resource',
        'azure-mgmt-network',
        'azure-mgmt-compute',
        'azure-mgmt-dns',
        'python-jenkins',
        'python-gitlab',
        'pyyaml'

    ],
    tests_require=[
        'dnspython'
    ]
)
