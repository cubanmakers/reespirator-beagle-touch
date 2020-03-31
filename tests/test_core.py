##############################################################################
# For copyright and license notices, see LICENSE file in root directory
##############################################################################
import unittest

from respyrator import core


class TestCore(unittest.TestCase):
    def test(self):
        self.assertTrue(True)

    def test_core(self):
        core.load_config()
        self.assertIn('log_level', core.config)
