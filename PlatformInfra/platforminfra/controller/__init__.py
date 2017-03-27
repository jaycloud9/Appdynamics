"""PlatformInfra Controller."""

from platforminfra.templates import Template
from platforminfra.helpers import Response
from platforminfra.infrastructure.azure import Azure
from multiprocessing import Process, Queue, Lock

from ..helpers import Jenkins, Gitlab, Helpers


class Controller(object):
    """Controls the platformInfra."""

    def __init__(self):
        """Initialise the controller."""
        self.templates = Template(templateDir='./templates/')
        self.tags = dict()
        self.response = list()
        self.subnets = list()
        self.vms = list()

    def getTemplate(self, templateName):
        """Get a Template by Name."""
        return self.templates.loadTemplate(templateName)

    def setTags(self, data):
        """Return the tags element."""
        print("Creating Tags")
        self.tags = {**self.tags, **data}

    def createNetworks(self, data, provider):
        """Create Networks."""
        # Must complete before everything else is built
        subNets = Queue()
        print("Creating network")
        netProcs = list()
        for idx, network in enumerate(data):
            netId = str(self.tags['uuid'])+str(idx)
            p = Process(
                target=provider.network,
                args=(network, netId, self.tags, subNets)
            )
            netProcs.append(p)
            p.start()

        subnets = dict()
        for proc in netProcs:
            proc.join()
            subnets['subnets'] = subNets.get()

        self.subnets.append(subnets)

    def createVms(self, data, provider):
        """Create VMs."""
        print("Creating Servers")
        vms = Queue()
        vmLock = Lock()
        # Processes that can be run in parrallel
        serverProcs = list()
        try:
            for server in data:
                for i in self.subnets:
                    if "subnets" in i:
                        p = Process(
                            target=provider.virtualMachine,
                            args=(
                                server,
                                self.tags,
                                i['subnets']['subnet'],
                                vms,
                                vmLock
                            )
                        )
                        vmDetails = {
                            'servers': server['name'],
                            'thread': p
                        }
                        if 'dns' in server:
                            vmDetails['dns'] = server['dns']
                        serverProcs.append(vmDetails)
                        p.start()

            for proc in serverProcs:
                proc['thread'].join()
                tmpData = vms.get()
                if 'dns' in proc:
                    # Only apply to the first server
                    result = provider.addDNS(
                        tmpData['vms'][0]['public_ip'],
                        proc['dns'] + '-' + self.tags['uuid']
                    )
                    tmpData['dns'] = result
                self.vms.append(tmpData)
        except Exception as e:
            raise Exception(e)

    def createLoadBalancers(self, data, provider):
        """Create Load balancers."""
        print("Creating Load Balancers")
        for item in data:
            for lbName, details in item.items():
                if details['load_balancer']['health_protocol'] == 'Tcp' or \
                        details['load_balancer']['health_protocol'] == 'Http':
                    if details['load_balancer']['health_protocol'] == 'Http':
                        if 'health_path' not in details['load_balancer']:
                            e = {
                                'error': "Must specify health_path with Http"
                            }
                            raise Exception(e)

                    # Create LB here
                    print("Creating LB: {}".format(lbName))
                    lbData = provider.loadBalancer(
                        details['load_balancer'],
                        self.tags
                    )
                    # Create Vm's Here
                    details['servers']['beId'] = lbData['lbInfo'] \
                        .backend_address_pools[0].id
                    serverList = list()
                    serverList.append(details['servers'])
                    self.createVms(
                        serverList,
                        provider
                    )
                    record = self.tags['uuid']
                    if 'domain' in details['load_balancer']:
                        record = details['load_balancer']['domain'] + '-' + \
                            record
                    else:
                        record = details['load_balancer']['name'] + '-' + \
                            record

                    result = provider.addDNS(
                        lbData['publicIp'].ip_address,
                        record
                    )
                    self.response.append({
                        details['load_balancer']['name']: result
                    })
                else:
                    e = {
                        'error': "back_end_protocol must be 'Http' or 'Tcp'"
                    }
                    raise Exception(e)

    def createEnvironment(self, config):
        """Create an Environment."""
        template = self.templates.loadTemplate(
            config['infrastructureTemplateID']
        )
        self.tags['uuid'] = config['id']
        provider = Azure(template, config['id'])
        if 'error' in provider.credentials:
            rsp = Response(provider.credentials)
            return rsp.httpResponse(404)

        buildMap = {
            "servers": self.createVms,
            "networks": self.createNetworks,
            "load_balancers": self.createLoadBalancers,
            "tags": self.setTags
        }
        # Build core resources
        print("Creating RG")
        provider.resourceGroup("mpdevtestrg" + self.tags['uuid'])
        print("Creating SA")
        provider.storageAccount("mpdevtestsa" + self.tags['uuid'])
        try:
            for resource in provider.resources['resources']:
                for k, v in resource.items():
                    if k in buildMap:
                        if k == 'tags':
                            buildMap[k](v)
                        else:
                            buildMap[k](v, provider)
                        continue
        except Exception as e:
            print("Something failed :'(")
            rsp = Response(e)
            return rsp.httpResponse(404)

        for vmRsp in self.vms:
            self.response.append(vmRsp)

        # By this point an environment should be created so Execute Jenkins job
        jenkinsServerConn = "http://51.141.7.30:8080"
        jenkinsServer = Jenkins(
            jenkinsServerConn,
            user='admin',
            password='Blue1Sky'
        )
        print("Running Jenkins Job")
        jenkinsServer.runBuildWithParams(
            "T24-Pipeline",
            params={
                "UUID": self.tags['uuid']
            }
        )
        print("Connecting to Gitlab")
        glServerConn = "https://gitlab.temenos.cloud"
        glServerToken = "FHcv_bHjHnAvd6uug7x_"
        glSourceProject = "customer-demo"
        glSourceTeam = "root"
        glServer = Gitlab(glServerConn, glServerToken)
        glSourceProject = glServer.getProject(glSourceTeam, glSourceProject)

        print("Create user")
        user = glServer.createUser(
            self.tags['uuid'],
            self.tags['uuid'],
            Helpers.randStr(10),
            self.tags['uuid'] + '@example.net'
        )
        forked = glServer.forkProject(
            user.username,
            glSourceProject.id
        )
        self.response.append({'git_url': forked.web_url})
        rsp = Response({'Servers': self.response})
        return rsp.httpResponse(200)
