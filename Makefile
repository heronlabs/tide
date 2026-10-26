ACTIONLINT = uvx --from actionlint-py==1.7.12.25 --with shellcheck-py==0.11.0.1 actionlint
SHELLCHECK = uvx --from shellcheck-py==0.11.0.1 shellcheck
COMPOSE_SERVICES = jellyfin qbittorrent prowlarr flaresolverr radarr sonarr seerr bazarr
TIDE = $(MAKE) --no-print-directory -C tide

.PHONY: build lint lint\:fix audit test test\:coverage test\:integration test\:mutation wire

build:
	$(TIDE) build

lint:
	$(ACTIONLINT)
	$(SHELLCHECK) .githooks/pre-commit
	for service in $(COMPOSE_SERVICES); do \
		docker compose -f $$service/docker-compose.yml --env-file $$service/.env.example config --quiet || exit 1; \
	done
	$(TIDE) lint

lint\:fix:
	$(TIDE) lint:fix

audit:
	$(TIDE) audit

test:
	$(TIDE) test

test\:coverage:
	$(TIDE) test:coverage

test\:integration:
	$(TIDE) test:integration

test\:mutation:
	$(TIDE) test:mutation

wire:
	$(TIDE) wire
