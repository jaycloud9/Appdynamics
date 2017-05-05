"""PlatformInfra Tests Module."""

import unittest
import xmlrunner

class PlatformInfraTestCase(unittest.TestCase):
    """Platfrom Infra Test Cases.

    A class whose instances are single test cases to test the PlatformInfra
    flask application.
    """

    def test_hello(self):
        print('hello')
        self.assertTrue(True)

    def test_hello2(self):
        print('hello2')
        self.assertEqual('bob', 'Bob')

if __name__ == '__main__':
    unittest.main(
        failfast=True,
        testRunner=xmlrunner.XMLTestRunner(output='/report.xml')
    )
