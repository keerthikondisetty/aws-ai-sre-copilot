.PHONY: install test lint format demo docker-build tf-fmt tf-validate manifests

install:
	python3 -m pip install -e '.[dev]'

test:
	pytest

lint:
	ruff check .
	ruff format --check .

format:
	ruff check --fix .
	ruff format .

demo:
	./scripts/demo.sh

docker-build:
	docker build -t ai-sre-copilot:local .

tf-fmt:
	terraform fmt -recursive infra

tf-validate:
	terraform -chdir=infra init -backend=false
	terraform -chdir=infra validate

manifests:
	kubectl kustomize deploy/overlays/dev

