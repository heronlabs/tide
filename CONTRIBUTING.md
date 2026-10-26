# Contributing

## Setup

```bash
git clone git@github.com:heronlabs/tide.git
cd tide
git config core.hooksPath .githooks
make build
```

You need:

- [uv](https://docs.astral.sh/uv/), which fetches the Python in `tide/.python-version` and the dev tools locked in `tide/uv.lock`;
- Docker with Compose, for `make lint`, which validates the compose files, and to run the services.

`actionlint` and `shellcheck` run through `uvx`, at the versions pinned in the `Makefile`.

## Commands

| Command | Purpose |
|---------|---------|
| `make build` | Build tide's wheel and sdist in `tide/dist/` |
| `make lint` | actionlint, shellcheck, `docker compose config` of each service, then tide's ruff, pyright and `uv lock --check` |
| `make lint:fix` | Apply the fixes ruff can make in tide |
| `make audit` | pip-audit over tide's locked dependencies |
| `make test` | tide's unit tests |
| `make test:coverage` | tide's unit tests with line and branch coverage |
| `make test:integration` | tide's integration tests: the real `tide wire` against a fake server per service |
| `make wire` | `tide wire` on the host, with the variables of `tide/.env` |
| `make test:mutation` | mutmut over tide's source with the unit tests; fails when a mutant survives |

The tide targets run the target of the same name in `tide/Makefile`, so inside `tide/` the same names work.

## Workflow

1. Every change starts in a worktree and reaches `main` through a pull request. Nothing is committed to `main` directly.
2. One logical change per pull request, squash-merged.
3. Commits follow [Conventional Commits](https://www.conventionalcommits.org/) (`feat:`, `fix:`, `chore:`, etc.). The squash commit takes the title of the pull request, and the release takes its bump from it: a breaking change is a major, `feat:` a minor, anything else a patch.
4. Never edit `version.txt` or `CHANGELOG.md`. The release workflow bumps the version, writes the changelog and tags the release when the pull request is merged.

## Conventions

`AGENTS.md` is the reference. In short:

- **Every mutant is killed.** A surviving one needs a test, or a refactor when it is equivalent (`AGENTS.md`).
- **One behavior and one assertion per test.** No `parametrize`, no loops. New behavior needs tests; bug fixes need a regression test.
- **Each test builds its own data.** No module-level constants shared between tests.
- **Hand-written fakes, standard library only.** The runtime of tide has no dependency.
- **Integration tests run the real `tide wire`** with only the `TIDE_*` variables they set, every URL at a fake server and every API key given, so they never reach the real services or docker.

## CI

Every pull request must pass Build, Lint, Audit, Unit Tests, Integration Tests and Mutation Tests. The Mutation Tests job writes the counts of killed, surviving and untested mutants to its summary.
