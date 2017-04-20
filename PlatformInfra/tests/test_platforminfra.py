"""PlatformInfra Tests Module."""

import unittest
import urllib.parse as urlp
import requests
import dns.resolver
import re
import time
from tests.interactions import Interactions
from platforminfra.config import Config

TEST_ENVIDS = None
SCALE_TO = None


class PlatformInfraTestCase(unittest.TestCase):
    """Platfrom Infra Test Cases.

    A class whose instances are single test cases to test the PlatformInfra
    flask application.
    """

    def setUp(self):
        """Setup Unittest."""
        global TEST_ENVIDS
        global SCALE_TO
        config = Config()
        TEST_ENVIDS = config.test["environment_ids"]
        SCALE_TO = config.test["scale_to"]
        self.interactions = Interactions()

    def tearDown(self):
        """Destroy any deployments created."""
        for envid in TEST_ENVIDS:
                self.interactions.destroy(envid)

        self.interactions.close()

    def checkSuccess(self, response_data, message):
        """Check that "response" is "Success" in response data."""
        response = response_data["response"]
        self.assertEqual(
            response, "Success", message
        )

    def test_config_gitlab_url(self):
        """Test the gitlab URL is correct."""
        url = self.interactions.getConfigGitlabUrl()
        url_components = urlp.urlparse(url)
        print("Gitlab url from configuration:", url)
        self.assertTrue(url_components.scheme.startswith("http"))
        self.assertTrue(len(url_components.netloc) > 0)

    def test_scale(self):
        """Test the creation and scaling of one environment.

        1: Environmnet creation

          - Returns 201
          - Tests that the response is "Succcess"
          - Request status response until response is "Success"

        2: Scale Environment

          - Tests that the response is "Succcess"
          - Request status response until response is "Success"
          - Check that the correct number of servers are listed in the response
            data
          - Checks that the website returns a 200 status

        3: Destroy the scaled environment

          - Tests that the destroy command returns a 204 status
          - Tests that the destroy response is "Success"

        4:  Environments Listing

          - Tests that the new environment ID is no longer present in the
        environments list

        """
        envid = TEST_ENVIDS[0]

        # Create environment
        rv = self.interactions.create(envid, "testBuild", "test")
        self.assertEqual(rv.status_code, 201, "Environment creation")
        response_data = self.interactions.getResponseData(rv)
        self.checkSuccess(response_data, "Testing environment creation")

        # Wait for environment
        for i in range(1, 20):
            # Check Status of success
            rv = self.interactions.status(envid)
            response_data = self.interactions.getResponseData(rv)
            response = response_data["response"]
            if response == "Success":
                break
            time.sleep(2)
        self.checkSuccess(
            response_data,
            "Status of environment creation. " +
            "Response of:"+str(response_data)
        )

        # Scale environment
        rv = self.interactions.scale(envid, SCALE_TO)
        response_data = self.interactions.getResponseData(rv)
        self.checkSuccess(
            response_data,
            "Testing environment scale. " +
            "Response of:"+str(response_data)
        )

        # Wait for environment
        for i in range(1, 20):
            # Check Status of success
            rv = self.interactions.status(envid)
            response_data = self.interactions.getResponseData(rv)
            response = response_data["response"]
            if response == "Success":
                break
            time.sleep(2)
        self.assertEqual(
            response, "Success",
            "Status of environment scale after several at status request. " +
            "Response of:"+str(response_data)
        )

        # Check Status has SCALE_TO servers
        rv = self.interactions.status(envid)
        response_data = self.interactions.getResponseData(rv)
        self.checkSuccess(
            response_data,
            "Testing environment creation. Response of:"+str(response_data)
        )

        print("Checking response data of status check")
        vm_counter = 0
        for resource in response_data["Resources"][0]["Environment resources"]:
            if "name" in resource:
                # Check resources (whatever it is) succeeded
                self.assertEqual(
                    resource["provisioningState"], "Succeeded",
                    "Provisioning state for resource " + str(resource["name"])
                )
                # Match on test1 + number
                s = re.search('^.*test1(\d+)$', resource["name"])
                if s:
                    print("VM", resource["name"], "found in response data")
                    vm_counter = vm_counter + 1
                    self.assertEqual(
                        resource["status"], "VM running",
                        "VM is running"
                    )
        self.assertEqual(
            vm_counter, SCALE_TO,
            "Test for correct number of VMs"
        )

        # Website URL is up and running
        r = requests.get(self.interactions.getWebsiteUrl(envid))
        self.assertEqual(r.status_code, 200)

        # Environment destuction
        rv = self.interactions.destroy(envid)
        self.assertEqual(rv.status_code, 204, "Destroy environment")

        # Tests that the environment no longer shows in environments listing
        rv = self.interactions.getEnvironments()
        self.assertEqual(rv.status_code, 200, "Listing environments")
        response_data = self.interactions.getResponseData(rv)
        self.assertFalse(
            envid in response_data["Environments"],
            "Destroyed environment no longer in environments list"
        )

    def test_create_and_destroy(self):
        """Test the creation and destruction of one environment.

        Testing the following:

        1: Environment Creation

          - Returns 201
          - Correct keys found in JSON resonse data for response, servers,
            dns, and public ip address
          - Tests that the response is "Succcess"
          - Tests that website responds correctly

        2: Environments Listing

          - Tests that the new environment ID is present in the environments
        list

        3: Website URL

          - Tests that the URL is accessible and returns a 200 response

        4: Destroy Environment

          - Tests that the destroy command returns a 204 status
          - Tests that the destroy response is "Success"

        5:  Environments Listing

          - Tests that the new environment ID is no longer present in the
        environments list

        """
        envid = TEST_ENVIDS[0]

        print("Create and destroy of environment", envid)

        # Create environment
        rv = self.interactions.create(envid, "testBuild", "test")
        self.assertEqual(rv.status_code, 201, "Environment creation")
        response_data = self.interactions.getResponseData(rv)

        print("Creation response data:", str(response_data))

        # KeyErrors. i.e. does the response contain the fields we expect
        servers = response_data["Resources"][0]["servers"]
        print("Servers:", str(servers))
        domain_name = response_data["Resources"][0]["dns"]
        public_ip = response_data["Resources"][0]["vms"][0]["public_ip"]

        # Test that the environment shows in environments listing
        rv = self.interactions.getEnvironments()
        self.assertEqual(rv.status_code, 200, "Listing environments")
        response_data = self.interactions.getResponseData(rv)
        self.assertTrue(
            envid in response_data["Environments"],
            "Created environment shows in environments list"
        )

        # DNS resolves to correct IP
        dnsq = dns.resolver.query(domain_name, 'A')
        print("Domain name shows a DNS entry of:", dnsq.rrset[0].to_text())
        self.assertEqual(dnsq.rrset[0].to_text(), public_ip)

        # Website URL is up and running
        r = requests.get(self.interactions.getWebsiteUrl(envid))
        self.assertEqual(r.status_code, 200)

        # Environment destuction
        rv = self.interactions.destroy(envid)
        self.assertEqual(rv.status_code, 204, "Destroy environment")

        # Tests that the environment no longer shows in environments listing
        rv = self.interactions.getEnvironments()
        self.assertEqual(rv.status_code, 200, "Listing environments")
        response_data = self.interactions.getResponseData(rv)
        self.assertFalse(
            envid in response_data["Environments"],
            "Destroyed environment no longer in environments list"
        )


if __name__ == '__main__':
    unittest.main()
