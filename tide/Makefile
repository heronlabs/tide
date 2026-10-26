.PHONY: build lint lint\:fix audit test test\:coverage test\:integration test\:mutation wire

build:
	uv build

lint:
	uv run ruff check src tests
	uv run ruff format --check src tests
	uv run pyright
	uv lock --check

lint\:fix:
	uv run ruff format src tests
	uv run ruff check --fix src tests

audit:
	uv export --frozen --format requirements-txt --no-emit-project \
		| uv run pip-audit --disable-pip --require-hashes --requirement /dev/stdin

test:
	uv run pytest tests/unit

test\:coverage:
	uv run pytest tests/unit --cov --cov-report=term-missing

test\:integration:
	uv run pytest tests/integration

test\:mutation:
	rm -rf mutants
	uv run mutmut run
	uv run mutmut export-cicd-stats
	uv run mutmut results
	uv run python -I -c 'import json, sys; s = json.load(open("mutants/mutmut-cicd-stats.json")); print("mutation: {killed} killed, {survived} survived, {no_tests} without tests, {total} total".format(**s)); sys.exit(s["survived"] + s["no_tests"] > 0)'

# Wires the running services, with the values of .env (see .env.example).
wire:
	set -a && . ./.env && set +a && uv run tide wire
