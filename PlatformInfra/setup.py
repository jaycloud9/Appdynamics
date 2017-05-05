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
        'azure-common==1.1.4',
        'msrest==0.4.6',
        'msrestazure==0.4.7',
        'azure-mgmt-storage==0.31.0',
        'azure-storage==0.34.0',
        'azure-mgmt-resource==0.31.0',
        'azure-mgmt-network==0.30.0',
        'azure-mgmt-compute==0.33.0',
        'azure-mgmt-dns==1.0.0',
        'python-jenkins',
        'python-gitlab',
        'pyyaml',
        'uwsgi',
        'pdoc',
        'PyJWT'
    ],
    test_suite='tests',
    tests_require=[
        'dnspython',
        'unittest-xml-reporting'
    ]
)
