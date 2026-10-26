import os
import sys
from collections.abc import Mapping
from dataclasses import dataclass


# Read from environment variables (TIDE_*), loaded from tide/.env by `make wire`.
# The API keys of the services are optional: without one, KeyService reads it from the container.
# The OpenSubtitles.com login is optional too: without it, Bazarr uses only the providers without an account.
# A missing required variable prints its name and exits with code 2.
@dataclass(frozen=True)
class EnvironmentService:
    qbit_username: str
    qbit_password: str
    jellyfin_api_key: str
    quality_profile: str
    lan_host: str
    radarr_url: str
    sonarr_url: str
    prowlarr_url: str
    seerr_url: str
    bazarr_url: str
    jellyfin_url: str
    radarr_api_key: str | None
    sonarr_api_key: str | None
    prowlarr_api_key: str | None
    seerr_api_key: str | None
    bazarr_api_key: str | None
    opensubtitles_username: str | None
    opensubtitles_password: str | None

    @classmethod
    def from_env(cls, environ: Mapping[str, str] = os.environ) -> "EnvironmentService":
        def required(name: str) -> str:
            if not environ.get(name):
                raise ValueError(f"{name} is not set (see tide/.env.example)")
            return environ[name]

        try:
            return cls(
                qbit_username=environ.get("TIDE_QBIT_USERNAME", "admin"),
                qbit_password=required("TIDE_QBIT_PASSWORD"),
                jellyfin_api_key=required("TIDE_JELLYFIN_API_KEY"),
                quality_profile=environ.get("TIDE_QUALITY_PROFILE", "HD-1080p"),
                lan_host=required("TIDE_LAN_HOST"),
                radarr_url=environ.get("TIDE_RADARR_URL", "http://localhost:7878"),
                sonarr_url=environ.get("TIDE_SONARR_URL", "http://localhost:8989"),
                prowlarr_url=environ.get("TIDE_PROWLARR_URL", "http://localhost:9696"),
                seerr_url=environ.get("TIDE_SEERR_URL", "http://localhost:5055"),
                bazarr_url=environ.get("TIDE_BAZARR_URL", "http://localhost:6767"),
                jellyfin_url=environ.get("TIDE_JELLYFIN_URL", "http://localhost:8096"),
                radarr_api_key=environ.get("TIDE_RADARR_API_KEY") or None,
                sonarr_api_key=environ.get("TIDE_SONARR_API_KEY") or None,
                prowlarr_api_key=environ.get("TIDE_PROWLARR_API_KEY") or None,
                seerr_api_key=environ.get("TIDE_SEERR_API_KEY") or None,
                bazarr_api_key=environ.get("TIDE_BAZARR_API_KEY") or None,
                opensubtitles_username=environ.get("TIDE_OPENSUBTITLES_USERNAME") or None,
                opensubtitles_password=environ.get("TIDE_OPENSUBTITLES_PASSWORD") or None,
            )
        except ValueError as error:
            print(error, file=sys.stderr)
            sys.exit(2)
