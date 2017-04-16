"""Module for managing VM's."""
from azure.mgmt.compute import ComputeManagementClient
from azure.mgmt.network import NetworkManagementClient
from msrestazure.azure_exceptions import CloudError


class Vm(object):
    """Class for managing Vm's."""

    def __init__(self, opts):
        """Init vm Class with Azure parent."""
        self.vmParams = dict()
        self.config = opts['config']
        self.storageAccount = opts['sa']
        self.resourceGroup = opts['rg']
        self.authAccount = opts['authAccount']
        self.credentials = opts['credentials']

    def generateParams(self, nicId, vmName, asId, tags, persistData=False):
        """Create the VM parameters structure."""
        createOption = "Empty"
        if persistData:
            createOption = "Attach"
        self.vmParams = {
          'location': self.config['region'],
          'tags': tags,
          'os_profile': {
            'computer_name': vmName,
            'admin_username': self.config['user'],
            'linux_configuration': {
              'ssh': {
                'public_keys': [{
                  'path': '/home/{}/.ssh/authorized_keys'.format(
                    self.config['user']
                    ),
                  'key_data': self.config["public_ssh_key"]
                }]
              }
            }
          },
          'hardware_profile': {
            'vm_size': self.config['server_size']
          },
          'storage_profile': {
            'image_reference': {
              'publisher': 'RedHat',
              'offer': 'RHEL',
              'sku': '7.2',
              'version': 'latest'
            },
            'os_disk': {
              'name': vmName + 'disk',
              'caching': 'None',
              'create_option': 'fromImage',
              'vhd': {
                'uri': 'https://{}.blob.core.windows.net/{}/{}'.format(
                    self.storageAccount,
                    tags['uuid'],
                    vmName + '.vhd'
                 )
              },
            },
            'data_disks': [{
              'name': vmName + 'datadisk1.vhd',
              'disk_size_gb': 200,
              'lun': 0,
              'vhd': {
                'uri': "https://{}.blob.core.windows.net/{}/{}".format(
                    self.storageAccount,
                    tags['uuid'],
                    vmName + 'datadisk1.vhd')
              },
              'create_option': createOption
            }]
          },
          'network_profile': {
              'network_interfaces': [{
                  'id': nicId,
              }]
          },
          'availability_set': {
            'id': asId
          },
        }

    def publicIp(self, pubIpName):
        """Get the Public IP of a VM."""
        netClient = NetworkManagementClient(
            self.authAccount, self.credentials['subscription_id']
        )
        pubIp = netClient.public_ip_addresses.get(
            self.resourceGroup,
            pubIpName)
        return pubIp.ip_address

    def privateIp(self, nic):
        """Get the Private ip address."""
        return nic.ip_configurations[0].private_ip_address

    def create(self, vmName, vmNic, vmQueue):
        """Create a VM."""
        cmpClient = ComputeManagementClient(
            self.authAccount,
            self.credentials['subscription_id']
        )
        try:
            asyncVmCreation = cmpClient.virtual_machines.create_or_update(
              self.resourceGroup,
              vmName,
              self.vmParams
            )
            asyncVmCreation.wait()
            vmQueue.put({
                'name': vmName,
                'public_ip': self.publicIp(vmNic['public_ip_name']),
                'private_ip': self.privateIp(vmNic['nic'])
            })
        except CloudError:
            raise
