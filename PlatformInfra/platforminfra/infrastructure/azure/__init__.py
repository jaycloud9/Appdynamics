"""Azure Infrastructure module."""
from .. import Infrastructure
from . import dependencies


def getCredentials(template):
    """Given provider details Get the Credentials."""
    for provider in template:
        if "azure" in provider:
            for details in provider['azure']:
                if "config" in details:
                    for configItem in details['config']:
                        if "credentials" in configItem:
                            return configItem
                        else:
                            return {
                                'error': 'No credentials in config'
                            }
                else:
                    return {'error': 'No config found in Azure provider'}
        else:
            return {'error': 'No Azure provider details'}
    return {'error': 'No Credentials found for Azure'}


def getResources(template):
    """Given a list of Resources reply with an ordered Execution list."""
    deploymentOrder = {'resources': dependencies.getOrderedList(template)}
    return deploymentOrder


class Azure(Infrastructure):
    """Azure class for Generic Azure operations."""

    def __init__(self, config):
        """The Azure Class."""
        Infrastructure.__init__(self, 'Azure')
        self.credentials = getCredentials(config['provider'])
        self.resources = getResources(config['services'])

    def authenticate(self):
        """Authenticate against Azure platfrom."""
        return self.credentials
