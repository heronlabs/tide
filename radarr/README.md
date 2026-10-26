# radarr — Radarr (Docker, LAN only)

Docker Compose service for [Radarr](https://radarr.video), which gets the movies, same style as `../jellyfin`.

- **Web UI:** `http://<host>:7878`
- **Library and downloads:** `~/Media` mounted whole at `/data`, as in qBittorrent: the movies in `/data/movies`, the downloads in `/data/downloads`
- **Config:** named volume `radarr_radarr-config`
- **Network:** external network `tide`, shared with the other services
- **Limits:** 1 CPU / 1G (`.env`)
- **Restart policy:** `always`

A movie added here, or requested in Seerr, is monitored: Radarr searches it through Prowlarr, sends the best release to qBittorrent with the category `radarr`, follows the queue and, when the torrent finishes, renames the movie and moves it into `/data/movies`, then asks Jellyfin to refresh. Downloads and library sit on the same mount, so the move is an instant rename.

## First access

The first access asks for an authentication method: pick **Forms**, set a user and password. Settings → General → API Key is the key Prowlarr, Seerr and Bazarr need.

## Setup

1. **Settings → Media Management:** turn on **Rename Movies**, with the folder and file format `{Movie Title} ({Release Year})`, as `../jellyfin/README.md` names them. Add the root folder `/data/movies`.
2. **Settings → Download Clients → Add → qBittorrent:** host `qbittorrent`, port `8080`, the qBittorrent user and password, category `radarr`. Under **Completed Download Handling**, turn on **Remove Completed**, so Radarr removes the torrent from qBittorrent once it imported it.
3. **Settings → Connect → Add → Emby / Jellyfin:** host `jellyfin`, port `8096`, an API key from Jellyfin (Dashboard → API Keys), **Update Library** on. Jellyfin sees the library at `/media`, not `/data`: when the form offers to map paths, map `/data/` to `/media/`; otherwise turn on real-time monitoring in the Jellyfin library.
4. **Settings → Media Management → Importing:** turn on **Import Extra Files** with the extension `srt`, so a subtitle that comes in the torrent is imported next to the video, named like it.
5. **Settings → Custom Formats → +:** the custom format `Portuguese (Brazil)`, with one **Language** condition, `Portuguese (Brazil)`, required. **Settings → Profiles:** the quality profile decides the release; score the custom format `100` in it, so a release in Portuguese (Brazil) wins over another of the same quality.
6. **Movies → Library Import:** pick `/data/movies`, so the movies already there are monitored and never downloaded again.

The indexers come from Prowlarr (`../prowlarr/README.md`): nothing to add here.

## Commands

```bash
docker compose up -d          # start / apply changes
docker compose logs -f        # logs
docker compose pull && docker compose up -d   # update the image
docker compose down           # stop, keeps config
docker compose down -v        # stop AND delete the config volume
```
