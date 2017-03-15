"""PlatformInfra Controller."""

from platforminfra.templates import Template
from platforminfra.helpers import Response
from platforminfra.infrastructure.azure import Azure


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
            rsp = Response(provider.resources)
            return rsp.httpResponse(200)
