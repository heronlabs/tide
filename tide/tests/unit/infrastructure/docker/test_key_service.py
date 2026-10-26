from pathlib import Path

import pytest

from tide.infrastructure.docker.key_service import KeyService


# A docker command that answers one `docker exec` with the given output and fails any other call.
def docker(tmp_path: Path, arguments: str, output: str) -> str:
    command = tmp_path / "docker"
    command.write_text(
        f"#!/bin/sh\n"
        f'[ "$*" = "{arguments}" ] || {{ echo "Error: unexpected $*" >&2; exit 1; }}\n'
        f"cat <<'EOF'\n{output}\nEOF\n"
    )
    command.chmod(0o755)
    return str(command)


class TestGivenKey:
    def test_should_answer_the_key_given_in_the_environment(self, tmp_path):
        keys = KeyService({"radarr": "given-key"}, docker=str(tmp_path / "missing"))

        assert keys.key("radarr") == "given-key"

    def test_should_read_the_key_of_an_arr_from_its_config(self, tmp_path):
        command = docker(
            tmp_path,
            "exec radarr cat /config/config.xml",
            "<Config>\n  <Port>7878</Port>\n  <ApiKey>radarr-key</ApiKey>\n</Config>",
        )

        assert KeyService({"radarr": None}, docker=command).key("radarr") == "radarr-key"

    def test_should_fail_when_the_config_has_no_key(self, tmp_path):
        command = docker(tmp_path, "exec radarr cat /config/config.xml", "<Config><Port>7878</Port></Config>")

        with pytest.raises(OSError) as error:
            KeyService({}, docker=command).key("radarr")

        assert str(error.value) == "no ApiKey in the config of radarr"

    def test_should_read_the_key_of_seerr_from_its_settings(self, tmp_path):
        command = docker(tmp_path, "exec seerr cat /app/config/settings.json", '{"main": {"apiKey": "seerr-key"}}')

        assert KeyService({}, docker=command).key("seerr") == "seerr-key"

    def test_should_read_the_key_of_bazarr_from_its_auth_block(self, tmp_path):
        command = docker(
            tmp_path,
            "exec bazarr cat /config/config/config.yaml",
            "anidb:\n  api_client: ''\nauth:\n  password: ''\n  apikey: b513eb0f\njellyfin:\n  apikey: ''",
        )

        assert KeyService({}, docker=command).key("bazarr") == "b513eb0f"

    def test_should_read_the_key_of_bazarr_when_quoted(self, tmp_path):
        command = docker(tmp_path, "exec bazarr cat /config/config/config.yaml", "auth:\n  apikey: '0123'\n")

        assert KeyService({}, docker=command).key("bazarr") == "0123"

    def test_should_not_take_the_key_of_another_block_of_bazarr(self, tmp_path):
        command = docker(
            tmp_path,
            "exec bazarr cat /config/config/config.yaml",
            "auth:\n  password: ''\njellyfin:\n  apikey: jellyfin-key\n",
        )

        with pytest.raises(OSError) as error:
            KeyService({}, docker=command).key("bazarr")

        assert str(error.value) == "no apikey in the config of bazarr"

    def test_should_fail_with_what_docker_said(self, tmp_path):
        command = docker(tmp_path, "exec radarr cat /config/config.xml", "")

        with pytest.raises(OSError) as error:
            KeyService({}, docker=command).key("sonarr")

        assert str(error.value) == "docker exec sonarr: Error: unexpected exec sonarr cat /config/config.xml"

    def test_should_fail_without_docker(self, tmp_path):
        with pytest.raises(OSError):
            KeyService({}, docker=str(tmp_path / "missing")).key("radarr")
