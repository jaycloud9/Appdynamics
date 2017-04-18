"""Module for Loading the configuration of PlatformInfra."""

import os.path
import yaml


class Config(object):
    """Class for managing the PlatformInfra Config."""

    def __init__(self, config="config.yml"):
        """Create a Config object."""
        if os.path.exists(config):
            self.configFile = config
            self.loadConfig()

    def loadConfig(self):
        """Load a Template from a file."""
        fp = self.configFile
        if os.path.isfile(fp):
            stream = open(fp, 'r')
            self.properties = yaml.load(stream)
            if 'credentials' in self.properties:
                self.credentials = self.properties['credentials']
            if 'defaults' in self.properties:
                self.defaults = self.properties['defaults']
            if 'test' in self.properties:
                self.test = self.properties['test']
            else:
                raise Exception("No Credentials provided")
        else:
            raise IOError
