"""Three independent policy contracts. Keep trusted tests unchanged."""
import json
from pathlib import Path
import unittest

POLICY = json.loads((Path(__file__).resolve().parents[1] / "pipeline.json").read_text())


class PipelinePolicy(unittest.TestCase):
    def test_1_gate(self):
        self.assertEqual(POLICY.get("order"), ["test", "build", "deploy"], "source test must gate build/deploy")

    def test_2_identity(self):
        self.assertEqual(POLICY.get("deploy_ref"), "tested-image-id", "latest can move after testing")

    def test_3_boundary(self):
        self.assertEqual(POLICY.get("release_mode"), "local-only", "cloud is outside this lab")
