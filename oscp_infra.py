from azure.common.credentials import ServicePrincipalCredentials
from azure.mgmt.resource import ResourceManagementClient
from azure.mgmt.storage import StorageManagementClient
from azure.mgmt.network import NetworkManagementClient
from azure.mgmt.compute import ComputeManagementClient
from azure.mgmt.dns import DnsManagementClient

import configparser
import sys

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
dns_client = DnsManagementClient(credentials, subscription_id)

#print('\nList VMs in subscription')
#for vm in compute_client.virtual_machines.list_all():
#  print("\tVM: {}".format(vm.name))

#NICE
#TODO: Get all resources for a resource group if it exists and only create new if they don't exist.

#MUST
#TODO: delete DNs records for Service

def main():
  if len(sys.argv) <= 1:
    print("Specify create or destroy")
    sys.exit(2)
  else:
    if sys.argv[1] == "create":
      create()
    elif sys.argv[1] == "destroy":
      if len(sys.argv) <= 2:
        print("Specify a service to destroy")
        sys.exit(2)
      else:
        destroy(sys.argv[2])

    else:
      print("Specify create or destroy")
      sys.exit(2)

def destroy(service):
  print("Destroying %s" % service)
  rg = service + '-' + config.get(service,'name') + '-' + config.get(service,'stack')
  delete_async_operation = resource_client.resource_groups.delete(rg)
  delete_async_operation.wait()
  print("Deleted Resource group {}".format(rg))


def create():
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
      sa = service + 'sa'
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

      print("Creating Network")
      subnet = create_network(service, rg)

      print("Creating Load Balancers")
      console_rules = []
      console_rules.append({'name': 'ssl', 'protocol':'Tcp', 'frontend_port': '443', 'backend_port': '443'})

      console_lb = create_load_balancer(rg, service, 'console', 443, 'Tcp', None, console_rules)
      console_be_id = console_lb['lb_info'].backend_address_pools[0].id
      console_ip = console_lb['public_ip'].ip_address
      add_dns('mp_dev_core', console_ip, service)


      apps_rules = []
      apps_rules.append({'name': 'router-ssl', 'protocol':'Tcp', 'frontend_port': '443', 'backend_port': '443'})
      apps_rules.append({'name': 'router-http', 'protocol':'Tcp', 'frontend_port': '80', 'backend_port': '80'})

      apps_lb = create_load_balancer(rg, service, 'apps', 443, 'Tcp', None, apps_rules)
      apps_be_id = apps_lb['lb_info'].backend_address_pools[0].id
      apps_ip = apps_lb['public_ip'].ip_address
      add_dns('mp_dev_core', apps_ip, '*.apps.cluster1')


      gitlab_rules = []
      gitlab_rules.append({'name': 'web', 'protocol':'Tcp', 'frontend_port': '80', 'backend_port': '8081'})

      gitlab_lb = create_load_balancer(rg, service, 'gitlab', 8081, 'Http', '/users/sign_in', gitlab_rules)
      gitlab_be_id = gitlab_lb['lb_info'].backend_address_pools[0].id
      gitlab_ip = gitlab_lb['public_ip'].ip_address
      add_dns('mp_dev_core', gitlab_ip, 'gitlab')

      size='Standard_D1_v2'

      create_vm(rg,service, sa, subnet, 'gitlab', size, config.get(service,'gitlab_count'), gitlab_be_id)
      create_vm(rg,service, sa, subnet, 'formation', size, config.get(service,'formation_count'))
      create_vm(rg,service, sa, subnet, 'storage', size, config.get(service,'storage_count'))
      create_vm(rg,service, sa, subnet, 'master', size, config.get(service,'master_count'), console_be_id)
      create_vm(rg,service, sa, subnet, 'node_worker', size, config.get(service,'node_worker_count'), )
      create_vm(rg,service, sa, subnet, 'node_infra', size, config.get(service,'node_infra_count'), apps_be_id)


      print("Done")


######################################################
#
#     Functions
#
######################################################

