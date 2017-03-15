"""Infrastructire wrapping Module."""


class Infrastructure(object):
    """Infrastructure Class for generic infrastructure operations."""

    def __init__(self, provider):
        """Init the class."""
        self.provider = provider

    def getProvider(self):
        """Get the provider."""
        return self.provider
