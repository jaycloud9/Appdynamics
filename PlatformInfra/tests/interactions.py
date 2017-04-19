"""PlatformInfra Tests Module."""

import urllib.parse as urlp
import json
from platforminfra.views import base_path
from platforminfra.config import Config
from jinja2 import Environment


def create(
    app,
    envid,
    application="T24-Pipeline",
    infrastructureTemplateID="test"
):
    """Create an environment."""
    print("Creating environment", envid)
    url = urlp.urljoin(base_path, "environments")
    request_data = json.dumps(
        dict(
            id=envid,
            application=application,
            infrastructureTemplateID=infrastructureTemplateID
        )
    )
    return app.post(
        url,
        data=request_data, content_type='application/json'
    )


def destroy(app, envid):
    """Destroy an environment."""
    print("Destroying environment", envid)
    url = urlp.urljoin(base_path, "environments/" + envid)
    return app.delete(url)


def scale(
    app,
    envid,
    count,
    application="T24-Pipeline",
    servers="t24",
    infrastructureTemplateID="test"
):
    """Sacling an environment."""
    print("Scaling environment", envid)
    url = urlp.urljoin(base_path, "environments/" + envid + "/scale")
    request_data = json.dumps(
        dict(
            application=application,
            count=count,
            infrastructureTemplateID=infrastructureTemplateID,
            servers=servers
        )
    )
    return app.put(
        url,
        data=request_data, content_type='application/json'
    )


def status(app, envid, infrastructureTemplateID="test"):
    """Check status of an environment."""
    print("Status check of environment", envid)
    url = urlp.urljoin(base_path, "environments/" + envid + "/status")
    request_data = json.dumps(
        dict(
            infrastructureTemplateID=infrastructureTemplateID,
        )
    )
    return app.post(
        url,
        data=request_data,
        content_type='application/json'
    )


def getEnvironments(app):
    """Return a response of environments GET request."""
    url = urlp.urljoin(base_path, "environments")
    return app.get(url)


def getResponseData(rv):
    """Return a JSON data from a flask response."""
    d = json.loads(rv.get_data().decode("utf-8"))
    print("Response data:", str(d))
    return d


def getConfigGitlabUrl():
    """Get the Gitlab URL from the config."""
    config = Config()
    config_url = config.credentials["gitlab"]["url"]
    print("Gitlab URL:", config_url)
    return config_url


def getWebsiteUrl(envid):
    """Get the website URL from the Config."""
    config = Config()
    website_url = config.test["website_url"]  # Template. Contains {{id}}
    url = Environment().from_string(website_url).render(id=envid)
    print("Website URL:", url)
    return url