def create_vm(rg, service, sa, subnet, vmtype, vm_size, count, be_id=None):
  """Create a VM and associated coponents
  """

  print('Create availability set')
  availability_set_info = compute_client.availability_sets.create_or_update(
    rg,
    rg + '-' + vmtype + '-as',
    {'location': config.get(service,'region')}
  )

  i = 1
  while (i <= int(count)):
    vmname = str(vmtype + str(i)).translate(None, '` ~!@#$%^&*()=+_[]{}\|;:\'",<>/?.')
    print("Creating %s of %s: %s VMs" % (i, count, vmtype))
    print("Creating NIC")
    nic = create_nic(network_client, rg, service, vmname, subnet, be_id)

    vm_parameters = create_vm_parameters(nic.id, sa, vmname, vm_size, service, availability_set_info.id)
    async_vm_creation = compute_client.virtual_machines.create_or_update(
      rg, vmname, vm_parameters)
    async_vm_creation.wait()
    
    print('Attach Data Disk')
    async_vm_update = compute_client.virtual_machines.create_or_update(
      rg,
      vmname,
      {
        'location': config.get(service,'region'),
        'storage_profile': {
          'data_disks': [{
            'name': vmname + 'datadisk1.vhd',
            'disk_size_gb': 200,
            'lun': 0,
            'vhd': {
              'uri' : "https://{}.blob.core.windows.net/vhds/{}".format(
                  sa, vmname + 'datadisk1.vhd')
            },
            'create_option': 'Empty'
          }]
        }
      }
    )
    async_vm_update.wait()
    
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
    resource_group + '-' + vmname + '-nic',
    params
  )
  return async_nic_creation.result()

def create_vm_parameters(nic_id, sa,  vmname, vmsize, service, as_id):
  """Create the VM parameters structure.
  """
  return {
    'location': config.get(service,'region'),
    'os_profile': {
      'computer_name': vmname,
      'admin_username': config.get(service,'user'),
      'linux_configuration': {
        'ssh': {
          'public_keys': [{
            'path': '/home/mpadmin/.ssh/authorized_keys',
            'key_data': "ssh-rsa AAAAB3NzaC1yc2EAAAADAQABAAABAQDYgAsBhjeEM2KTkUTwQjFer2uRyBQ6qWdkC46eJt40c2YEmEer32vylVNGvaMo9/OiObxXi0PjkzEdP8vonyJiP01Xq1yZguKPRoOhrUtXWzW45NLjZqyjiJMp8MaweIs5TA19oAQL6knWCzVQjN8tiaDlqhSmkLK1l2G3gW8iVGrWt4cUz2SJJkEKp3gN3zjGlohP5J6F6qiS+ES+TXtbW7g97rfWuMxN1m+2go96GBsR+zrsAk0Wp2U/JBCghUi2vYNEZk9dmpX/C5JVzLiIOOi44mIkgxeZvzkPeo4Qo4A76ZJeC0RZwhKGWnip6UwqReDOMDYcMxba5OF2WUGR"
          }]
        }
      }
    },
    'hardware_profile': {
      'vm_size': vmsize
    },
    'storage_profile': {
      'image_reference': {
        'publisher': 'RedHat',
        'offer': 'RHEL',
        'sku': '7.2',
        'version': 'latest'
      },
      'os_disk': {
        'name': vmname + 'disk',
        'caching': 'None',
        'create_option': 'fromImage',
        'vhd': {
          'uri': 'https://{}.blob.core.windows.net/vhds/{}.vhd'.format(
            sa , vmname)
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

def create_load_balancer(rg, service, purpose, hp_port, hp_proto, hp_path, lb_rules):
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
    'name': lbname + hp_proto + '-probe',
    'protocol': hp_proto,
    'port': hp_port,
    'interval_in_seconds': 15,
    'number_of_probes': 4,
  }]
  if hp_proto == 'Http':
    probes[0]['request_path'] = hp_path

  # Building a LoadBalancer rule
  print('Create LoadBalancerRule configuration')
  load_balancing_rules = []
  for rule in lb_rules:
    load_balancing_rules.append({
      'name': lbname + rule['name'] +'-rule',
      'protocol': rule['protocol'],
      'frontend_port': rule['frontend_port'],
      'backend_port': rule['backend_port'],
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
        'id': construct_probe_id(subscription_id, rg, lbname, lbname + hp_proto + '-probe')
      }
    })

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
  lb_data = dict()
  lb_data['lb_info'] = lb_info
  lb_data['public_ip'] = public_ip_info
  
  return lb_data


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

def add_dns(resource_group, ip, rs, domain='dev.temenos.cloud'):
  record_set = dns_client.record_sets.create_or_update(
    resource_group,
    domain,
    rs,
    'A',
      {
        "ttl": 300,
        "arecords": [
          {
            "ipv4_address": ip 
          }
       ]
      }
    )

def print_item(group):
  """Print an Azure object instance."""
  print("\tName: {}".format(group.name))
  print("\tId: {}".format(group.id))
  print("\tLocation: {}".format(group.location))
  print("\tTags: {}".format(group.tags))
  if hasattr(group, 'properties'):
    print_properties(group.properties)

def print_properties(props):
  """Print a ResourceGroup properties instance."""
  if props and props.provisioning_state:
    print("\tProperties:")
    print("\t\tProvisioning State: {}".format(props.provisioning_state))
    print("\n\n")


if __name__ == "__main__":
    main()
