# qbittorrent — qBittorrent (Docker, LAN only)

Docker Compose service for qBittorrent, same style as `../jellyfin`.

- **Web UI:** `http://<host>:8080` (user `admin`)
- **Downloads:** `~/Media` mounted whole at `/data`, as in Radarr and Sonarr, with the downloads in `/data/downloads`
- **Network:** external network `tide`, shared with the other services
- **Config:** named volume `qbittorrent_qbittorrent-config`
- **Peer port:** 6881 tcp/udp. Works on the LAN; forwarding it on the router is optional.
- **Limits:** 2 CPUs / 2G (`.env`)
- **Restart policy:** `always`

## First access

The first start generates a temporary admin password, printed in the logs:

```bash
docker logs qbittorrent 2>&1 | grep -i password
```

Log in, then go to Tools → Options → Web UI → Authentication and set your own password.

## Commands

```bash
docker compose up -d          # start / apply changes
docker compose logs -f        # logs
docker compose pull && docker compose up -d   # update the image
docker compose down           # stop, keeps config
docker compose down -v        # stop AND delete the config volume
```

## Using it with Radarr and Sonarr

Radarr and Sonarr add the torrents here, each with its category (`radarr`, `sonarr`), follow them through the Web UI API at `http://qbittorrent:8080` and import them into the library when they finish (`../radarr/README.md`, `../sonarr/README.md`). They need these settings (Tools → Options):

- **Downloads → Default Save Path:** `/data/downloads`
- **Downloads → Keep incomplete torrents in:** `/data/downloads/incomplete`
- **BitTorrent → Seeding Limits → When ratio reaches:** `0`, then **Stop torrent** (**Pause torrent** in older versions), so nothing seeds after the download. Do not pick **Remove torrent**: Radarr and Sonarr must still see the finished torrent to import it, and they remove it themselves afterwards (**Remove Completed**).

Torrents added by hand, without a category, stay in `/data/downloads`: move them into the library by hand, named as in `../jellyfin/README.md`.

## Notes

No VPN: your IP is visible to the swarm. Use it for legitimate content only (Linux ISOs, public-domain and Creative Commons media such as the Blender open movies). Torrents from untrusted sources are a common malware vector.
