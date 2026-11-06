# Cloud transfer: complete in your PDF and here

1. Why must failing source tests block build/deploy? How do same-job steps differ from jobs using `needs`? What transfers the tested image between jobs?
2. Trace build once -> smoke exact image -> push that image -> registry manifest digest -> deploy digest -> inspect revision/image/readiness/authorized HTTP. Distinguish local image ID, registry manifest digest, mutable commit-SHA tag. How does poisoned latest demonstrate the risk?
3. Explain GitHub OIDC -> narrowly conditioned WIF provider -> dedicated publisher/deployer. Limit repository numeric IDs, audience, approved ref/environment; no untrusted PR deploy. Which jobs need contents: read and id-token: write? Separate publisher, deployer and runtime roles. No JSON keys. Why does local Python/Docker execution still require trusted source and a trusted host?

No cloud account, token, SDK, registry push, hosted Actions run or paid service is required or permitted for this exercise. This document is a design mapping, not proof WIF/cloud deployment worked.
