import os
import unittest
from unittest.mock import patch
from app import health


class AppTests(unittest.TestCase):
    def test_health(self):
        with patch.dict(os.environ, {"REVISION": "test-revision"}):
            self.assertEqual(health(), {"status": "ok", "revision": "test-revision"})
