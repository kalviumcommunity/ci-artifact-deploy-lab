"""Mocked command-boundary tests, NOT real Docker/cloud integration."""
import unittest
from unittest.mock import patch
import local_ci as ci

ID = "sha256:" + "a" * 64


class DriverTests(unittest.TestCase):
    def test_cloud_refused_before_external_commands(self):
        with patch.object(ci, "command") as cmd:
            with self.assertRaisesRegex(RuntimeError, "BEFORE external"):
                ci.run(dict(ci.GOOD, release_mode="cloud"))
            cmd.assert_not_called()

    def test_missing_boundary_fail_closed(self):
        with patch.object(ci, "command") as cmd:
            with self.assertRaises(RuntimeError):
                ci.run({})
            cmd.assert_not_called()

    def test_malformed_and_missing_image_ids(self):
        for value in ("", "latest", "sha256:abc", "sha256:" + "G" * 64):
            with self.subTest(value=value), self.assertRaises(RuntimeError):
                ci.image_id(value)

    def test_invalid_policy_no_execution(self):
        with patch.object(ci, "command") as cmd:
            with self.assertRaises(RuntimeError):
                ci.run(dict(ci.GOOD, order=["deploy", "test", "build"]))
            cmd.assert_not_called()

    def test_source_failure_no_build_or_deploy(self):
        with patch.object(ci, "source_tests", side_effect=RuntimeError("negative source test")), patch.object(ci, "command", return_value="") as cmd:
            with self.assertRaises(RuntimeError):
                ci.run(ci.GOOD, inject=True)
            self.assertFalse(any(c.args[0][:2] in (["docker", "build"], ["docker", "run"]) for c in cmd.call_args_list))

    def fake_command(self, args):
        if args == ["git", "rev-parse", "HEAD"]:
            return "b" * 40
        if args[:3] == ["docker", "image", "inspect"]:
            return ID
        return ""

    def test_smoke_failure_no_deploy_and_cleanup(self):
        with patch.object(ci, "source_tests"), patch.object(ci, "command", side_effect=self.fake_command) as cmd, patch.object(ci, "verify", side_effect=RuntimeError("bad smoke")):
            with self.assertRaises(RuntimeError):
                ci.run(ci.GOOD)
            runs = [c.args[0] for c in cmd.call_args_list if c.args[0][:2] == ["docker", "run"]]
            self.assertEqual(len(runs), 1)
            self.assertTrue(any(c.args[0][:3] == ["docker", "rm", "-f"] for c in cmd.call_args_list))

    def test_success_order_and_exact_identity(self):
        events = []
        def command(args):
            if args[:2] == ["docker", "build"]: events.append("build")
            if args[:2] == ["docker", "run"]:
                events.append("smoke" if "-smoke" in args[4] else "deploy")
                self.assertEqual(args[-1], ID)
            return self.fake_command(args)
        with patch.object(ci, "source_tests", side_effect=lambda _: events.append("test")), patch.object(ci, "command", side_effect=command), patch.object(ci, "verify", side_effect=lambda *args: events.append("verify")):
            ci.run(ci.GOOD)
        self.assertEqual(events, ["test", "build", "smoke", "verify", "deploy", "verify"])

    def test_malformed_build_id_aborts_before_container(self):
        def command(args):
            return "bad" if args[:3] == ["docker", "image", "inspect"] else self.fake_command(args)
        with patch.object(ci, "source_tests"), patch.object(ci, "command", side_effect=command) as cmd:
            with self.assertRaisesRegex(RuntimeError, "malformed"):
                ci.run(ci.GOOD)
            self.assertFalse(any(c.args[0][:2] == ["docker", "run"] for c in cmd.call_args_list))

    def test_running_image_mismatch_fails_before_http(self):
        with patch.object(ci, "command", return_value="sha256:" + "c" * 64), patch.object(ci.urllib.request, "urlopen") as http:
            with self.assertRaisesRegex(RuntimeError, "differs"):
                ci.verify("own-container", ID, "revision")
            http.assert_not_called()
