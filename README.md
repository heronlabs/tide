# 🌊 tide — Self-hosted media server on one LAN host

[![CI][ci-badge]][ci-url]
[![Python 3.13][python-badge]][python-url]
[![License: MIT][license-badge]][license-url]
[![Version][version-badge]][releases-url]

> **Docker Compose stack** for a self-hosted media server, on one Ubuntu host on the LAN: Seerr takes the requests, Radarr and Sonarr get the movies and shows through Prowlarr and qBittorrent, Bazarr gets their subtitles, and Jellyfin plays them.

`tide wire`, in the `tide` folder, wires the services together through their APIs: Radarr, Sonarr, Prowlarr, Seerr and Bazarr to each other, to qBittorrent and to Jellyfin, and Jellyfin's library `Discover` to Seerr, from the values in `tide/.env`. It is Python with the standard library only. [tide/README.md](tide/README.md) covers what it does and its layout.

## Contents

- [How it works](#how-it-works)
- [Legal use](#legal-use)
- [Install](#install)
- [Setup](#setup)
- [URLs](#urls)
- [Architecture](#architecture)
- [Develop](#develop)
- [License](#license)

## How it works

```
Seerr ──request──▶ Radarr (movies) / Sonarr (shows) ──search──▶ Prowlarr ──▶ indexers
                         │
                         ├──sends the release──▶ qBittorrent ──▶ ~/Media/downloads
                         │
                         └──imports when it finishes──▶ ~/Media/{movies,shows} ──refresh──▶ Jellyfin
                                                                  ▲
                                          Bazarr ──.pt-BR.srt─────┘
```

A user requests a movie or a show in Seerr, signed in with their Jellyfin account, or marks it as a favorite in the Jellyfin library `Discover`, where the JellyBridge plugin shows Seerr's catalog and sends the favorite to Seerr as a request. Seerr adds it, monitored, to Radarr or Sonarr, which search it through the indexers Prowlarr manages, pick the release by their quality profile and send it to qBittorrent with their category. When the torrent finishes they rename it the way Jellyfin expects, move it into the library, ask Jellyfin to refresh and remove the torrent from qBittorrent. Sonarr also watches the indexers for the new episodes of the shows it monitors. Bazarr follows what they import and saves the missing Portuguese (Brazil) subtitles from OpenSubtitles.com next to each video. Nothing in the flow is manual. Music is not part of it: `~/Media/music` is managed by hand. `~/Media/Discover` holds only JellyBridge's placeholders, never real media.

The host keeps the library in `~/Media/{movies,shows,music}`, JellyBridge's placeholders in `~/Media/Discover` and the downloads in `~/Media/downloads`, on the same disk. qBittorrent, Radarr, Sonarr and Bazarr all mount `~/Media` at `/data`, so a download has the same path in all of them and the import is an instant rename. Jellyfin mounts `~/Media` at `/media`. The services reach each other by name (`http://radarr:7878`) on the external Docker network `tide`.

## Legal use

tide is a research and education project about integrating open-source tools through their APIs. Use it only for content you have the right to download, keep and share:

- BitTorrent uploads (seeds) what it downloads to other peers, and uploading is distribution.
- Add only indexers for that content, such as the Blender open movies, the public-domain works of the Internet Archive and Linux ISOs.
- Never publish Jellyfin to the internet with third-party content.
- FlareSolverr passes a site's challenge, which can breach that site's terms of use: use it only with indexers whose terms allow automated access ([flaresolverr/README.md](flaresolverr/README.md)).

## Install

The host is an Ubuntu machine with Docker Compose. Clone the repository anywhere, create the shared network and start the services:

```bash
git clone git@github.com:heronlabs/tide.git
cd tide
docker network create tide
for service in jellyfin qbittorrent prowlarr flaresolverr radarr sonarr seerr bazarr; do
  cp $service/.env.example $service/.env
  (cd $service && docker compose up -d)
done
```

Each `.env.example` lists the variables of its service; edit the copy when the host differs. The `.env` files are git-ignored.

## Setup

Set the services up, in this order, as the `README.md` of each describes. `make wire` does steps 3 to 7 through the APIs, except the indexers, the FlareSolverr proxy, the Library Import, and installing JellyBridge and picking what it shows, from the values in `tide/.env` (`cp tide/.env.example tide/.env`, mode `600`; [tide/README.md](tide/README.md) covers it):

1. Jellyfin: the setup wizard and the libraries, and an API key (Dashboard → API Keys) for Radarr, Sonarr and tide. JellyBridge and the library `Discover` come last, since they need Seerr's API key.
2. qBittorrent: the admin password and the save paths and seeding limit Radarr and Sonarr need.
3. Radarr and Sonarr: naming, root folder, qBittorrent as download client, the Jellyfin connection, the quality profile and the Library Import of what is already in `~/Media`.
4. Prowlarr: FlareSolverr as the proxy of the indexers behind Cloudflare, the indexers, and Radarr and Sonarr as apps.
5. Seerr: Jellyfin, Radarr and Sonarr.
6. Bazarr: the Portuguese (Brazil) profile, the subtitle provider OpenSubtitles.com, and Radarr and Sonarr.
7. Jellyfin: the JellyBridge plugin, installed from the repository `make wire` adds, then `make wire` again for its settings, the library `Discover` and Seerr leaving it out. Pick what it shows in its settings.

## URLs

On the host, `TIDE_LAN_HOST` in `tide/.env`, from any machine on the LAN:

| Service | URL |
|---|---|
| Jellyfin | `http://<host>:8096` |
| Seerr | `http://<host>:5055` |
| Radarr | `http://<host>:7878` |
| Sonarr | `http://<host>:8989` |
| Prowlarr | `http://<host>:9696` |
| qBittorrent | `http://<host>:8080` |
| Bazarr | `http://<host>:6767` |

Between the containers, on the network `tide`, each one is its container name on the same port (`http://radarr:7878`). FlareSolverr publishes no port: only Prowlarr calls it, at `http://flaresolverr:8191`.

## Architecture

One folder per service, each with its `docker-compose.yml`, its `.env.example` and a `README.md` with its setup, and `tide/` with `tide wire`:

```
jellyfin/             # Jellyfin, the media server — web UI and API on 8096, the library mounted read-write at /media, caps of 4 CPUs and 3G
qbittorrent/          # qBittorrent — web UI on 8080, peer port 6881 tcp and udp, ~/Media mounted at /data, caps of 2 CPUs and 2G
prowlarr/             # Prowlarr, the indexer manager — web UI on 9696, caps of 1 CPU and 512M
flaresolverr/         # FlareSolverr, the proxy Prowlarr uses for the indexers behind Cloudflare — no published port (Prowlarr calls it at http://flaresolverr:8191), caps of 1 CPU and 1G
radarr/               # Radarr, which gets the movies — web UI on 7878, ~/Media mounted at /data, caps of 1 CPU and 1G
sonarr/               # Sonarr, which gets the shows — web UI on 8989, ~/Media mounted at /data, caps of 1 CPU and 1G
seerr/                # Seerr (formerly Jellyseerr), the request UI — web UI on 5055, caps of 1 CPU and 1G
bazarr/               # Bazarr, which gets the Portuguese (Brazil) subtitles of the movies and episodes — web UI on 6767, ~/Media mounted at /data, caps of 1 CPU and 1G
tide/                 # tide wire — Python, standard library only, wires the services through their APIs from tide/.env
.github/workflows/    # continuous-integration (build, lint, audit, unit, integration and mutation tests on PRs), continuous-deployment (release on main)
.githooks/            # pre-commit — make -C tide lint test when staged changes touch tide's Python, pyproject.toml or uv.lock
Makefile              # make build · lint · lint:fix · audit · test · test:coverage · test:integration · test:mutation · wire
AGENTS.md             # code map and conventions
CONTRIBUTING.md       # setup and workflow
SECURITY.md           # vulnerability reporting and scope
```

The caps leave room for the other workloads of the host.

Each service's README covers its part of the setup: [jellyfin/README.md](jellyfin/README.md) the commands, the library setup, the Discover library of JellyBridge and transcoding, and [jellyfin/SUBTITLES.md](jellyfin/SUBTITLES.md) where the subtitles come from; [qbittorrent/README.md](qbittorrent/README.md) the first access, the commands and the settings Radarr and Sonarr need; [prowlarr/README.md](prowlarr/README.md) the indexers, with the Internet Archive as the example, FlareSolverr as the proxy of those behind Cloudflare, and the sync to Radarr and Sonarr; [flaresolverr/README.md](flaresolverr/README.md) the terms of use of the sites it reaches, the commands and the new image that fixes it when Cloudflare changes its challenge; [radarr/README.md](radarr/README.md), [sonarr/README.md](sonarr/README.md), [seerr/README.md](seerr/README.md) and [bazarr/README.md](bazarr/README.md) the setup of each.

## Develop

```bash
make build              # tide's wheel and sdist in tide/dist/
make lint               # actionlint, shellcheck, docker compose config, then tide's ruff, pyright and uv lock --check
make test               # tide's unit tests
make test:integration   # runs the real tide wire against fake services
make test:mutation      # mutmut over tide's source; fails when a mutant survives
```

[CONTRIBUTING.md](CONTRIBUTING.md) has the setup and the workflow. [AGENTS.md](AGENTS.md) has the code map and the conventions. Vulnerabilities go through [SECURITY.md](SECURITY.md).

## License

[MIT](LICENSE) © Lucas Lacerda

[ci-badge]: https://github.com/heronlabs/tide/actions/workflows/continuous-integration.yml/badge.svg
[ci-url]: https://github.com/heronlabs/tide/actions/workflows/continuous-integration.yml
[python-badge]: https://img.shields.io/badge/Python-3.13-blue.svg
[python-url]: https://www.python.org/
[license-badge]: https://img.shields.io/badge/License-MIT-blue.svg
[license-url]: ./LICENSE
[version-badge]: https://img.shields.io/github/v/release/heronlabs/tide
[releases-url]: https://github.com/heronlabs/tide/releases
