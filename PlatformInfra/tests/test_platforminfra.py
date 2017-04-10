import platforminfra
import unittest
from platforminfra.views import base_path
import urllib.parse as urlp
import json
import requests
import dns.resolver

TEST_UUIDS = ['abcdefghijk0']


class PlatformInfraTestCase(unittest.TestCase):
    """A class whose instances are single test cases to test the PlatformInfra
    flask application.
    """

    def setUp(self):
        # disable the error catching during request handling
        platforminfra.app.config['TESTING'] = True
        self.app = platforminfra.app.test_client()

    def tearDown(self):
        for uuid in TEST_UUIDS:
            self.destroy(uuid)

    def create(self, uuid, application, infrastructureTemplateID):
        """Creates an environment"""
        print("Creating environment", uuid)
        url = urlp.urljoin(base_path, "environments")
        request_data = json.dumps(
            dict(
                id=uuid,
                application=application,
                infrastructureTemplateID=infrastructureTemplateID
            )
        )
        print(request_data)
        return self.app.post(
            url,
            data=request_data, content_type='application/json'
        )

    def destroy(self, uuid):
        """Destroy an environment"""
        print("Destroying environment", uuid)
        url = urlp.urljoin(base_path, "environments/" + uuid)
        return self.app.delete(url)

    def getEnvironments(self):
        """Returns response of environments GET request"""
        url = urlp.urljoin(base_path, "environments")
        return self.app.get(url)

    def getResponseData(self, rv):
        """Returns JSON data from a flask response"""
        return json.loads(rv.get_data().decode("utf-8"))

    def test_root(self):
        """Test that root page does not exist"""
        rv = self.app.get(base_path)
        self.assertEqual(rv.status_code, 404, "Checking "+base_path)

    def test_create_and_destroy(self):
        """Tests creation and destruction of one environment.

        Testing the following:

        1: Environment Creation

          - Returns 200
          - Correct keys found in JSON resonse data for response, servers,
          git_url, dns, and public ip address
          - Tests that the response is "Succcess"
          - Tests that the servers are "t24"
          - Tests that the GitLab URL is correct

        2: Environments Listing

          - Tests that the new environment ID is present in the environments
        list

        3: GitLab

          - Tests that the hostname for GitLab resolves to the IP address
            stated in the environment creation step
          - Tests that the URL is accessible and returns a 200 response

        4: Destroy Environment

          - Tests that the destroy command returns a 200 status
          - Tests that the destroy response is "Success"

        5:  Environments Listing

          - Tests that the new environment ID is no longer present in the
        environments list

        """
        uuid = TEST_UUIDS[0]

        # Create environment
        rv = self.create(uuid, "T24-Pipeline", "test")
        self.assertEqual(rv.status_code, 200, "Environment creation")
        response_data = self.getResponseData(rv)

        # KeyErrors. i.e. does the response contain the fields we expect
        response = response_data["response"]
        servers = response_data["Resources"][0]["servers"]
        git_url = response_data["Resources"][1]["git_url"]
        domain_name = response_data["Resources"][0]["dns"]
        public_ip = response_data["Resources"][0]["vms"][0]["public_ip"]

        # Response data is correct
        self.assertEqual(
            response, "Success",
            "Testing environment creation"
        )
        self.assertEqual(
            servers, "t24",
            "Testing response for t24 servers"
        )
        self.assertEqual(
            git_url, "https://gitlab.temenos.cloud/"+uuid+"/customer-demo",
            "Testing response for t24 servers"
        )

        # Test that the environment shows in environments listing
        rv = self.getEnvironments()
        self.assertEqual(rv.status_code, 200, "Listing environments")
        response_data = self.getResponseData(rv)
        self.assertTrue(
            uuid in response_data["Environments"],
            "Created environment shows in environments list"
        )

        # DNS resolves to correct IP
        dnsq = dns.resolver.query(domain_name, 'A')
        print("Got", dnsq.rrset[0].to_text())

        self.assertTrue(dnsq.rrset[0].to_text(), public_ip)

        # GIT URL is up and running
        r = requests.head(git_url)
        self.assertTrue(r.status_code, 200)

        # Environment destuction
        rv = self.destroy(uuid)
        self.assertEqual(rv.status_code, 200, "Destroy environment")
        response_data = self.getResponseData(rv)
        response = response_data["response"]
        self.assertEqual(
            response, "Success",
            "Testing environment destruction"
        )

        # Tests that the environment no longer shows in environments listing
        rv = self.getEnvironments()
        self.assertEqual(rv.status_code, 200, "Listing environments")
        response_data = self.getResponseData(rv)
        self.assertFalse(
            uuid in response_data["Environments"],
            "Destroyed environment no longer in environments list"
        )


if __name__ == '__main__':
    unittest.main()
