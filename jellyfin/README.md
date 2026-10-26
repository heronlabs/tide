# jellyfin — Jellyfin media server (Docker, LAN only)

Docker Compose service for [Jellyfin](https://jellyfin.org).

- **Web UI:** `http://<host>:8096` (first access runs the setup wizard)
- **Library:** `~/Media/{movies,shows,music}`, and `~/Media/Discover` for JellyBridge, mounted at `/media` (read-write)
- **State:** named volumes `jellyfin_jellyfin-config` and `jellyfin_jellyfin-cache`
- **Network:** external network `tide`, shared with the other services, where Radarr, Sonarr and Seerr reach it as `http://jellyfin:8096`
- **Restart policy:** `always`, so it comes back on boot with Docker
- **Limits:** 4 CPUs / 3G (`.env`), so it cannot starve the other workloads of the host

## Commands

```bash
docker compose up -d          # start / apply changes
docker compose logs -f        # logs
docker compose pull && docker compose up -d   # update the image
docker compose down           # stop, keeps config and watch history
docker compose down -v        # stop AND delete config/cache volumes
```

## Library setup

In the wizard add libraries pointing to `/media/movies`, `/media/shows` and `/media/music`.
Name files as `Movies/Title (Year)/Title (Year).mkv` and `Shows/Show/Season 01/Show - S01E01.mkv` for good metadata matching.

## Discover (JellyBridge)

The [JellyBridge](https://github.com/kinggeorges12/JellyBridge) plugin brings Seerr's catalog into Jellyfin: it fills the library `Discover` with placeholders of the movies and shows its settings pick from that catalog, and a user requests one by marking it as a favorite. JellyBridge sends the request to Seerr as that user, so the Jellyfin users must be imported into Seerr (`../seerr/README.md`), and from there it follows the usual flow to Radarr or Sonarr. A requested item leaves `Discover`, and the download lands in Movies or Shows.

`make wire` (`../tide/README.md`) sets it up, except installing the plugin, which restarts Jellyfin, and picking the networks:

1. `make wire` adds the repository `Jelly Bridge`, `https://raw.githubusercontent.com/kinggeorges12/JellyBridge/refs/heads/main/manifest.json`, to Dashboard → Plugins → Catalog → Repositories. Its step `jellyfin: JellyBridge` fails with `no Name JellyBridge` until the plugin is installed, and the other steps still run.
2. Install JellyBridge from the catalog and restart Jellyfin.
3. `make wire` again points JellyBridge at Seerr, `http://seerr:5055` on the network `tide`, with Seerr's API key and the library directory `/media/Discover`, turns off Request 4K by user permission (on, a favorite of an admin is a 4K request, which Seerr has no 4K Radarr or Sonarr to send to), syncs on every start of Jellyfin (the sync task runs 24 hours after Jellyfin starts, which a host shut down every day never reaches) and turns it on; its other settings stay as they are. It creates the library `Discover` (mixed movies and shows) on `/media/Discover` unless one has that name, which Jellyfin only accepts once the folder exists (`mkdir -p ~/Media/Discover`), and has Seerr scan every library but `Discover`.
4. In JellyBridge's settings, pick what the library shows.

`~/Media/Discover` holds only placeholders and their metadata, which JellyBridge writes, sorts once a day and cleans up. Never put real media there, and never point Radarr, Sonarr or Bazarr at it. Seerr must not scan that library either (`../seerr/README.md`), or it would see the placeholders as available.

## Transcoding

CPU only for now. The only GPU the OS sees is the RTX 3060 (the Ryzen iGPU is disabled), so VAAPI is not available. Hardware acceleration would be NVENC, which needs `nvidia-container-toolkit` on the host plus `runtime: nvidia` / a GPU reservation in the compose file.
