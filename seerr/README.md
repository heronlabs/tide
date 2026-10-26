# seerr — Seerr (Docker, LAN only)

Docker Compose service for [Seerr](https://github.com/seerr-team/seerr), the request UI formerly known as Jellyseerr, same style as `../jellyfin`.

- **Web UI:** `http://<host>:5055`
- **Config:** named volume `seerr_seerr-config`
- **Network:** external network `tide`, shared with the other services
- **Limits:** 1 CPU / 1G (`.env`)
- **Restart policy:** `always`

Users sign in with their Jellyfin account, browse the TMDB catalog and request a movie or a show. Seerr creates it, monitored, in Radarr or Sonarr, which search and download it, and shows the request as available once it is in the Jellyfin library. Seerr itself downloads nothing.

## Setup

The first access runs the setup:

1. **Choose Jellyfin**, at `http://jellyfin:8096`, and sign in with the Jellyfin admin. Pick the libraries Movies and Shows; Seerr reads them to show what is already there. Leave `Discover` out: it holds only JellyBridge's placeholders (`../jellyfin/README.md`), which Seerr would take as available.
2. **Radarr:** host `radarr`, port `7878`, the API key from Radarr (Settings → General), the quality profile and the root folder `/data/movies`. Mark it as the default server.
3. **Sonarr:** host `sonarr`, port `8989`, the API key from Sonarr, the quality profile and the root folder `/data/shows`. Mark it as the default server.

`make wire` (`../tide/README.md`) does steps 2 and 3 through the API. It also syncs the libraries of step 1 from Jellyfin and enables every one but `Discover`.

On the first start, Seerr may warn that "the /app/config volume mount was not configured properly". It is a false alarm: the image marks an unmounted `/app/config` with an empty `DOCKER` file, and Docker copies it into the empty named volume along with the rest of the folder. The settings are saved in the volume. Remove the marker once, and it does not come back, since Docker only fills an empty volume:

```bash
docker exec seerr rm /app/config/DOCKER && docker restart seerr
```

Settings → Users → Import Jellyfin Users brings in the other accounts; each user's permissions say whether their requests need an approval. JellyBridge sends each favorite of the library `Discover` as a request of that user, so every Jellyfin user who uses it must be imported.

## Commands

```bash
docker compose up -d          # start / apply changes
docker compose logs -f        # logs
docker compose pull && docker compose up -d   # update the image
docker compose down           # stop, keeps config
docker compose down -v        # stop AND delete the config volume
```
