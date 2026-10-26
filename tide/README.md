# tide — wires the media server services together

Python (stdlib only), run on the host by hand. `tide wire` does through the APIs what the READMEs of `../radarr`, `../sonarr`, `../prowlarr`, `../seerr`, `../bazarr` and `../jellyfin` (its library `Discover`) describe in the web UIs, so a new host, or a host whose volumes were deleted, is wired with one command. Each step replaces what an earlier run created, matched by name, so it is safe to run again, for example after changing a value in `.env`.

## What it does

| Service | Step | Values used |
|---|---|---|
| Radarr | Root folder `/data/movies` | |
| | Naming: rename on, folder and file `{Movie Title} ({Release Year})` | |
| | Custom format `Portuguese (Brazil)` (the language `Portuguese (Brazil)`, required, its id read from the app's `/api/v3/language`, since Radarr and Sonarr number their languages differently) scored `100` in the quality profile, so a release in Portuguese (Brazil) wins over another of the same quality | `TIDE_QUALITY_PROFILE` |
| | Download client `qBittorrent` at `qbittorrent:8080`, category `radarr`, Remove Completed and Remove Failed on | `TIDE_QBIT_USERNAME`, `TIDE_QBIT_PASSWORD` |
| | Connection `Jellyfin` at `jellyfin:8096`, Update Library on import, upgrade, rename and delete, paths mapped from `/data/` to `/media/` | `TIDE_JELLYFIN_API_KEY` |
| | Import Extra Files on, with the extension `srt`, so a subtitle in the torrent is imported next to the video | |
| Sonarr | The same, with the root folder `/data/shows`, the category `sonarr` and the naming `{Series TitleYear}/Season {season:00}/{Series TitleYear} - S{season:00}E{episode:00}` | the same |
| Prowlarr | Apps `Radarr` and `Sonarr`, Full Sync, so every indexer added in Prowlarr reaches both | the Radarr and Sonarr keys |
| Seerr | Servers `Radarr` and `Sonarr` as the defaults, with the quality profile, the root folder and a link to their web UI | `TIDE_QUALITY_PROFILE`, `TIDE_LAN_HOST` |
| | After the Jellyfin steps, the libraries of Jellyfin synced and every one enabled but `Discover`, whose placeholders Seerr would take as available | |
| Jellyfin | Plugin repository `Jelly Bridge` (JellyBridge's `manifest.json`), replaced or added by name, the other repositories kept | `TIDE_JELLYFIN_API_KEY` |
| | JellyBridge pointed at Seerr: `http://seerr:5055` with Seerr's API key, the library directory `/media/Discover` and the plugin on; what it shows and its other settings kept | the Seerr key |
| | Library `Discover` (mixed movies and shows) on `/media/Discover`, unless one has that name | |
| Bazarr | Language profile `Portuguese (Brazil)`, the default of the movies and the shows, with the other profiles and enabled languages kept | |
| | Provider OpenSubtitles.com, with its login, added to the ones enabled; without the login, no provider | `TIDE_OPENSUBTITLES_USERNAME`, `TIDE_OPENSUBTITLES_PASSWORD` |
| | Radarr at `radarr:7878` and Sonarr at `sonarr:8989`; Bazarr sees their files at the same `/data`, so no path is mapped | the Radarr and Sonarr keys |

Every address between services is the container name on the network `tide`. tide itself reaches them from the host on `localhost`, at the ports the compose files publish (`TIDE_*_URL` changes that).

The API keys of Radarr, Sonarr and Prowlarr come from `/config/config.xml` in each container, Seerr's from `/app/config/settings.json` and Bazarr's from `/config/config/config.yaml`, through `docker exec`, so they are never copied by hand; `TIDE_*_API_KEY` gives one instead. Jellyfin's is `TIDE_JELLYFIN_API_KEY`, which tide sends as `Authorization: MediaBrowser Token="<key>"`, the only form Jellyfin takes.

A step that fails, such as a service that is down or a wrong qBittorrent password, prints what the service answered, and the next steps still run. It does not do:

- the **logins** of the web UIs and **Seerr's Jellyfin sign-in**, which need a person;
- the **indexers**: pick them in Prowlarr, which syncs them to Radarr and Sonarr;
- the **Library Import**, in Radarr (Movies → Library Import, `/data/movies`) and Sonarr (Series → Library Import, `/data/shows`), to adopt what is already in `~/Media` once;
- **qBittorrent's own settings** (save paths, the ratio action), in `../qbittorrent/README.md`;
- **installing JellyBridge**, which restarts Jellyfin, and **what it shows**, in `../jellyfin/README.md`.

## Run

Before the first run: all services up and healthy (`docker ps`), Radarr, Sonarr and Prowlarr opened once in the browser to set their login, and Seerr's setup done up to the Jellyfin libraries (its Radarr and Sonarr step can be skipped). Bazarr needs nothing first. The Jellyfin steps need the JellyBridge plugin installed, from the repository the first run adds (`../jellyfin/README.md`); until then `jellyfin: JellyBridge` fails and the other steps still run. The host needs [uv](https://docs.astral.sh/uv/) and `docker`.

```bash
cp tide/.env.example tide/.env   # fill in; each value says why it is needed
chmod 600 tide/.env
make wire                        # from the root of the clone
```

```
done   radarr: root folder
...
done   bazarr: sonarr
wire: 24 done, 0 failed
```

It exits with `1` when a step failed and `2` when a required variable is missing.

## Commands

| Command | What |
|---|---|
| `make wire` | `tide wire` with the variables of `.env` |
| `make build` | `uv build`: wheel and sdist in `dist/`, with the `tide` command |
| `make lint` | `ruff check`, `ruff format --check` and `pyright` over `src` and `tests`, and `uv lock --check` |
| `make lint:fix` | `ruff format`, then `ruff check --fix` |
| `make audit` | `pip-audit` over the dependencies pinned in `uv.lock` |
| `make test` | Unit tests (`pytest tests/unit`) |
| `make test:coverage` | Unit tests with line and branch coverage; `main.py` is left out |
| `make test:integration` | Integration tests (`pytest tests/integration`): the real `tide wire` against fake services |
| `make test:mutation` | mutmut over `src/tide/` (`main.py` excluded) with the unit tests; fails when a mutant survives |

## Layout

- `src/tide/main.py`: builds the services and injects them into the commands (`tide wire` runs `run()`).
- `src/tide/application/cli/`: commands, one per file. `WireCommand` runs the wire and turns its report into output and the exit code.
- `src/tide/core/domain/`: the data that crosses the layers, one class per file: `WireReport` and `Failure`.
- `src/tide/core/interfaces/`: one `Protocol` per file (`MediaManager`, `IndexerManager`, `RequestManager`, `SubtitleManager`, `MediaServer`, `Wire`). pyright checks that each service matches its interface where `main.py` injects it.
- `src/tide/core/services/`: `WireService`, which holds the steps and their order and goes on after a step that failed.
- `src/tide/infrastructure/`: `http/` (`ApiClient`, the JSON calls and the form posts, and the helpers for the *arr schemas), `arr/` (Radarr and Sonarr, which share their API), `prowlarr/`, `seerr/`, `bazarr/`, `jellyfin/`, `docker/` (the API keys) and `environment/`.
- `tests/unit/`: one test file per service or command, in the same folders as `src/tide/`. A class per method (`TestGivenRun`) and one `test_should_...` per behavior, with one assertion each. Fakes live in the test file that uses them; the fake HTTP server lives in `tests/mocks/`.
- `tests/integration/`: one test file per command, running the real `tide wire` as a subprocess against a `FakeServer` per service, with only the `TIDE_*` variables each test sets.
