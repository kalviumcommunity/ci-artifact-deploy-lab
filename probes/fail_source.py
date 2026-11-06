"""Deliberate negative probe; excluded from normal test discovery."""
import unittest
from app import health


class InjectedFailure(unittest.TestCase):
    def test_source_gate_negative_control(self):
        self.assertEqual(health()["status"], "broken-on-purpose")
