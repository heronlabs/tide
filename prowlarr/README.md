# prowlarr — Prowlarr (Docker, LAN only)

Docker Compose service for [Prowlarr](https://prowlarr.com), the indexer manager, same style as `../jellyfin`.

- **Web UI:** `http://<host>:9696`
- **Config:** named volume `prowlarr_prowlarr-config`
- **Network:** external network `tide`, shared with the other services
- **Limits:** 1 CPU / 512M (`.env`)
- **Restart policy:** `always`

Prowlarr only searches: Radarr and Sonarr ask it for releases, pick one and send it to qBittorrent themselves. It never talks to qBittorrent.

## First access

The first access asks for an authentication method: pick **Forms**, set a user and password. Prowlarr pushes the indexers to Radarr and Sonarr, so it is Prowlarr that holds their API keys, not the other way round.

## Setup

1. **Indexers → Add Indexer:** add the indexers. Only indexers for content you have the right to download, keep and share (`../README.md`, Legal use).
2. **Settings → Apps → Add → Radarr:** Prowlarr Server `http://prowlarr:9696`, Radarr Server `http://radarr:7878`, the API key from Radarr (Settings → General). Sync Level **Full Sync**.
3. **Settings → Apps → Add → Sonarr:** the same, with `http://sonarr:8989` and the API key from Sonarr.

Prowlarr then keeps the indexers of Radarr and Sonarr in sync: an indexer is added once, here.

Example, Internet Archive: the public indexer in Prowlarr's list for [archive.org](https://archive.org/), the non-profit digital library whose collections include public-domain and openly licensed movies, such as the Blender open movies. It searches only the items the Archive serves as a torrent (format `Archive BitTorrent`), in their titles by default (**Search only in title**). Not every item there is openly licensed: an item's page names its licence when it has one, so take only what you have the right to. Seed Ratio and Seed Time empty, so qBittorrent's stop at ratio `0` applies; no tags, since it is not behind Cloudflare.

## Indexers behind Cloudflare

Adding an indexer behind Cloudflare fails with `Unable to access <indexer>, blocked by CloudFlare Protection.` Prowlarr reaches it through FlareSolverr (`../flaresolverr/README.md`), started on the network `tide`. Passing a site's challenge can breach that site's terms of use, so use it only with indexers whose terms allow automated access:

1. **Settings → Indexers → Indexer Proxies → + → FlareSolverr:** Name `FlareSolverr`, Tags `flaresolverr`, Host `http://flaresolverr:8191/`, Request Timeout `60`.
2. **Indexers → Add Indexer:** an indexer behind Cloudflare gets the tag `flaresolverr`. Prowlarr sends through the proxy only the indexers that share its tag; the others it reaches directly.
3. The tag does not stop the sync to Radarr and Sonarr as long as the apps under Settings → Apps have no tags.

## Commands

```bash
docker compose up -d          # start / apply changes
docker compose logs -f        # logs
docker compose pull && docker compose up -d   # update the image
docker compose down           # stop, keeps config
docker compose down -v        # stop AND delete the config volume
```
