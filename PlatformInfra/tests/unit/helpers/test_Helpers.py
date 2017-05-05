"""PlatformInfra Tests Module."""

import unittest
from platforminfra.helpers import Helpers


class PlatformInfraHelpersHelpersTestCase(unittest.TestCase):
    """PlatformInfra Helpers Helpers Test.

    Test the Helpers Class within the Helpers module
    """

    def test_RandStrLength(self):
        """Test the Random String method.

        Validate that Strings of a length between 0 and 300 can be generated
        and that they are random
        """
        for length in range(300):
            randString = Helpers.randStr(length)
            self.assertEqual(len(randString), length)

        try:
            Helpers.randStr(301)
        except Exception as e:
            if (e.args and type(e.args[0]) is dict):
                self.assertEquals(e.args[0]['code'], 500)
                self.assertIn(
                    'randStr must be less than or equal to 300',
                    e.args[0]['error']
                )


if __name__ == '__main__':
    unittest.main(
        failfast=True
    )
