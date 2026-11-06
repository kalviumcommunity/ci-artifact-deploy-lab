"""Supplied local CI simulation. No cloud/registry execution path."""
import argparse
import json
import re
import subprocess
import sys
import time
import urllib.error
import urllib.request
import uuid
from pathlib import Path

ROOT = Path(__file__).resolve().parent
GOOD = {"order": ["test", "build", "deploy"], "deploy_ref": "tested-image-id", "release_mode": "local-only"}


def contracts(policy):
    return [name for name, value in GOOD.items() if policy.get(name) != value]


def command(args):
    print("RUN " + " ".join(args), flush=True)
    result = subprocess.run(args, cwd=ROOT, text=True, stdout=subprocess.PIPE,
                            stderr=subprocess.STDOUT, timeout=180)
    if result.stdout:
        print(result.stdout.rstrip(), flush=True)
    if result.returncode:
        raise RuntimeError(f"command exit={result.returncode}: {args[0]}")
    return result.stdout.strip()


def image_id(value):
    if not re.fullmatch(r"sha256:[0-9a-f]{64}", value):
        raise RuntimeError("missing or malformed image ID; refusing release")
    return value


def boundary(policy):
    # Runs before even Git or source tests. Never add a cloud command here.
    if policy.get("release_mode") != "local-only":
        raise RuntimeError("cloud mode refused BEFORE external commands")


def source_tests(inject=False):
    command([sys.executable, "-m", "unittest", "discover", "-s", "tests", "-p", "test_app.py", "-v"])
    if inject:
        # A real, deliberately failing source-level unittest, not a printed failure.
        command([sys.executable, "-m", "unittest", "probes.fail_source", "-v"])


def verify(name, expected, revision):
    running = image_id(command(["docker", "inspect", name, "--format", "{{.Image}}"] ))
    if running != expected:
        raise RuntimeError("running image differs from tested image")
    binding = json.loads(command(["docker", "inspect", name, "--format", '{{json .NetworkSettings.Ports}}']))
    port = binding["8080/tcp"][0]["HostPort"]
    url = f"http://127.0.0.1:{port}/health"
    for _ in range(40):
        try:
            with urllib.request.urlopen(url, timeout=0.5) as response:
                body = json.load(response)
                if response.status != 200 or body != {"status": "ok", "revision": revision}:
                    raise RuntimeError("HTTP response/revision mismatch")
                print(f"HTTP {url} 200 {json.dumps(body)}", flush=True)
                print(f"RUNNING_ID={running}", flush=True)
                return
        except (urllib.error.URLError, TimeoutError, ConnectionError):
            time.sleep(0.1)
    raise RuntimeError("readiness deadline exceeded")


def run(policy, inject=False, poison=False):
    boundary(policy)
    faults = contracts(policy)
    if faults:
        raise RuntimeError("policy refused: " + ", ".join(faults))
    prefix = "ci-lab-" + uuid.uuid4().hex[:10]
    tag, decoy = prefix + ":latest", prefix + ":decoy"
    names = [prefix + "-smoke", prefix + "-deploy"]
    tags = [tag]
    stage = "test"
    try:
        print("LOCAL CI SIMULATION: source-test -> build -> image-smoke -> deploy -> verify", flush=True)
        source_tests(inject)
        stage = "build"
        revision = command(["git", "rev-parse", "HEAD"])
        if not re.fullmatch(r"[0-9a-f]{40}", revision):
            raise RuntimeError("invalid source revision")
        if command(["git", "status", "--porcelain"]):
            raise RuntimeError("commit changes first: revision evidence needs clean source")
        print(f"SOURCE_COMMIT={revision}", flush=True)
        command(["docker", "build", "--build-arg", f"REVISION={revision}", "-t", tag, "."])
        candidate = image_id(command(["docker", "image", "inspect", tag, "--format", "{{.Id}}"] ))
        print(f"CANDIDATE_ID={candidate}", flush=True)
        stage = "image-smoke"
        def start(name, identity):
            command(["docker", "run", "-d", "--name", name, "--cpus", "1", "--memory", "128m", "--read-only", "--cap-drop", "ALL", "--security-opt", "no-new-privileges", "-p", "127.0.0.1::8080", identity])
        start(names[0], candidate)
        verify(names[0], candidate, revision)
        tested = candidate
        print(f"TESTED_ID={tested}", flush=True)
        if poison:
            # Same source, different revision argument: deliberately distinguishable image.
            tags.append(decoy)
            command(["docker", "build", "--build-arg", "REVISION=DECOY", "-t", decoy, "."])
            decoy_id = image_id(command(["docker", "image", "inspect", decoy, "--format", "{{.Id}}"] ))
            if decoy_id == tested:
                raise RuntimeError("decoy must differ")
            command(["docker", "tag", decoy_id, tag])
            print(f"POISONED_LATEST={decoy_id}; deploy must ignore tag", flush=True)
        stage = "deploy"
        start(names[1], tested)
        stage = "verify"
        verify(names[1], tested, revision)
        print("PASS candidate=tested=running; local-only; no registry digest claimed", flush=True)
    except Exception:
        if stage == "test":
            print("SKIPPED build, image-smoke, deploy, verify: source tests failed", flush=True)
        elif stage == "image-smoke":
            print("SKIPPED deploy, verify: image smoke failed", flush=True)
        raise
    finally:
        # Own random names only. No prune, no unrelated resources, no socket mount.
        for name in names:
            try:
                command(["docker", "rm", "-f", name])
            except Exception as error:
                print(f"cleanup note: {error}", flush=True)
        if stage != "test":
            for tag_name in tags:
                try:
                    command(["docker", "image", "rm", tag_name])
                except Exception as error:
                    print(f"cleanup note: {error}", flush=True)


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--simulate", action="store_true", required=False)
    parser.add_argument("--inject-test-failure", action="store_true")
    parser.add_argument("--poison-tag", action="store_true")
    parser.add_argument("--check-boundary", action="store_true")
    args = parser.parse_args()
    if args.check_boundary:
        command([sys.executable, "-m", "unittest", "discover", "-s", "tests", "-p", "test_driver.py", "-v"])
    elif args.simulate:
        run(json.loads((ROOT / "pipeline.json").read_text()), args.inject_test_failure, args.poison_tag)
    else:
        parser.error("choose --simulate or --check-boundary")


if __name__ == "__main__":
    try:
        main()
    except (RuntimeError, ValueError, OSError, subprocess.TimeoutExpired) as error:
        print(f"FAIL {error}", flush=True)
        sys.exit(1)
