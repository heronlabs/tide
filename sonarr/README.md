# sonarr — Sonarr (Docker, LAN only)

Docker Compose service for [Sonarr](https://sonarr.tv), which gets the shows, same style as `../jellyfin`.

- **Web UI:** `http://<host>:8989`
- **Library and downloads:** `~/Media` mounted whole at `/data`, as in qBittorrent: the shows in `/data/shows`, the downloads in `/data/downloads`
- **Config:** named volume `sonarr_sonarr-config`
- **Network:** external network `tide`, shared with the other services
- **Limits:** 1 CPU / 1G (`.env`)
- **Restart policy:** `always`

A show added here, or requested in Seerr, is monitored: Sonarr searches the missing episodes through Prowlarr, watches the RSS of the indexers for new ones, sends each release to qBittorrent with the category `sonarr`, follows the queue and, when the torrent finishes, renames the episodes and moves them into `/data/shows`, then asks Jellyfin to refresh. Downloads and library sit on the same mount, so the move is an instant rename.

## First access

The first access asks for an authentication method: pick **Forms**, set a user and password. Settings → General → API Key is the key Prowlarr, Seerr and Bazarr need.

## Setup

1. **Settings → Media Management:** turn on **Rename Episodes**, with the episode format `{Series TitleYear} - S{season:00}E{episode:00}`, the series folder `{Series TitleYear}` and the season folder `Season {season:00}`, as `../jellyfin/README.md` names them. Add the root folder `/data/shows`.
2. **Settings → Download Clients → Add → qBittorrent:** host `qbittorrent`, port `8080`, the qBittorrent user and password, category `sonarr`. Under **Completed Download Handling**, turn on **Remove Completed**, so Sonarr removes the torrent from qBittorrent once it imported it.
3. **Settings → Connect → Add → Emby / Jellyfin:** host `jellyfin`, port `8096`, an API key from Jellyfin (Dashboard → API Keys), **Update Library** on. Jellyfin sees the library at `/media`, not `/data`: when the form offers to map paths, map `/data/` to `/media/`; otherwise turn on real-time monitoring in the Jellyfin library.
4. **Settings → Media Management → Importing:** turn on **Import Extra Files** with the extension `srt`, so a subtitle that comes in the torrent is imported next to the video, named like it.
5. **Settings → Custom Formats → +:** the custom format `Portuguese (Brazil)`, with one **Language** condition, `Portuguese (Brazil)`, required. **Settings → Profiles:** the quality profile decides the release; score the custom format `100` in it, so a release in Portuguese (Brazil) wins over another of the same quality.
6. **Series → Library Import:** pick `/data/shows`, so the shows already there are monitored and the episodes on disk are never downloaded again.

The indexers come from Prowlarr (`../prowlarr/README.md`): nothing to add here.

## Commands

```bash
docker compose up -d          # start / apply changes
docker compose logs -f        # logs
docker compose pull && docker compose up -d   # update the image
docker compose down           # stop, keeps config
docker compose down -v        # stop AND delete the config volume
```
