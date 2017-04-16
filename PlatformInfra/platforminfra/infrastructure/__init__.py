"""Infrastructire wrapping Module.

Currently this is unused but it is intended as the location where deciding
which provider to use and how to create the VMs (for example) should be done.
This and the structure of the providers will need revisiting so this was left
out until a better understanding was achieved.
"""


class Infrastructure(object):
    """Infrastructure Class for generic infrastructure operations."""

    def __init__(self, provider):
        """Init the class."""
        self.provider = provider

    def getProvider(self):
        """Get the provider."""
        return self.provider
