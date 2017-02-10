from azure.common.credentials import ServicePrincipalCredentials
from azure.mgmt.resource import ResourceManagementClient
from azure.mgmt.storage import StorageManagementClient
from azure.mgmt.network import NetworkManagementClient
from azure.mgmt.compute import ComputeManagementClient
from azure.mgmt.dns import DnsManagementClient

import yaml
import sys
import time

######################################################
#
#     Helper methods
#
######################################################

def timeit(method):
  def timed(*args, **kw):
    ts = time.time()
    result = method(*args, **kw)
    te = time.time()

    print '%r (%r, %r) %2.2f sec' % \
      (method.__name__, args, kw, te-ts)
    return result

  return timed


def get_env(service):
  for srvc in config['services']:
    if srvc['name'] == service:
      srvc['server_size'] = config['provider'][0]['azure'][0]['config'][1]['server_size']
      return srvc


######################################################
#
#     Main Code
#
######################################################


def main():
  #print('\nList VMs in subscription')
  #for vm in compute_client.virtual_machines.list_all():
  #  print("\tVM: {}".format(vm.name))

  #NICE
  #TODO: Get all resources for a resource group if it exists and only create new if they don't exist.

  #MUST
  #TODO: delete DNs records for Service

  if len(sys.argv) <= 1:
    print("Specify create or destroy")
    print("i.e. python infra_provision.py create azure cluster1 dev")
    sys.exit(2)
  else:
    if sys.argv[1] == "create":
      if len(sys.argv) <= 4:
        print("Please ensure you have specified a provider and environment i.e.")
        print("python infra_provision.py create azure cluster1 dev")
        sys.exit(2)
      else:
        if sys.argv[2] == "azure":
          service = get_env(sys.argv[3])
          create(sys.argv[2],service, sys.argv[4])
        else:
          print("not implemented yet")
          sys.exit(2)
    elif sys.argv[1] == "destroy":
      if len(sys.argv) <= 3:
        print("Specify a provider and environment to destroy")
        sys.exit(2)
      else:
        if sys.argv[2] == "azure":
          service = get_env(sys.argv[3])
          destroy(sys.argv[2], service, sys.argv[4])
        else:
          print("not implemented yet")
          sys.exit(2)
    else:
      print("Specify create or destroy")
      sys.exit(2)

def destroy(proviver, service, environment):
  print("Destroying %s %s" % (service['name'], environment))
  rg = service['name'] + '-' + environment + '-' + service['stack']
  delete_async_operation = resource_client.resource_groups.delete(rg)
  delete_async_operation.wait()
  print("Deleted Resource group {}".format(rg))


def create(provider, service, environment):
  ######################################################
  #
  #     Prepare Environment
  #
  ######################################################

  print("Preparing Environment %s - %s" % (service['name'], environment))
  print('Create Resource Group')
  rg = service['name'] + '-' + environment + '-' + service['stack']
  resource_client.resource_groups.create_or_update(
    rg,
    {
      'location': service['region']
    }
  ).name
  print("Reosource Group %s created" % rg)

  sa = create_storage(rg,service, environment)
	
  be_ids = dict()

  print("Creating Network")
  subnet = create_network(service, rg)

  if 'load_balancers' in service:
    for lb in service['load_balancers']:
      print("Creating Load Balancer: {}".format(lb['name']))
      lb_rules = []
      for rule in lb['rules']:
        lb_rules.append({'name': rule['name'], 'protocol':rule['protocol'], 'frontend_port': str(rule['frontend_port']), 'backend_port': str(rule['backend_port'])})

      if lb['health_protocol'] == 'Tcp' or lb['health_protocol'] == 'Http':
        path = None
        if lb['health_protocol'] == 'Http':
          if 'health_path' not in lb:
            print("Must specify health_path with Http")
            sys.exit(2)
          path = lb['health_path']

        load_balancer = create_load_balancer(rg, service, lb['name'], lb['health_port'], lb['health_protocol'], path, lb_rules)
      else:
        print("back_end_protocol must be EXACTLY 'Http' or 'Tcp'")
        sys.exit(2)

      be_ids[lb['be_servers']] = load_balancer['lb_info'].backend_address_pools[0].id
      public_ip = load_balancer['public_ip'].ip_address
      record = lb['name']
      if 'domain' in lb:
        record = lb['domain']

      result = add_dns('mp_dev_core', public_ip, record)
      print("Created Domain: {}".format(result))

  for server in service['servers']:

    if 'lb' in server:
      vms = create_vm(rg,service, environment, sa, subnet, server['name'], service['server_size'], server['count'], be_ids[server['name']])
      print("VMs {}".format(vms))
      if 'dns' in server:
        for vm in vms:
          print("NB: the DNS option run against multiple machines overrides")
          result = add_dns('mp_dev_core', vm['public_ip'] , server['dns'])
          print("Created Domain: {}".format(result))
    else:
      vms = create_vm(rg,service, environment, sa, subnet, server['name'], service['server_size'], server['count'])
      if 'dns' in server:
        for vm in vms:
          print("NB: the DNS option run against multiple machines overrides")
          result = add_dns('mp_dev_core', vm['public_ip'] , server['dns'])
          print("Created Domain: {}".format(result))


  print("Done")


