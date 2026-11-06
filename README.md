# CI artifact deployment lab

A green test is useful only if its artifact is the one you release.

This is a **local CI simulation**, manually launched on your computer. It is not hosted GitHub Actions and not cloud deployment. Only three `pipeline.json` fields need repair. Supplied Python driver, app, Dockerfile and tests stay unchanged. No dependencies beyond Python standard library, Docker and Git.

## Before class
Install Python 3.10+, Git and an institution-approved Docker runtime. Start Docker. Pre-pull `python:3.12-slim` before the 30-minute assignment. Use macOS/Linux Bash, or WSL Bash on Windows, with `python3` and `docker` available together. These are not PowerShell commands. Fork this public repository, clone your own fork and make a `solution` branch. No token, registry account or cloud setup needed. Docker can download its public base image; app traffic stays localhost.

```bash
python3 --version
docker info
docker pull python:3.12-slim
git switch -c solution
python3 -m unittest discover -s tests -v
```

Expect **exactly three policy failures** on starter main. Mocked driver tests pass without executing Docker. Default simulation refuses cloud mode before even Git/source commands. This is deliberate fail-closed behavior, not a fourth fault.

## Exactly three tasks, 10 marks, 30 minutes
1. Gate (3): change `order` to `test, build, deploy`. Explain source gate vs built-image smoke. Commit this repair.
2. Identity (3): change `deploy_ref` from `latest` to `tested-image-id`. Explain local image ID vs registry manifest digest vs mutable SHA tag. Commit this repair.
3. Boundary and transfer (4): change `release_mode` to `local-only`, complete CLOUD_MAPPING.md and commit. Run all probes below; record five labelled evidence groups in one PDF under **2,000,000 bytes**. Include your public fork solution-branch URL and final commit in PDF. Upload only PDF; no PR or video submission.

After fixing all three fields, commit changes first (runner rejects dirty source), then:
```bash
python3 -m unittest discover -s tests -v
python3 local_ci.py --simulate --inject-test-failure
python3 local_ci.py --simulate --poison-tag
python3 local_ci.py --check-boundary
git rev-parse HEAD
```
Injected test command must exit nonzero and skip build/deploy. Next command must succeed: source tests, one candidate build, exact-ID smoke, local deploy, inspect `.Image`, HTTP revision. Poison probe builds a separate DECOY counterexample only, moves convenience latest tag, and proves deployment ignores it. Normal `--simulate` builds only candidate once. Random container names and random localhost port avoid collisions. `finally` removes own containers/tags even after errors; cached untagged images may remain. Never globally prune. Interrupt normally with Ctrl-C, not force-kill.

**Evidence groups:** A baseline three red tests; B policy diff plus real failing source test/skipped downstream; C ordered passing run; D candidate/tested/running IDs plus HTTP and tag-poison counterexample; E safe boundary result and written cloud mapping. Groups may span screenshots. Use genuine terminal captures, readable IDs, no secrets. Mocked command-boundary tests are not real Docker integration evidence. Real Docker simulation proves local packaging/identity/HTTP, not registry, OIDC/IAM, persistence or production correctness. Student screenshots must be your own.

Run only trusted source/tests. Python executes on host; Docker daemon controls containers. No Docker socket is mounted into helper containers, no shell policy evaluation, no cloud subprocess path, no credentials requested. A malicious source change can still execute code on your machine. This lab is not a sandbox for untrusted PRs.
