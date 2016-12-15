from azure.common.credentials import ServicePrincipalCredentials
from azure.mgmt.resource import ResourceManagementClient
from azure.mgmt.storage import StorageManagementClient
from azure.mgmt.network import NetworkManagementClient
from azure.mgmt.compute import ComputeManagementClient

import configparser

######################################################
#
#     Main Code
#
######################################################

config = configparser.ConfigParser()
config.read('config.ini')

subscription_id = str(config.get('azure','subscription_id'))

credentials = ServicePrincipalCredentials(
    client_id = config.get('azure','client_id'),
    secret = config.get('azure','secret'),
    tenant = config.get('azure','tenant')
)

resource_client = ResourceManagementClient(credentials, subscription_id)
compute_client = ComputeManagementClient(credentials, subscription_id)
storage_client = StorageManagementClient(credentials, subscription_id)
network_client = NetworkManagementClient(credentials, subscription_id)

#print('\nList VMs in subscription')
#for vm in compute_client.virtual_machines.list_all():
#  print("\tVM: {}".format(vm.name))

#TODO: Get all resourves for a resource group if it exists and only create new if they don't exist.
#TODO: Copy VHD to new RG and provision from that one
def main():
  for service in config.sections():
    if service != 'azure':
      ######################################################
      #
      #     Prepare Environment
      #
      ######################################################

      print("Preparing Environment %s" % service)
      print('Create Resource Group')
      rg = service + '-' + config.get(service,'name') + '-' + config.get(service,'stack')
      resource_client.resource_groups.create_or_update(
        rg, 
        {
          'location': config.get(service,'region')
        }
      ).name
      print("Reosource Group %s created" % rg)

      print('Create a storage account')
      sa = service + config.get(service,'name') + config.get(service,'stack')
      storage_async_operation = storage_client.storage_accounts.create(
          rg,
          sa,
          {
              'sku': {'name': 'standard_lrs'},
              'kind': 'storage',
              'location': config.get(service,'region')
          }
      )
      storage_async_operation.wait() 
      print("Storage Account %s created" % sa)

      print("Creating Network")
      subnet = create_network(service, rg)


      create_vm(rg,service, subnet, sa, 'gitlab', config.get(service,'gitlab_count'))


      print("Done")


######################################################
#
#     Functions
#
######################################################

def create_vm(rg, service, subnet, sa, vmtype, count):
  """Create a VM and associated coponents
  """

  i = 1
  while (i <= int(count)):
    vmname = vmtype + str(i)
    print("Creating %s of %s: %s VMs" % (i, count, vmtype))
    print("Creating NIC")
    nic = create_nic(network_client, rg, service, vmname, subnet)

    vm_parameters = create_vm_parameters(nic.id, vmname, 'Standard_A0', sa, service)
    async_vm_creation = compute_client.virtual_machines.create_or_update(
      rg, vmname, vm_parameters)
    async_vm_creation.wait()

    print('Tag Virtual Machine')
    async_vm_update = compute_client.virtual_machines.create_or_update(
      rg,
      vmname,
      {
        'location': config.get(service,'region'),
        'tags': {
          'Environment': config.get(service,'environment'),
          'Stack': config.get(service,'stack'),
          'Owner': config.get(service,'owner'),
          'Type': vmtype
        }
      }
    )
    async_vm_update.wait()

    i = i + 1


def create_network(service, resource_group):
  """Create a Network and subnets.
  """
  # Create VNet
  print('Create Vnet')
  async_vnet_creation = network_client.virtual_networks.create_or_update(
    resource_group,
    resource_group + '-vnet',
    {
      'location': config.get(service,'region'),
      'address_space': {
        'address_prefixes': [config.get(service,'cidr')]
      }
    }
  )
  async_vnet_creation.wait()

  # Create Subnet
  print('Create Subnet')
  async_subnet_creation = network_client.subnets.create_or_update(
    resource_group,
    resource_group + '-vnet',
    resource_group + '-vnet1',
    {'address_prefix': config.get(service, 'subnet')}
  )
  subnet_info = async_subnet_creation.result()
  return subnet_info

def create_nic(network_client, resource_group, service, vmname, subnet_info):
  """Create a Network Interface for a VM.
  """

  # Create Pub IP
  async_pubIP_creation = network_client.public_ip_addresses.create_or_update(
    resource_group,
    resource_group + '-' + vmname + '-ip',
    {
      'public_ip_allocation_method': 'Dynamic',
      'location': config.get(service,'region'),
      'public_ip_address_version': 'IPv4'
    }
  )
  pub_ip = async_pubIP_creation.result()

  # Create NIC
  print('Create NIC')
  async_nic_creation = network_client.network_interfaces.create_or_update(
    resource_group,
    resource_group + vmname + '-nic',
    {
      'location': config.get(service,'region'),
      'ip_configurations': [{
        'name': vmname + '-nic',
        'subnet': {
          'id': subnet_info.id
        },
        'public_ip_address': {
          'id': pub_ip.id
        }
      }]
    }
  )
  return async_nic_creation.result()

def create_vm_parameters(nic_id, vmname, vmsize, sa, service):
  """Create the VM parameters structure.
  """
  return {
    'location': config.get(service,'region'),
    'os_profile': {
      'computer_name': vmname,
      'admin_username': config.get(service,'user'),
      'admin_password': config.get(service,'user_password')
    },
    'hardware_profile': {
      'vm_size': vmsize
    },
    'storage_profile': {
      'os_disk': {
        'os_type': 'Linux',
        'name': vmname + 'disk',
        'caching': 'None',
        'create_option': 'fromImage',
        'vhd': {
          'uri': 'https://{}.blob.core.windows.net/vhds/{}.vhd'.format(
            'mpcoredisks532', vmname)
        },
        'image': {
          'uri': config.get('azure','base_os_vhd')
        },
      },
    },
    'network_profile': {
        'network_interfaces': [{
            'id': nic_id,
        }]
    },
  }

if __name__ == "__main__":
    main()
