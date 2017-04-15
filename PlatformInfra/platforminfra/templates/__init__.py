"""Template management for PlatformInfra."""

import os.path
import yaml


class Template(object):
    """Class for handeling Templates."""

    def __init__(self, templateDir='./'):
        """Constructor for Template class."""
        if os.path.exists(templateDir):
            self.templateDir = templateDir
        else:
            raise Exception({
                'error': "Can not find Template DIR {}".format(templateDir),
                'code': 500
            })

    def loadTemplate(self, templateName):
        """Load a Template from a file."""
        fp = self.templateDir + templateName + '.yml'
        if os.path.isfile(fp):
            stream = open(fp, 'r')
            return yaml.load(stream)
        else:
            raise Exception({
                'error': "Can not find Template file {}".format(templateName),
                'code': 404
            })
