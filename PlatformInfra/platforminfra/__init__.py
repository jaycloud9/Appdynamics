"""Main entry point for the PlatformInfra application."""
from flask import Flask
app = Flask(__name__)

import platforminfra.views
"""Needed so the app knows what views are available."""
