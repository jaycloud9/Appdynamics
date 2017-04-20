"""PlatformInfra Tests Module."""

import platforminfra
import urllib.parse as urlp
import json
from platforminfra.views import base_path
from platforminfra.config import Config
from jinja2 import Environment
import requests
from multiprocessing import Process
import time


class Interactions():
    """Interactions Class."""

    def __init__(self):
        """Constructor for Interactions."""
        self.config = Config()
        self.api_host = self.config.test["api_host"]
        self.api_port = self.config.test["api_port"]
        self.server_url = "http://" + self.api_host + ":" + str(self.api_port)
        self.base_url = self.server_url + base_path
        if self.config.test["run_api"]:

            """Set Up Flask."""
            platforminfra.app.config['TESTING'] = (
                self.config.test["flask_testing"]
            )
            platforminfra.app.config['DEBUG'] = self.config.test["flask_debug"]

            """Run Flask."""
            self.server_process = Process(target=self.start_and_init_server)
            self.server_process.start()
            time.sleep(1)

    def close(self):
        """To be called as part of the tear down of tests."""
        if self.config.test["run_api"] and self.server_process.is_alive():
            self.server_process.terminate()

    def start_and_init_server(self):
        """A helper function to start out server in a thread."""
        platforminfra.app.run(
            threaded=True,
            host=self.api_host,
            port=self.api_port
        )

    def create(
        self,
        envid,
        application="testBuild",
        infrastructureTemplateID="test"
    ):
        """Create an environment."""
        url = urlp.urljoin(self.base_url, "environments")
        request_data = json.dumps(
            dict(
                id=envid,
                application=application,
                infrastructureTemplateID=infrastructureTemplateID
            )
        )
        print("Requesting", url)
        return requests.post(
            url,
            data=request_data,
            headers={'content-type': 'application/json'}
        )

    def destroy(self, envid):
        """Destroy an environment."""
        print("Destroying environment", envid)
        url = urlp.urljoin(self.base_url, "environments/" + envid)
        print("Requesting", url)
        return requests.delete(url)

    def scale(
        self,
        envid,
        count,
        application="T24-Pipeline",
        servers="t24",
        infrastructureTemplateID="test"
    ):
        """Sacling an environment."""
        print("Scaling environment", envid)
        url = urlp.urljoin(self.base_url, "environments/" + envid + "/scale")
        request_data = json.dumps(
            dict(
                application=application,
                count=count,
                infrastructureTemplateID=infrastructureTemplateID,
                servers=servers
            )
        )
        return requests.put(
            url,
            data=request_data,
            headers={'content-type': 'application/json'}
        )

    def status(self, envid, infrastructureTemplateID="test"):
        """Check status of an environment."""
        print("Status check of environment", envid)
        url = urlp.urljoin(self.base_url, "environments/" + envid + "/status")
        request_data = json.dumps(
            dict(
                infrastructureTemplateID=infrastructureTemplateID,
            )
        )
        return requests.post(
            url,
            data=request_data,
            headers={'content-type': 'application/json'}
        )

    def getEnvironments(self):
        """Return a response of environments GET request."""
        url = urlp.urljoin(self.base_url, "environments")
        return requests.get(url)

    def getResponseData(self, rv):
        """Return a JSON data from a flask response."""
        d = rv.json()
        print("Response data:", str(d))
        return d

    def getConfigGitlabUrl(self):
        """Get the Gitlab URL from the config."""
        config_url = self.config.credentials["gitlab"]["url"]
        print("Gitlab URL:", config_url)
        return config_url

    def getWebsiteUrl(self, envid):
        """Get the website URL from the Config.

        Where config value may contain {{id}} for the envid value.
        """
        website_url = self.config.test["website_url"]
        url = Environment().from_string(website_url).render(id=envid)
        print("Website URL:", url)
        return url
