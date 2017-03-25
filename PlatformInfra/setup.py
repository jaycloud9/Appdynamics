"""Set's up the platforminfra app."""

from setuptools import setup

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
        'azure-mgmt-resource',
        'azure-mgmt-network',
        'azure-mgmt-compute',
        'azure-mgmt-dns'
    ],
)
