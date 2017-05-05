"""PlatformInfra Tests Module."""

import unittest
from platforminfra.helpers import Helpers


class HelpersTestCase(unittest.TestCase):
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

    def test_ValidString(self):
        """Test a strings validity for the platform.

        Ensure that any string is:
        - 'a-z'
        - '0-9'
        - '-'
        """
        validStrings = [
            "abcdefgh012984-",
            "abcd-efgh-gs928",
            "-sdwf12ggfsfs72"
        ]
        invalidStrings = [
            "A8sda-a02ddaaX%",
            "jhj*76^@1)()d+=",
            "\'aas\"23adsaXXk2"
        ]
        for string in validStrings:
            self.assertTrue(Helpers.validString(string))
        for string in invalidStrings:
            self.assertFalse(Helpers.validString(string))
        longString = "thisisaverylongstring"
        self.assertFalse(Helpers.validString(longString))


if __name__ == '__main__':
    unittest.main(
        failfast=True
    )
