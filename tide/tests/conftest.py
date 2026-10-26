from collections.abc import Callable, Iterator

import pytest
from mocks.http_server import FakeServer


@pytest.fixture
def fake_server():
    server = FakeServer()
    server.start()
    yield server
    server.stop()


# Starts a new FakeServer on each call, for a test that needs several services; all stop after the test.
@pytest.fixture
def fake_servers() -> Iterator[Callable[[], FakeServer]]:
    servers: list[FakeServer] = []

    def start() -> FakeServer:
        server = FakeServer()
        server.start()
        servers.append(server)
        return server

    yield start
    for server in servers:
        server.stop()
