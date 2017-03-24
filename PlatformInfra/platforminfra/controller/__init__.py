"""PlatformInfra Controller."""

from platforminfra.templates import Template
from platforminfra.helpers import Response
from platforminfra.infrastructure.azure import Azure
from multiprocessing import Process, Queue


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
            netId = str(self.tags['id'])+str(idx)
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
        print(data)
        vms = Queue()
        # Processes that can be run in parrallel
        serverProcs = list()
        try:
            for server in data:
                print("Threading {}".format(server))
                for i in self.subnets:
                    if "subnets" in i:
                        p = Process(
                            target=provider.virtualMachine,
                            args=(
                                server,
                                self.tags,
                                i['subnets']['subnet'],
                                vms
                            )
                        )
                        print("Threading servers {}".format(server['name']))
                        serverProcs.append({
                            'servers': server['name'],
                            'thread': p
                        })
                        print("Started thread process")
                        p.start()

            for proc in serverProcs:
                proc['thread'].join()
                self.vms.append(vms.get())
        except Exception as e:
            raise Exception(e)

    def createEnvironment(self, config):
        """Create an Environment."""
        template = self.templates.loadTemplate(
            config['infrastructureTemplateID']
        )
        self.tags['id'] = config['id']
        provider = Azure(template, config['id'])
        if 'error' in provider.credentials:
            rsp = Response(provider.credentials)
            return rsp.httpResponse(404)

        buildMap = {
            "servers": self.createVms,
            "networks": self.createNetworks,
            "tags": self.setTags
        }
        # Build core resources
        print("Creating RG")
        provider.resourceGroup("mpdevtestrg" + self.tags['id'])
        print("Creating SA")
        provider.storageAccount("mpdevtestsa" + self.tags['id'])
        # lbProcs = list()
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
            rsp = Response(e)
            return rsp.httpResponse(404)

        for vmRsp in self.vms:
            print(vmRsp)
            self.response.append(vmRsp)

        rsp = Response({'Servers': self.response})
        return rsp.httpResponse(200)