######################################################
#
#     Functions
#
######################################################
@timeit
def create_storage(rg,service, environment):
  print('Create a storage account')
  sa = service['name'] + environment + 'sa'
  # looking at https://github.com/Azure/azure-sdk-for-python/blob/master/azure-mgmt-storage/azure/mgmt/storage/operations/storage_accounts_operations.py
  # Suggests I can pass in a dict with long_running_operation_timeout to adjust the azure poller timeout
  storage_async_operation = storage_client.storage_accounts.create(
    rg,
    sa,
    {
      'sku': {'name': 'standard_lrs'},
      'kind': 'storage',
      'location': service['region']
#    },
#    {
#      'long_running_operation_timeout': 5
    }
  )
  storage_async_operation.wait()
#  print(storage_async_operation.result())

  return sa


def create_vm(rg, service, environment, sa, subnet, vmtype, vm_size, count, be_id=None):
  """Create a VM and associated coponents
  """

  print('Create availability set')
  availability_set_info = compute_client.availability_sets.create_or_update(
    rg,
    rg + '-' + vmtype + '-as',
    {'location': service['region']}
  )

  vm_details = list()

  i = 1
  while (i <= int(count)):
    vmname = str(vmtype + str(i)).translate(None, '` ~!@#$%^&*()=+_[]{}\|;:\'",<>/?.')
    print("Creating %s of %s: %s VMs" % (i, count, vmtype))
    print("Creating NIC")
    details = create_nic(network_client, rg, service, vmname, subnet, be_id)
    nic = details['nic']
    print("Generating VM Params")
    vm_parameters = create_vm_parameters(nic.id, sa, vmname, service, availability_set_info.id)
    print("Creating VM")
    async_vm_creation = compute_client.virtual_machines.create_or_update(
      rg, vmname, vm_parameters)
    async_vm_creation.wait()
    print('Attach Data Disk')
    async_vm_update = compute_client.virtual_machines.create_or_update(
      rg,
      vmname,
      {
        'location': service['region'],
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
        'location': service['region'],
        'tags': {
          'Environment': environment,
          'Stack': service['stack'],
          'Owner': service['owner'],
          'Type': vmtype
        }
      }
    )
    async_vm_update.wait()

    #Get Public IP for Host and return
    public_ip = network_client.public_ip_addresses.get(rg,details['public_ip_name'])
    vm_details.append({'name': vmname, 'public_ip': public_ip.ip_address})
    

    i = i + 1

  print("VM Details inside create VM {}".format(vm_details))
  return vm_details


def create_network(service, resource_group):
  """Create a Network and subnets.
  """
  # Create VNet
  print('Create Vnet')
  async_vnet_creation = network_client.virtual_networks.create_or_update(
    resource_group,
    resource_group + '-vnet',
    {
      'location': service['region'],
      'address_space': {
        'address_prefixes': [service['cidr']]
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
    {'address_prefix': service['subnet']}
  )
  subnet_info = async_subnet_creation.result()
  return subnet_info

def create_nic(network_client, resource_group, service, vmname, subnet_info, be_id=None):
  """Create a Network Interface for a VM.
  """

  # Create Pub IP
  print("Creating Public IP")
  pub_ip_name=resource_group + '-' + vmname + '-ip'
  async_pubIP_creation = network_client.public_ip_addresses.create_or_update(
    resource_group,
    pub_ip_name,
    {
      'public_ip_allocation_method': 'Dynamic',
      'location': service['region'],
      'public_ip_address_version': 'IPv4'
    }
  )
  async_pubIP_creation.wait()
  pub_ip = async_pubIP_creation.result()

  # Create NIC
  print('Create NIC')
  params = {
      'location': service['region'],
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
  details = dict()
  details['public_ip_name'] = pub_ip_name
  details['nic'] = async_nic_creation.result()
  return details

def create_vm_parameters(nic_id, sa, vmname, service, as_id):
  """Create the VM parameters structure.
  """
  return {
    'location': service['region'],
    'os_profile': {
      'computer_name': vmname,
      'admin_username': config['global']['user'],
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
      'vm_size': service['server_size']
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
    'location': service['region'],
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
      'location': service['region'],
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

  return rs + "." + domain

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

def get_config(cfg_file):
  stream = file(cfg_file, 'r')
  config_yaml = yaml.load(stream)
  return config_yaml


#Initialise Config:
config = get_config('config.yml')

subscription_id = config['provider'][0]['azure'][0]['config'][0]['credentials']['subscription_id']
credentials = ServicePrincipalCredentials(
    client_id = config['provider'][0]['azure'][0]['config'][0]['credentials']['client_id'],
    secret = config['provider'][0]['azure'][0]['config'][0]['credentials']['secret'],
    tenant = config['provider'][0]['azure'][0]['config'][0]['credentials']['tenant']
)

resource_client = ResourceManagementClient(credentials, subscription_id)
compute_client = ComputeManagementClient(credentials, subscription_id)
storage_client = StorageManagementClient(credentials, subscription_id)
network_client = NetworkManagementClient(credentials, subscription_id)
dns_client = DnsManagementClient(credentials, subscription_id)


if __name__ == "__main__":
    main()
