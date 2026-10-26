# Security Policy

## Reporting a Vulnerability

Report vulnerabilities to **security@heronlabs.com**. Do not open public issues.

Expect a response within 72 hours. After triage we will keep you updated on progress and coordinate disclosure timing.

## Scope

The stack runs on one Ubuntu host and serves the LAN only. It handles:

- `tide/.env`, ignored by git, with the qBittorrent password and the Jellyfin API key: its mode must be `600`;
- the `.env` of each service, ignored by git, with host paths and resource caps;
- the web UIs of Jellyfin (`8096`), qBittorrent (`8080`), Prowlarr (`9696`), Radarr (`7878`), Sonarr (`8989`), Seerr (`5055`) and Bazarr (`6767`), published on the LAN and never forwarded on the router; each needs its own login, and the temporary admin password qBittorrent prints on its first start must be changed right away;
- the qBittorrent peer port `6881`, the only port that may be forwarded on the router.

`tide wire` runs by hand as the user. It reads the API keys of the services from their containers through `docker exec` and only changes their settings through their APIs; it never touches a file of the library.

### Supported versions

| Version | Supported |
|---------|-----------|
| latest release | ✅ |
| older | ❌ |

## Disclosure

We follow coordinated disclosure. A fix reaches `main` through a pull request and ships in the next release; its changelog entry credits the reporter unless they prefer anonymity.
