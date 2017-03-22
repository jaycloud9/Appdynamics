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

    def getTemplate(self, templateName):
        """Get a Template by Name."""
        return self.templates.loadTemplate(templateName)

    def createEnvironment(self, config):
        """Create an Environment."""
        template = self.templates.loadTemplate(
            config['infrastructureTemplateID']
        )
        provider = Azure(template, config['id'])
        if 'error' in provider.credentials:
            rsp = Response(provider.credentials)
            return rsp.httpResponse(404)
        else:
            # Build core resources
            print("Creating RG")
            provider.resourceGroup("mpdevtestrg")
            print("Creating SA")
            provider.storageAccount("mpdevtestsa")

            tags = dict()
            tags['id'] = config['id']
            subNets = Queue()
            vms = Queue()
            response = list()
            # Processes that can be run in parrallel
            serverProcs = list()
            # lbProcs = list()
            for resource in provider.resources['resources']:
                if 'tags' in resource:
                    print("Creating Tags")
                    tags = resource['tags']
                    continue
                if 'networks' in resource:
                    # Must complete before everything else is built
                    print("Creating network")
                    netProcs = list()
                    for idx, network in enumerate(resource['networks']):
                        netId = str(config['id'])+str(idx)
                        p = Process(
                            target=provider.network,
                            args=(network, netId, tags, subNets)
                        )
                        netProcs.append(p)
                        p.start()

                    for proc in netProcs:
                        proc.join()
                    continue
                if 'servers' in resource:
                    print("Creating Servers")
                    for server in resource['servers']:
                        p = Process(
                            target=provider.virtualMachine,
                            args=(server, tags, subNets.get(), vms)
                        )
                        serverProcs.append(p)
                        p.start()
                    for proc in serverProcs:
                        response.append(vms.get())
                        proc.join()
            for vmRsp in response:
                print(vmRsp)
                if 'error' in vmRsp:
                    rsp = Response(vmRsp)
                    return rsp.httpResponse(404)

            rsp = Response({'Servers': response})
            return rsp.httpResponse(200)
