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

#NICE
#TODO: Get all resourves for a resource group if it exists and only create new if they don't exist.
#TODO: Copy VHD to new RG and provision from that one or Provision from one SA to another

#MUST
#TODO: Configure the Lb's for each purpose properly
#TODO: Point DNS at the LB's
#TODO: Delete RG 

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

      print("Creating Network")
      subnet = create_network(service, rg)


      print("Creating Load Balancers")
      lb_info = create_load_balancer(rg, service, 'console')
      console_be_id = lb_info.backend_address_pools[0].id

      lb_info = create_load_balancer(rg, service, 'apps')
      apps_be_id = lb_info.backend_address_pools[0].id

      lb_info = create_load_balancer(rg, service, 'gitlab')
      gitlab_be_id = lb_info.backend_address_pools[0].id

      print("Creating VMs")
      create_vm(rg,service, subnet, 'gitlab', config.get(service,'gitlab_count'), gitlab_be_id)
      create_vm(rg,service, subnet, 'formation', config.get(service,'formation_count'))
      create_vm(rg,service, subnet, 'storage', config.get(service,'storage_count'))
      create_vm(rg,service, subnet, 'master', config.get(service,'master_count'), console_be_id)
      create_vm(rg,service, subnet, 'node_worker', config.get(service,'node_worker_count'), )
      create_vm(rg,service, subnet, 'node_infra', config.get(service,'node_infra_count'), apps_be_id)


      print("Done")


######################################################
#
#     Functions
#
######################################################

def create_vm(rg, service, subnet, vmtype, count, be_id=None):
  """Create a VM and associated coponents
  """

  print('Create availability set')
  availability_set_info = compute_client.availability_sets.create_or_update(
    rg,
    rg + vmtype + '-as',
    {'location': config.get(service,'region')}
  )

  i = 1
  while (i <= int(count)):
    vmname = str(vmtype + str(i)).translate(None, '` ~!@#$%^&*()=+_[]{}\|;:\'",<>/?.')
    print("Creating %s of %s: %s VMs" % (i, count, vmtype))
    print("Creating NIC")
    nic = create_nic(network_client, rg, service, vmname, subnet, be_id)

    vm_parameters = create_vm_parameters(nic.id, vmname, 'Standard_A0', service, availability_set_info.id)
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

def create_nic(network_client, resource_group, service, vmname, subnet_info, be_id=None):
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
  params = { 
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
  if be_id:
    print("Inserting LB param")
    params['ip_configurations'][0]['load_balancer_backend_address_pools'] = [{'id': be_id}]

  async_nic_creation = network_client.network_interfaces.create_or_update(
    resource_group,
    resource_group + vmname + '-nic',
    params
  )
  return async_nic_creation.result()

def create_vm_parameters(nic_id, vmname, vmsize, service, as_id):
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
    'availability_set': {
      'id': as_id
    },
  }

def create_load_balancer(rg, service, purpose):
  lbname = rg + '-' + purpose + '-lb'
  
  # Create PublicIP
  print('Create Public IP')
  public_ip_parameters = {
    'location': config.get(service,'region'),
    'public_ip_allocation_method': 'static',
    'idle_timeout_in_minutes': 4
  }
  async_publicip_creation = network_client.public_ip_addresses.create_or_update(
    rg,
    lbname + '-ip',
    public_ip_parameters
  )
  public_ip_info = async_publicip_creation.result()

  # Building a FrontEndIpPool
  print('Create FrontEndIpPool configuration')
  frontend_ip_configurations = [{
    'name': lbname + '-fip',
    'private_ip_allocation_method': 'Dynamic',
    'public_ip_address': {
      'id': public_ip_info.id
    }
  }]

  # Building a BackEnd address pool
  print('Create BackEndAddressPool configuration')
  backend_address_pools = [{
    'name': lbname + '-bepool'
  }]

  # Building a HealthProbe
  print('Create HealthProbe configuration')
  probes = [{
    'name': lbname + 'http-probe',
    'protocol': 'Http',
    'port': 80,
    'interval_in_seconds': 15,
    'number_of_probes': 4,
    'request_path': 'healthprobe.aspx'
  }]

  # Building a LoadBalancer rule
  print('Create LoadBalancerRule configuration')
  load_balancing_rules = [{
    'name': lbname + '-rule',
    'protocol': 'tcp',
    'frontend_port': 80,
    'backend_port': 80,
    'idle_timeout_in_minutes': 4,
    'enable_floating_ip': False,
    'load_distribution': 'Default',
    'frontend_ip_configuration': {
      'id': construct_fip_id(subscription_id, rg, lbname, lbname + '-fip')
    },
    'backend_address_pool': {
      'id': construct_bap_id(subscription_id, rg, lbname, lbname + '-bepool')
    },
    'probe': {
      'id': construct_probe_id(subscription_id, rg, lbname, lbname + 'http-probe')
    }
  }]

  # Creating Load Balancer
  print('Creating Load Balancer')
  lb_async_creation = network_client.load_balancers.create_or_update(
    rg,
    lbname,
    {
      'location': config.get(service,'region'),
      'frontend_ip_configurations': frontend_ip_configurations,
      'backend_address_pools': backend_address_pools,
      'probes': probes,
      'load_balancing_rules': load_balancing_rules
    }
  )
  lb_info = lb_async_creation.result()

  return lb_info

def construct_fip_id(subscription_id, rg, lbname, fipname):
  """Build the future FrontEndId based on components name.
  """
  return ('/subscriptions/{}'
          '/resourceGroups/{}'
          '/providers/Microsoft.Network'
          '/loadBalancers/{}'
          '/frontendIPConfigurations/{}').format(
              subscription_id, rg, lbname, fipname
          )

def construct_bap_id(subscription_id, rg, lbname, addr_pool_name):
  """Build the future BackEndId based on components name.
  """
  return ('/subscriptions/{}'
          '/resourceGroups/{}'
          '/providers/Microsoft.Network'
          '/loadBalancers/{}'
          '/backendAddressPools/{}').format(
              subscription_id, rg, lbname, addr_pool_name
          )

def construct_probe_id(subscription_id, rg, lbname, probe_name):
  """Build the future ProbeId based on components name.
  """
  return ('/subscriptions/{}'
          '/resourceGroups/{}'
          '/providers/Microsoft.Network'
          '/loadBalancers/{}'
          '/probes/{}').format(
              subscription_id, rg, lbname, probe_name
          )

if __name__ == "__main__":
    main()
