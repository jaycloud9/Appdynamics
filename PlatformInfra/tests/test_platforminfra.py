import platforminfra
import unittest
from platforminfra.views import base_path
import urllib.parse as urlp
import json

TEST_ENVIRONMENTS = ['ghy543', '77h89d', 's8sf8s']


class PlatformInfraTestCase(unittest.TestCase):

    def setUp(self):
        platforminfra.app.config['TESTING'] = True
        self.app = platforminfra.app.test_client()

    def tearDown(self):
        pass

    def test_root(self):
        """Test that root page does not exist, to get some tests started"""
        rv = self.app.get(base_path)
        self.assertEqual(rv.status_code, 404, "Checking "+base_path)

    def test_get_environment(self):
        url = urlp.urljoin(base_path, "environments/")
        url = urlp.urljoin(url, TEST_ENVIRONMENTS[0])
        rv = self.app.get(url)
        self.assertEqual(rv.status_code, 200, "Checking "+url)
        data = json.loads(rv.get_data().decode("utf-8"))

        self.assertEqual(
            data["response"],
            "Success",
            "Checking successful json response for "+url
        )

        self.assertEqual(
            data["application"],
            "Retail_suite",
            "Checking applcation is Retail_suit for "+url
        )

    def test_get_unknown_environment(self):
        """Test that the system responds correctly to unknown env IDs"""
        url = urlp.urljoin(base_path, "environments/")
        url = urlp.urljoin(url, "INCORRECT_ENV_ID")
        rv = self.app.get(url)
        self.assertEqual(rv.status_code, 200, "Checking "+url)
        data = json.loads(rv.get_data().decode("utf-8"))

        self.assertEqual(
            data["response"],
            "Failure",
            "Checking reported failure for "+url
        )


if __name__ == '__main__':
    unittest.main()
