"""Azure Infrastructure module."""
# from .. import Infrastructure
from . import dependencies
from .vm import Vm


from azure.common.credentials import ServicePrincipalCredentials
from azure.mgmt.resource import ResourceManagementClient
from azure.mgmt.storage import StorageManagementClient
from azure.mgmt.network import NetworkManagementClient
from azure.mgmt.compute import ComputeManagementClient
# from azure.mgmt.dns import DnsManagementClient
from multiprocessing import Process


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


# class Azure(Infrastructure):
class Azure(object):
    """Azure class for Generic Azure operations."""

    def __init__(self, config, id):
        """The Azure Class."""
        # Infrastructure.__init__(self, 'Azure')
        self.credentials = getCredentials(config['provider'])
        self.config = getConfig(config['provider'])
        self.id = id
        self.resources = getResources(config['services'])
        self.authAccount = ServicePrincipalCredentials(
            client_id=self.credentials['client_id'],
            secret=self.credentials['secret'],
            tenant=self.credentials['tenant']
        )

    def resourceGroupAvailable(self, rg):
        """Test to See if TG is available."""
        resClient = ResourceManagementClient(
            self.authAccount, self.credentials['subscription_id']
        )
        return resClient.resource_groups.check_existence(rg)

    def resourceGroup(self, rg):
        """Create a RG if not already created."""
        resClient = ResourceManagementClient(
            self.authAccount, self.credentials['subscription_id']
        )
        self.resourceGroup = rg
        if not self.resourceGroupAvailable(self.resourceGroup):
            resClient.resource_groups.create_or_update(
              self.resourceGroup,
              {
                'location': self.config['region']
              }
            )
        return self.resourceGroup

    def storageAccountAvailable(self, sa):
        """Test to see if a SA is available."""
        strClient = StorageManagementClient(
            self.authAccount, self.credentials['subscription_id']
        )
        availability = strClient.storage_accounts.check_name_availability(
            sa
        )
        return availability.name_available

    def storageAccount(self, sa):
        """Create a SA if not already created."""
        strClient = StorageManagementClient(
            self.authAccount, self.credentials['subscription_id']
        )
        self.storageAccount = sa
        if self.storageAccountAvailable(self.storageAccount):
            saAsyncOp = strClient.storage_accounts.create(
              self.resourceGroup,
              self.storageAccount,
              {
                'sku': {'name': 'standard_lrs'},
                'kind': 'storage',
                'location': self.config['region']
              }
            )
            saAsyncOp.wait()

    def network(self, network, netName, tags, subNets):
        """Create networks."""
        netClient = NetworkManagementClient(
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

        subFound = False
        netFound = False
        try:
            network = netClient.virtual_networks.get(
                self.resourceGroup,
                netName
            )
            if network.provisioning_state == 'Succeeded':
                netFound = True
            if len(network.subnets) != 0:
                subFound = True
        except:
            pass

        print("netFound: {} subFound: {}".format(netFound, subFound))
        if not netFound:
            asyncVnetCreation = netClient.virtual_networks.create_or_update(
              self.resourceGroup,
              netName,
              params
            )
            asyncVnetCreation.wait()
            print("Network Created: {}".format(netName))
        # This will need to loop when we want more than 1 subnet per network
        if not subFound:
            asyncSubnetCreation = netClient.subnets.create_or_update(
              self.resourceGroup,
              netName,
              netName + "sub1",
              {'address_prefix': network['subnet']}
            )
            asyncSubnetCreation.wait()
            subNets.put(asyncSubnetCreation.result())
        else:
            subNets.put(network.subnets[0])

    def nsg(self, vm):
        """Create NSG."""
        netClient = NetworkManagementClient(
            self.authAccount, self.credentials['subscription_id']
        )
        nsgName = self.id + vm['name'] + "Nsg"
        rules = {
          "location": self.config['region'],
          "security_rules": [
            {
              "description": "SSH Access",
              "protocol": "Tcp",
              "source_port_range": "*",
              "source_address_prefix": "*",
              "destination_address_prefix": "*",
              "destination_port_range": "22",
              "access": "Allow",
              "priority": 100,
              "direction": "Inbound",
              "name": nsgName + "-22-nsg"
            },
            {
              "description": nsgName + "-" + str(vm['service_port']),
              "protocol": "Tcp",
              "source_port_range": "*",
              "source_address_prefix": "*",
              "destination_address_prefix": "*",
              "destination_port_range": str(vm['service_port']),
              "access": "Allow",
              "priority": 110,
              "direction":"Inbound",
              "name": nsgName + "-" + str(vm['service_port']) + "-nsg"
            }
          ]
        }
        asyncNsgOp = netClient.network_security_groups.create_or_update(
            self.resourceGroup,
            nsgName,
            rules
        )
        asyncNsgOp.wait()
        nsg = asyncNsgOp.result()
        return nsg

    def generateNicParams(self, vm, vmName, subnet, pubIP, beId):
        """Generate the Nic Parameters."""
        params = {
            'location': self.config['region'],
          }
        ipConfig = [{
          'name': vmName + '-nic',
          'subnet': {
            'id': subnet.id
          },
          'public_ip_address': {
            'id': pubIP.id
          }
        }]

        if 'service_port' in vm:
            nsg = self.nsg(vm)
            params['network_security_group'] = nsg
        if beId:
            ipConfig[0]['load_balancer_backend_address_pools'] = [{'id': beId}]

        params['ip_configurations'] = ipConfig
        return params

    def nic(self, vm, vmName, subnet, beId=None):
        """Create a Network interface for a vm."""
        netClient = NetworkManagementClient(
            self.authAccount, self.credentials['subscription_id']
        )
        pubIPName = vmName + "pubip"
        asyncPubIPCreation = netClient.public_ip_addresses.create_or_update(
          self.resourceGroup,
          pubIPName,
          {
            'public_ip_allocation_method': 'Dynamic',
            'location': self.config['region'],
            'public_ip_address_version': 'IPv4'
          }
        )
        asyncPubIPCreation.wait()
        pubIP = asyncPubIPCreation.result()

        nicParams = self.generateNicParams(vm, vmName, subnet, pubIP, beId)
        print("Create Nic")
        asyncNicCreation = netClient.network_interfaces.create_or_update(
          self.resourceGroup,
          vmName + "nic",
          nicParams
        )
        details = dict()
        details['public_ip_name'] = pubIPName
        details['nic'] = asyncNicCreation.result()
        return details

    def virtualMachine(self, vm, tags, subnet, vmQueue):
        """Create a VM."""
        print("Creating VM")
        cmpClient = ComputeManagementClient(
            self.authAccount, self.credentials['subscription_id']
        )
        print("Creating AS")
        asInfo = cmpClient.availability_sets.create_or_update(
          self.resourceGroup,
          self.id + '-as',
          {
            'location': self.config['region'],
            'tags': tags
          }
        )
        i = 0
        vmProcList = list()
        opts = dict()
        opts['config'] = self.config
        opts['sa'] = self.storageAccount
        opts['rg'] = self.resourceGroup
        opts['authAccount'] = self.authAccount
        opts['credentials'] = self.credentials
        while i < vm['count']:
            i = i + 1
            tmpVm = Vm(opts)
            vmName = self.id + vm['name'].translate({
                None: '` ~!@#$%^&*()=+_[]{}\|;:\'",<>/?.'
            }) + str(i)
            vmNic = self.nic(vm, vmName, subnet)
            tmpVm.generateParams(
                vmNic['nic'].id,
                vmName,
                asInfo.id,
                tags
            )
            p = Process(
                target=tmpVm.create,
                args=(vmName, vmNic, vmQueue)
            )
            vmProcList.append(p)
            p.start()

        for proc in vmProcList:
            # Wait for all VM's to create
            proc.join()
