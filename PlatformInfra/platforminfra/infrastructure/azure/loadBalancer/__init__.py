"""Module for managing Load Balancers."""

from azure.mgmt.network import NetworkManagementClient


class LoadBalancer(object):
    """Class for managing LB."""

    def __init__(self, opts, lb, rules, tags):
        """Init LB Class with Azure parent."""
        self.vmParams = dict()
        self.config = opts['config']
        self.storageAccount = opts['sa']
        self.resourceGroup = opts['rg']
        self.authAccount = opts['authAccount']
        self.credentials = opts['credentials']
        self.lb = lb
        self.rules = rules
        self.tags = tags

    def createPublicIp(self, lbName):
        """Create a public IP address."""
        netClient = NetworkManagementClient(
            self.authAccount, self.credentials['subscription_id']
        )
        print('Create Public IP')
        publicIpParameters = {
          'location': self.config['region'],
          'public_ip_allocation_method': 'static',
          'idle_timeout_in_minutes': 4
        }
        asyncPublicIpCreation = netClient.public_ip_addresses.create_or_update(
          self.resourceGroup,
          lbName + 'pip',
          publicIpParameters
        )
        publicIpInfo = asyncPublicIpCreation.result()
        return publicIpInfo

    def generateFrontEndConfiguration(self, lbName, pubIpInfo):
        """Generate the Front End config."""
        print('Create FrontEndIpPool configuration')
        frontendIpConfigurations = [{
          'name': lbName + '-fip',
          'private_ip_allocation_method': 'Dynamic',
          'public_ip_address': {
            'id': pubIpInfo.id
          }
        }]
        return frontendIpConfigurations

    def generateBackEndConfiguration(self, lbName):
        """Generate Back End Config."""
        print('Create BackEndAddressPool configuration')
        backEndAddressPools = [{
            'name': lbName + '-bepool'
        }]
        return backEndAddressPools

    def generateHealthProbeConfiguration(self, lbName):
        """Generate Health probe Config."""
        print('Create HealthProbe configuration')
        probes = [{
          'name': lbName + self.lb['hp_proto'] + '-probe',
          'protocol': self.lb['hp_proto'],
          'port': self.lb['hp_proto'],
          'interval_in_seconds': 15,
          'number_of_probes': 4,
        }]
        if self.lb['hp_proto'] == 'Http':
            probes[0]['request_path'] = self.lb['hp_path']

        return probes

    def generateFipId(self, lbName):
        """Build the future FrontEndId based on components name."""
        return ('/subscriptions/{}'
                '/resourceGroups/{}'
                '/providers/Microsoft.Network'
                '/loadBalancers/{}'
                '/frontendIPConfigurations/{}').format(
                    self.credentials['subscription_id'],
                    self.resourceGroup,
                    lbName,
                    lbName + 'fip'
                )

    def generateBapId(self, lbName):
        """Build the future BackEndId based on components name."""
        return ('/subscriptions/{}'
                '/resourceGroups/{}'
                '/providers/Microsoft.Network'
                '/loadBalancers/{}'
                '/backendAddressPools/{}').format(
                    self.credentials['subscription_id'],
                    self.resourceGroup,
                    lbName,
                    lbName + '-bepool'
                )

    def generateProbeId(self, lbName):
        """Build the future ProbeId based on components name."""
        return ('/subscriptions/{}'
                '/resourceGroups/{}'
                '/providers/Microsoft.Network'
                '/loadBalancers/{}'
                '/probes/{}').format(
                    self.credentials['subscription_id'],
                    self.resourceGroup,
                    lbName,
                    lbName + self.lb['hp_proto'] + '-probe'
                )

    def generateLbrules(self, lbName):
        """Generate LB Rules."""
        print('Create LoadBalancerRule configuration')
        loadBalancingRules = []
        for rule in self.rules:
            loadBalancingRules.append({
                'name': lbName + rule['name'] + '-rule',
                'protocol': rule['protocol'],
                'frontend_port': rule['frontend_port'],
                'backend_port': rule['backend_port'],
                'idle_timeout_in_minutes': 4,
                'enable_floating_ip': False,
                'load_distribution': 'Default',
                'frontend_ip_configuration': {
                    'id': self.generateFipId(lbName)
                },
                'backend_address_pool': {
                  'id': self.generateBapId(lbName)
                },
                'probe': {
                  'id': self.generateProbeId(lbName)
                }
            })

    def create(self):
        """Create a Load Balancer."""
        netClient = NetworkManagementClient(
            self.authAccount, self.credentials['subscription_id']
        )
        lbName = self.config['id'] + '-lb'
        # Create PublicIP
        pubIp = self.createPublicIp(lbName)
        # Building a FrontEndIpPool
        feConfig = self.generateFrontEndConfiguration(lbName, pubIp)
        # Building a BackEnd address pool
        beConfig = self.generateBackEndConfiguration(lbName)
        # Building a HealthProbe
        probe = self.generateHealthProbeConfiguration(lbName)
        # Building a LoadBalancer rule
        rules = self.generateLbrules(lbName)
        # Creating Load Balancer
        print('Creating Load Balancer')
        lbAsyncCreation = netClient.load_balancers.create_or_update(
            self.resourceGroup,
            lbName,
            {
              'location': self.config['region'],
              'frontend_ip_configurations': feConfig,
              'backend_address_pools': beConfig,
              'probes': probe,
              'load_balancing_rules': rules
            }
        )
        lbInfo = lbAsyncCreation.result()

        return {
            'name': lbName,
            'lbInfo': lbInfo,
            'publicIp': pubIp
        }
