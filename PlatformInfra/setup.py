"""Set's up the platforminfra app."""

from setuptools import setup

setup(
    name='platforminfra',
    packages=['platforminfra'],
    include_package_data=True,
    install_requires=[
        'flask',
    ],
)
