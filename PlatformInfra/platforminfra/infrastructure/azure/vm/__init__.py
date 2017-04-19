"""Module for managing VM's."""
from azure.mgmt.compute import ComputeManagementClient
from azure.mgmt.network import NetworkManagementClient
from azure.storage.blob import BlockBlobService
from azure.mgmt.storage import StorageManagementClient
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

    def generateImageReference(self, os=dict):
        """Generate an image_reference."""
        imageReference = {
          'publisher': os.get('publisher', "RedHat"),
          'offer': os.get('offer', 'RHEL'),
          'sku': os.get('sku', '7.2'),
          'version': os.get('version', 'latest')
        }
        return imageReference

    def getStorageDisks(self, filter):
        """Get a list of Storage disks."""
        saKey = self.getStorageAccountKey()
        disks = list()
        blockBlobService = BlockBlobService(
            account_name=self.storageAccount,
            account_key=saKey
        )
        blobs = blockBlobService.list_blobs('system')
        for blob in blobs:
            print('blob name {}'.format(blob.name))
            print("filter = {}".format(filter))
            if 'vhd' in blob.name:
                print('has vhd')
                if filter in blob.name:
                    print("has filter {}".format(filter))
                    disks.append(blob.name)
        return disks

    def getStorageAccountKey(self):
        """Return a Storage account Key."""
        strClient = StorageManagementClient(
            self.authAccount, self.credentials['subscription_id']
        )
        saKeys = strClient.storage_accounts.list_keys(
            self.resourceGroup,
            self.storageAccount
        )
        return saKeys.keys[0].value

    def getImage(self, image):
        """Generate the Image URL for `image`."""
        baseUrl = "https://{}.blob.core.windows.net/".format(
            self.storageAccount
        )
        container = "system"
        filter = image['os'] + '/' + image['type'] + "_" + image['build']
        disks = self.getStorageDisks(filter)
        for item in disks:
            disk = item

        if len(disks) == 1:
            return baseUrl + container + disk
        elif disks:
            raise Exception({'error': 'no disk found for {}'.format(image)})
        else:
            raise Exception({'error': 'Found too many disks'})

    def generateStorageProfile(
        self,
        tags,
        vmName,
        persistData=False,
        os=None,
        image=None
    ):
        """Generate the Storage profile for a VM."""
        createOption = "Empty"
        if persistData:
            createOption = "Attach"
        storageProfile = {
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
        }
        osType = {
            'redhat': 'Linux',
            'windows': 'Windows'
        }
        if image:
            try:
                storageProfile['os_disk'] = {
                    'name': vmName + 'disk',
                    'caching': 'ReadWrite',
                    'create_option': 'fromImage',
                    'os_type': osType[image['os']],
                    'vhd': {
                        'image': self.getImage(image),
                        'uri': 'https://{}.blob.core.windows.net/{}/{}'.format(
                            self.storageAccount,
                            tags['uuid'],
                            vmName + '.vhd'
                         )
                    },
                },
            except:
                raise
        else:
            if os:
                storageProfile['image_reference'] =\
                    self.generateImageReference(os)
            else:
                storageProfile['image_reference'] =\
                    self.generateImageReference({})
            storageProfile['os_disk'] = {
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
        return storageProfile

    def generateParams(
        self,
        nicId,
        vmName,
        asId,
        tags,
        persistData=False,
        os=None,
        image=None
    ):
        """Create the VM parameters structure.

        generateParams can take an os dictionary that containes other OS
        versions i.e.::
            {
                'publisher': 'RedHat',
                'offer': 'RHEL',
                'sku': '7.2',
                'version': 'latest'
            }

        if Image is passed in a custom image can be used tyo create a Vm::
            {
                'os': 'redhat',
                'type': 't24',
                'build': '32'
            }
        """
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
            'storage_profile': self.generateStorageProfile(
                tags,
                vmName,
                persistData,
                os,
                image
            ),
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
