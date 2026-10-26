# flaresolverr — FlareSolverr (Docker, network tide only)

Docker Compose service for [FlareSolverr](https://github.com/FlareSolverr/FlareSolverr), the proxy that lets Prowlarr reach the indexers behind Cloudflare, same style as `../jellyfin`.

- **Address:** `http://flaresolverr:8191`, on the network `tide` only: no port is published, since only Prowlarr calls it
- **Config:** none, it keeps no state
- **Network:** external network `tide`, shared with the other services
- **Limits:** 1 CPU / 1G (`.env`); the headless Chromium is the heavy part
- **Restart policy:** `always`

Some indexers sit behind Cloudflare, which answers Prowlarr with a challenge instead of the page, so adding one fails with `Unable to access <indexer>, blocked by CloudFlare Protection.` FlareSolverr opens the page in a headless Chromium, passes the challenge and answers the page to Prowlarr. Prowlarr sends through it only the indexers tagged `flaresolverr`; the others it reaches directly.

## Terms of use

Passing a site's challenge can breach that site's terms of use. Use FlareSolverr only with indexers whose terms allow automated access and that serve content you have the right to download (`../README.md`, Legal use).

## Setup

FlareSolverr itself has nothing to set up. Prowlarr takes it as an indexer proxy, as `../prowlarr/README.md` describes under "Indexers behind Cloudflare".

## When it breaks

Cloudflare changes its challenge from time to time, and FlareSolverr stops passing it: the indexers tagged `flaresolverr` fail their test and their searches in Prowlarr. The fix comes in a new image:

```bash
docker compose pull && docker compose up -d
```

## Commands

```bash
docker compose up -d          # start / apply changes
docker compose logs -f        # logs
docker compose pull && docker compose up -d   # update the image
docker compose down           # stop
```
