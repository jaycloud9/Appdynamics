"""Azure Infrastructure module."""
# from .. import Infrastructure
from . import dependencies
from .vm import Vm
from .loadBalancer import LoadBalancer


from azure.common.credentials import ServicePrincipalCredentials
from azure.mgmt.resource import ResourceManagementClient
from azure.mgmt.storage import StorageManagementClient
from azure.mgmt.network import NetworkManagementClient
from azure.mgmt.compute import ComputeManagementClient
from azure.mgmt.dns import DnsManagementClient
from msrestazure.azure_exceptions import CloudError
from multiprocessing import Process, Queue, Lock


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
        result = resClient.resource_groups.check_existence(rg)
        return result

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

    def addDNS(self, ip, record, domain='dev.temenos.cloud'):
        """Add DNS Record."""
        print("Adding DNS Record")
        dnsClient = DnsManagementClient(
            self.authAccount, self.credentials['subscription_id']
        )
        try:
            dnsClient.record_sets.create_or_update(
                "mp_dev_core",
                domain,
                record,
                'A',
                {
                    "ttl": 300,
                    "arecords": [{
                        "ipv4_address": ip
                    }]
                }
            )
        except CloudError as e:
            raise Exception(e)

        return record + "." + domain

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

        if not netFound:
            asyncNetCreation = netClient.virtual_networks.create_or_update(
              self.resourceGroup,
              netName,
              params
            )
            asyncNetCreation.wait()
        # This will need to loop when we want more than 1 subnet per network
        if not subFound:
            subNetName = netName + "sub1"
            asyncSubnetCreation = netClient.subnets.create_or_update(
              self.resourceGroup,
              netName,
              subNetName,
              {'address_prefix': network['subnet']}
            )
            asyncSubnetCreation.wait()
            subNets.put({
                'name': netName + "sub1",
                'subnet': asyncSubnetCreation.result()
            })
        else:
            subNets.put({
                'name': netName + "sub1",
                'subnet': network.subnets[0]
            })

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
        nsgCreated = False
        try:
            asyncNsgOp = netClient.network_security_groups.get(
                self.resourceGroup,
                nsgName
            )
            asyncNsgOp.wait()
            nsg = asyncNsgOp.result()
            return nsg
        except:
            pass
        if not nsgCreated:
            aNsgOp = netClient \
                .network_security_groups.create_or_update(
                    self.resourceGroup,
                    nsgName,
                    rules
                )
            aNsgOp.wait()
            nsg = aNsgOp.result()
            return nsg

    def generateNicParams(self, vm, vmName, subnet, pubIP):
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
        if 'beId' in vm:
            ipConfig[0]['load_balancer_backend_address_pools'] = [{
                'id': vm['beId']
            }]

        params['ip_configurations'] = ipConfig
        return params

    def nic(self, vm, vmName, subnet):
        """Create a Network interface for a vm."""
        netClient = NetworkManagementClient(
            self.authAccount, self.credentials['subscription_id']
        )
        pubIPName = vmName + "pubip"
        asycPubIPCreation = netClient.public_ip_addresses.create_or_update(
          self.resourceGroup,
          pubIPName,
          {
            'public_ip_allocation_method': 'Dynamic',
            'location': self.config['region'],
            'public_ip_address_version': 'IPv4'
          }
        )
        asycPubIPCreation.wait()
        pubIP = asycPubIPCreation.result()
        nicParams = self.generateNicParams(vm, vmName, subnet, pubIP)
        asyncNicCreation = netClient.network_interfaces.create_or_update(
          self.resourceGroup,
          vmName + "nic",
          nicParams
        )
        details = dict()
        details['public_ip_name'] = pubIPName
        details['nic'] = asyncNicCreation.result()
        return details

    def vmWorker(self, opts, vm, vmName, tags, asInfo, subnet, vmQ, lock):
        """Worker to create a VM."""
        tmpVm = Vm(opts)
        lock.acquire()
        vmNic = self.nic(vm, vmName, subnet)
        lock.release()
        tmpVm.generateParams(
            vmNic['nic'].id,
            vmName,
            asInfo.id,
            tags
        )
        tmpVm.create(vmName, vmNic, vmQ)

    def virtualMachine(self, vm, tags, subnet, vmQueue):
        """Create a VM."""
        print("Creating VMs: {}".format(vm['name']))
        cmpClient = ComputeManagementClient(
            self.authAccount, self.credentials['subscription_id']
        )
        asName = self.id + '-as' + vm['name']
        asInfo = cmpClient.availability_sets.create_or_update(
          self.resourceGroup,
          asName,
          {
            'location': self.config['region'],
            'tags': tags
          }
        )
        vmProcList = list()
        opts = dict()
        opts['config'] = self.config
        opts['sa'] = self.storageAccount
        opts['rg'] = self.resourceGroup
        opts['authAccount'] = self.authAccount
        opts['credentials'] = self.credentials
        vmQ = Queue()
        lock = Lock()
        results = list()
        i = 0
        while i < vm['count']:
            i = i + 1
            tmpStr = self.id + vm['name'] + str(i)
            vmName = ''.join(e for e in tmpStr if e.isalnum())
            p = Process(
                target=self.vmWorker,
                args=(opts, vm, vmName, tags, asInfo, subnet, vmQ, lock)
            )
            vmProcList.append(p)
            p.start()
        for proc in vmProcList:
            # Wait for all VM's to create
            proc.join()
            results.append(vmQ.get())

        vmQueue.put({'servers': vm['name'], 'vms': results})

    def lbWorker(self, opts, lb, tags):
        """Worker to create a LB."""
        tmpLb = LoadBalancer(opts, lb, tags)
        result = tmpLb.create()
        return result

    def loadBalancer(self, lb, tags):
        """Create Load Balancer."""
        opts = dict()
        opts['config'] = self.config
        opts['sa'] = self.storageAccount
        opts['rg'] = self.resourceGroup
        opts['authAccount'] = self.authAccount
        opts['credentials'] = self.credentials

        return self.lbWorker(opts, lb, tags)
