# bazarr — Bazarr (Docker, LAN only)

Docker Compose service for [Bazarr](https://www.bazarr.media), which gets the subtitles of the movies and the shows, same style as `../jellyfin`.

- **Web UI:** `http://<host>:6767`
- **Library:** `~/Media` mounted whole at `/data`, as in Radarr and Sonarr, so their paths need no mapping
- **Config:** named volume `bazarr_bazarr-config`
- **Network:** external network `tide`, shared with the other services
- **Limits:** 1 CPU / 1G (`.env`)
- **Restart policy:** `always`

Bazarr syncs the movies of Radarr and the episodes of Sonarr. Each one gets the language profile `Portuguese (Brazil)`, and Bazarr searches the providers for the subtitle it lacks after each sync and on a schedule, and saves it next to the video with the same name and the language, where Jellyfin lists it. A video whose file already carries a Portuguese (Brazil) track (`../jellyfin/SUBTITLES.md`) lacks nothing and is skipped.

## First access

The web UI opens without a login: set one under **Settings → General → Security** (**Forms**, a user and a password). Settings → General → API Key is the key `tide wire` reads from `/config/config/config.yaml`.

## Setup

`make wire` (`../tide/README.md`) does these steps through the API:

1. **Settings → Languages:** enable **Portuguese (Brazil)**, add the profile `Portuguese (Brazil)` with that language, and set it as the default of the movies and the series.
2. **Settings → Providers:** **OpenSubtitles.com**, with a free account (`TIDE_OPENSUBTITLES_USERNAME` and `TIDE_OPENSUBTITLES_PASSWORD` in `tide/.env`). It is the only provider `make wire` enables, and only when that login is set: without it, `make wire` enables none.
3. **Settings → Radarr:** on, address `radarr`, port `7878`, Radarr's API key. **Settings → Sonarr:** the same with `sonarr`, `8989` and Sonarr's key.

To search now instead of waiting for the schedule: **Movies** (or **Series**) → the title → **Search**, or **Wanted** → **Search All**.

## Commands

```bash
docker compose up -d          # start / apply changes
docker compose logs -f        # logs
docker compose pull && docker compose up -d   # update the image
docker compose down           # stop, keeps config
docker compose down -v        # stop AND delete the config volume
```
