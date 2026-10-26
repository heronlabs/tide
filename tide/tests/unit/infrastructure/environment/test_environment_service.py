import pytest

from tide.infrastructure.environment.environment_service import EnvironmentService


class TestGivenFromEnv:
    def test_should_read_every_variable(self):
        environment_service = EnvironmentService.from_env(
            {
                "TIDE_QBIT_USERNAME": "lucas",
                "TIDE_QBIT_PASSWORD": "qbit-password",
                "TIDE_JELLYFIN_API_KEY": "jellyfin-key",
                "TIDE_QUALITY_PROFILE": "Ultra-HD",
                "TIDE_LAN_HOST": "192.168.1.10",
                "TIDE_RADARR_URL": "http://radarr.lan:7878",
                "TIDE_SONARR_URL": "http://sonarr.lan:8989",
                "TIDE_PROWLARR_URL": "http://prowlarr.lan:9696",
                "TIDE_SEERR_URL": "http://seerr.lan:5055",
                "TIDE_BAZARR_URL": "http://bazarr.lan:6767",
                "TIDE_JELLYFIN_URL": "http://jellyfin.lan:8096",
                "TIDE_RADARR_API_KEY": "radarr-key",
                "TIDE_SONARR_API_KEY": "sonarr-key",
                "TIDE_PROWLARR_API_KEY": "prowlarr-key",
                "TIDE_SEERR_API_KEY": "seerr-key",
                "TIDE_BAZARR_API_KEY": "bazarr-key",
                "TIDE_OPENSUBTITLES_USERNAME": "lucas",
                "TIDE_OPENSUBTITLES_PASSWORD": "opensubtitles-password",
            }
        )

        assert environment_service == EnvironmentService(
            qbit_username="lucas",
            qbit_password="qbit-password",
            jellyfin_api_key="jellyfin-key",
            quality_profile="Ultra-HD",
            lan_host="192.168.1.10",
            radarr_url="http://radarr.lan:7878",
            sonarr_url="http://sonarr.lan:8989",
            prowlarr_url="http://prowlarr.lan:9696",
            seerr_url="http://seerr.lan:5055",
            bazarr_url="http://bazarr.lan:6767",
            jellyfin_url="http://jellyfin.lan:8096",
            radarr_api_key="radarr-key",
            sonarr_api_key="sonarr-key",
            prowlarr_api_key="prowlarr-key",
            seerr_api_key="seerr-key",
            bazarr_api_key="bazarr-key",
            opensubtitles_username="lucas",
            opensubtitles_password="opensubtitles-password",
        )

    def test_should_default_to_the_local_services_without_keys(self):
        environment_service = EnvironmentService.from_env(
            {
                "TIDE_QBIT_PASSWORD": "qbit-password",
                "TIDE_JELLYFIN_API_KEY": "jellyfin-key",
                "TIDE_LAN_HOST": "192.168.1.10",
                "TIDE_RADARR_API_KEY": "",
                "TIDE_OPENSUBTITLES_USERNAME": "",
            }
        )

        assert environment_service == EnvironmentService(
            qbit_username="admin",
            qbit_password="qbit-password",
            jellyfin_api_key="jellyfin-key",
            quality_profile="HD-1080p",
            lan_host="192.168.1.10",
            radarr_url="http://localhost:7878",
            sonarr_url="http://localhost:8989",
            prowlarr_url="http://localhost:9696",
            seerr_url="http://localhost:5055",
            bazarr_url="http://localhost:6767",
            jellyfin_url="http://localhost:8096",
            radarr_api_key=None,
            sonarr_api_key=None,
            prowlarr_api_key=None,
            seerr_api_key=None,
            bazarr_api_key=None,
            opensubtitles_username=None,
            opensubtitles_password=None,
        )

    def test_should_exit_with_code_two_when_a_required_variable_is_missing(self):
        with pytest.raises(SystemExit) as exit:
            EnvironmentService.from_env({"TIDE_JELLYFIN_API_KEY": "jellyfin-key", "TIDE_LAN_HOST": "192.168.1.10"})

        assert exit.value.code == 2

    def test_should_name_a_missing_qbittorrent_password(self, capsys):
        with pytest.raises(SystemExit):
            EnvironmentService.from_env({"TIDE_JELLYFIN_API_KEY": "jellyfin-key", "TIDE_LAN_HOST": "192.168.1.10"})

        assert "TIDE_QBIT_PASSWORD is not set (see tide/.env.example)" in capsys.readouterr().err

    def test_should_name_a_missing_jellyfin_api_key(self, capsys):
        with pytest.raises(SystemExit):
            EnvironmentService.from_env({"TIDE_QBIT_PASSWORD": "qbit-password", "TIDE_LAN_HOST": "192.168.1.10"})

        assert "TIDE_JELLYFIN_API_KEY is not set" in capsys.readouterr().err

    def test_should_name_a_missing_lan_host(self, capsys):
        with pytest.raises(SystemExit):
            EnvironmentService.from_env(
                {"TIDE_QBIT_PASSWORD": "qbit-password", "TIDE_JELLYFIN_API_KEY": "jellyfin-key"}
            )

        assert "TIDE_LAN_HOST is not set" in capsys.readouterr().err
