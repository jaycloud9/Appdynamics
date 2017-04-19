"""PlatformInfra Tests Module."""

import unittest
from platforminfra.views import base_path
import urllib.parse as urlp
import time
from tests.interactions import Interactions
import threading
import requests
from platforminfra.config import Config

TEST_ENVIDS = None
CONCURRENT_DEPLOYMENTS = None
API_HOST = None
API_PORT = None
SERVER_URL = None


class PlatformInfraThreadsTestCase(unittest.TestCase):
    """Platfrom Infra Threads Test Cases.

    A class whose instances are single test cases to test the PlatformInfra
    flask application threads.
    """

    def setUp(self):
        """Setup unittest."""
        config = Config()
        global TEST_ENVIDS
        global SERVER_URL
        global CONCURRENT_DEPLOYMENTS
        TEST_ENVIDS = config.test["environment_ids"]
        CONCURRENT_DEPLOYMENTS = config.test["concurrent_deployments"]
        self.interactions = Interactions()

    def tearDown(self):
        """Tear Down Flask App."""
        # Destroy environments, using the flask test client
        for envid in TEST_ENVIDS:
            self.interactions.destroy(envid)

        """Stop flask if it is running"""
        self.interactions.close()

    def destroyEnvironment(
        self,
        envid,
    ):
        """Destroy an environment."""
        print("Destroying environment", envid)
        url = urlp.urljoin(SERVER_URL + base_path, "environments/"+envid)
        print("Requesting", url)
        r = requests.delete(url)
        print("Status code:", r.status_code)

    def creationWorker(
        self,
        envid,
        application="T24-Pipeline",
        infrastructureTemplateID="test"
    ):
        """Create an environment.

        Does not raise exeptions, but appends them to
        self.execption. Suitable as a thread worker.

        Checks:
          - Response of environment creation is "Success"
          - Website URL returns 200 response code

        """
        try:
            print("Creating environment", envid)
            r = self.interactions.create(
                envid,
                application,
                infrastructureTemplateID
            )
            print("Status code:", r.status_code)
            print("Response:", r.text)

            self.assertEqual(
                "Success",
                r.json()["response"],
                "Check for creation success of environmnet ID " + envid
            )

            # Website URL is up and running
            r = requests.get(self.interactions.getWebsiteUrl(envid))
            self.assertEqual(r.status_code, 200)

        except Exception as ex:
            print("Caught an exception from worker thread:", ex)
            self.exceptions.append(ex)

    def test_parallel_creation(self):
        """Test creation of several environments in parallel.

        Using the creationWorker function for concurrent threads.
        """
        request_threads = []

        # Worker threads might raise an exception. Check this afterwards
        self.exceptions = []

        # Start threads
        for i in range(CONCURRENT_DEPLOYMENTS):
            t = threading.Thread(
                target=self.creationWorker,
                args=(TEST_ENVIDS[i],)
            )
            request_threads.append(t)
            t.start()

        # Wait until all of the threads are complete
        all_done = False
        while not all_done:
            all_done = True
            for t in request_threads:
                if t.is_alive():
                    all_done = False
                    time.sleep(1)

        # Check to see if we caught any exceptions
        if len(self.exceptions) > 0:
            print("Number of exceptions:", len(self.exceptions))
            # May be several exceptions, but we'll just raise the first one
            raise self.exceptions[0]


if __name__ == '__main__':
    unittest.main()
