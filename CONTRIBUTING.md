# Contributing

Use Python 3.12 and Terraform 1.13.3. Keep changes small enough to review and do not add AWS write
permissions to the runtime role without a separate architecture decision.

```bash
python3 -m venv .venv
source .venv/bin/activate
pip install -e '.[dev]'
make lint test manifests
```

For infrastructure changes, also run `make tf-validate`. Pull requests should describe the failure
mode being addressed, operational impact, rollback, and validation performed. New analyzer behavior
needs a deterministic test fixture. Never include live alarm payloads or production logs.

