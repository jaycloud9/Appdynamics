"""PlatformInfra Tests Module."""

import platforminfra
import unittest
from platforminfra.views import base_path
import urllib.parse as urlp
import json
import time
import tests.interactions as interactions
import threading
from multiprocessing import Process
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
        config = Config()
        global TEST_ENVIDS
        global SERVER_URL
        global CONCURRENT_DEPLOYMENTS
        global API_HOST
        global API_PORT
        TEST_ENVIDS = config.test["environment_ids"]
        CONCURRENT_DEPLOYMENTS = config.test["concurrent_deployments"]
        API_HOST = config.test["api_host"]
        API_PORT = config.test["api_port"]
        SERVER_URL = "http://" + API_HOST + ":" + str(API_PORT)

        """Set Up Flask."""
        self.server_process = Process(target=self.start_and_init_server)
        self.server_process.start()
        time.sleep(1)

    def tearDown(self):
        """Tear Down Flask App."""
        try:
            self.server_process.terminate()
        except Exception as ex:
            print(ex)

        # Destroy environments, using the flask test client
        app = platforminfra.app.test_client()
        for envid in TEST_ENVIDS:
            interactions.destroy(app, envid)

    def start_and_init_server(self):
        """A helper function to start out server in a thread."""
        platforminfra.app.run(threaded=True, host=API_HOST, port=API_PORT)

    def destroyEnvironment(
        self,
        envid,
    ):
        """Destroys an environment"""
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
        """Create an environment. Does not raise exeptions, but appends them to
        self.execption. Suitable as a thread worker.

        Checks:
          - Response of environment creation is "Success"
          - Website URL returns 200 response code

        """

        try:
            print("Creating environment", envid)
            url = urlp.urljoin(SERVER_URL + base_path, "environments")
            request_data = json.dumps(
                dict(
                    id=envid,
                    application=application,
                    infrastructureTemplateID=infrastructureTemplateID
                )
            )
            print("Requesting", url)
            r = requests.post(
                url,
                data=request_data,
                headers={'content-type': 'application/json'}
            )
            print("Status code:", r.status_code)
            print("Response:", r.text)

            self.assertEqual(
                "Success",
                r.json()["response"],
                "Check for creation success of environmnet ID " + envid
            )

            # Website URL is up and running
            r = requests.get(interactions.getWebsiteUrl(envid))
            self.assertEqual(r.status_code, 200)

        except Exception as ex:
            print("Caught an exception from worker thread:", ex)
            self.exceptions.append(ex)

    def test_parallel_creation(self):
        """ Test creation of several environments in parallel, using
        creationWorker function for concurrent threads.
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
            raise self.exception[0]

if __name__ == '__main__':
    unittest.main()
