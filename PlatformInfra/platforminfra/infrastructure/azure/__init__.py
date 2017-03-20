"""Azure Infrastructure module."""
from .. import Infrastructure
from . import dependencies

from azure.common.credentials import ServicePrincipalCredentials
from azure.mgmt.resource import ResourceManagementClient
from azure.mgmt.storage import StorageManagementClient
from azure.mgmt.network import NetworkManagementClient
# from azure.mgmt.compute import ComputeManagementClient
# from azure.mgmt.dns import DnsManagementClient


def getCredentials(template):
    """Given provider details Get the Credentials."""
    for provider in template:
        if "azure" in provider:
            for details in provider['azure']:
                if "config" in details:
                    for configItem in details['config']:
                        if "credentials" in configItem:
                            return configItem["credentials"]
                        else:
                            return {
                                'error': 'No credentials in config'
                            }
                else:
                    return {'error': 'No config found in Azure provider'}
        else:
            return {'error': 'No Azure provider details'}
    return {'error': 'No Credentials found for Azure'}


def getConfig(template):
    """Given provider details Get the Credentials."""
    for provider in template:
        if "azure" in provider:
            for details in provider['azure']:
                if "config" in details:
                    return details
                else:
                    return {'error': 'No config found in Azure provider'}
        else:
            return {'error': 'No Azure provider details'}


def getResources(template):
    """Given a list of Resources reply with an ordered Execution list."""
    deploymentOrder = {"resources": dependencies.getOrderedList(template)}
    return deploymentOrder


class Azure(Infrastructure):
    """Azure class for Generic Azure operations."""

    def __init__(self, config):
        """The Azure Class."""
        Infrastructure.__init__(self, 'Azure')
        self.credentials = getCredentials(config['provider'])
        self.config = getConfig(config['provider'])
        self.resources = getResources(config['services'])
        self.authAccount = ServicePrincipalCredentials(
            client_id=self.credentials['client_id'],
            secret=self.credentials['secret'],
            tenant=self.credentials['tenant']
        )

    def resourceGroupAvailable(self, rg):
        """Test to See if TG is available."""
        resource_client = ResourceManagementClient(
            self.authAccount, self.credentials['subscription_id']
        )
        return resource_client.resource_groups.check_existence(rg)

    def resourceGroup(self, rg):
        """Create a RG if not already created."""
        resource_client = ResourceManagementClient(
            self.authAccount, self.credentials['subscription_id']
        )
        self.resourceGroup = rg
        if not self.resourceGroupAvailable(self.resourceGroup):
            resource_client.resource_groups.create_or_update(
              self.resourceGroup,
              {
                'location': self.config['region']
              }
            )
        return self.resourceGroup

    def storageAccountAvailable(self, sa):
        """Test to see if a SA is available."""
        storage_client = StorageManagementClient(
            self.authAccount, self.credentials['subscription_id']
        )
        availability = storage_client.storage_accounts.check_name_availability(
            sa
        )
        return availability.name_available

    def storageAccount(self, sa):
        """Create a SA if not already created."""
        storage_client = StorageManagementClient(
            self.authAccount, self.credentials['subscription_id']
        )
        self.storageAccount = sa
        if self.storageAccountAvailable(self.storageAccount):
            sa_async_op = storage_client.storage_accounts.create(
              self.resourceGroup,
              self.storageAccount,
              {
                'sku': {'name': 'standard_lrs'},
                'kind': 'storage',
                'location': self.config['region']
              }
            )
            sa_async_op.wait()

    def network(self, network, id, tags):
        """Create networks."""
        network_client = NetworkManagementClient(
            self.authAccount, self.credentials['subscription_id']
        )
        params = {
           'location': self.config['region'],
           'address_space': {
             'address_prefixes': [network['cidr']]
           }
        }
        if len(tags) > 0:
            params["tags"] = tags
        async_vnet_creation = network_client.virtual_networks.create_or_update(
          self.resourceGroup,
          id,
          params
        )
        async_vnet_creation.wait()
        async_subnet_creation = network_client.subnets.create_or_update(
          self.resourceGroup,
          id,
          id + "1",
          {'address_prefix': network['subnet']}
        )
        return async_subnet_creation.result()
