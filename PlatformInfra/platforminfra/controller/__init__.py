"""PlatformInfra Controller."""

from platforminfra.templates import Template
from platforminfra.helpers import Response
from platforminfra.infrastructure.azure import Azure
from multiprocessing import Process


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
        provider = Azure(template)
        if 'error' in provider.credentials:
            rsp = Response(provider.credentials)
            return rsp.httpResponse(404)
        else:
            # Build core resources
            provider.resourceGroup("mpdevtestrg")
            provider.storageAccount("mpdevtestsa")

            tags = dict()
            for resource in provider.resources['resources']:
                if 'tags' in resource:
                    tags = resource['tags']
                    continue
                if 'networks' in resource:
                    netProcs = list()
                    for idx, network in enumerate(resource['networks']):
                        netId = str(config['id'])+str(idx)
                        p = Process(
                            target=provider.network,
                            args=(network, netId, tags)
                        )
                        netProcs.append(p)
                        p.start()

                    for proc in netProcs:
                        proc.join()

            rsp = Response(provider.resources)
            return rsp.httpResponse(200)
