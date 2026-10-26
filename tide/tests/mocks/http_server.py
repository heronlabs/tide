import threading
import time
from dataclasses import dataclass, field
from http.server import BaseHTTPRequestHandler, ThreadingHTTPServer
from urllib.parse import urlsplit


@dataclass(frozen=True)
class Request:
    method: str
    path: str
    query: str
    headers: dict[str, str]
    body: str


@dataclass(frozen=True)
class Response:
    status: int = 200
    body: str = ""
    headers: dict[str, str] = field(default_factory=dict)
    delay: float = 0


# Real HTTP server on localhost: routes are (method, path) -> Response, every request is recorded.
class FakeServer:
    def __init__(self) -> None:
        self.routes: dict[tuple[str, str], Response] = {}
        self.requests: list[Request] = []
        self._server = ThreadingHTTPServer(("127.0.0.1", 0), self._handler())

    @property
    def url(self) -> str:
        host, port = self._server.server_address[:2]
        return f"http://{host}:{port}"

    def requests_to(self, path: str) -> list[Request]:
        return [request for request in self.requests if request.path == path]

    def _handler(self) -> type[BaseHTTPRequestHandler]:
        server = self

        class Handler(BaseHTTPRequestHandler):
            def do_GET(self) -> None:
                self._serve()

            def do_POST(self) -> None:
                self._serve()

            def do_PUT(self) -> None:
                self._serve()

            def _serve(self) -> None:
                url = urlsplit(self.path)
                length = int(self.headers.get("Content-Length", 0))
                server.requests.append(
                    Request(self.command, url.path, url.query, dict(self.headers), self.rfile.read(length).decode())
                )
                response = server.routes.get((self.command, url.path), Response(status=404))
                time.sleep(response.delay)
                self.send_response(response.status)
                for name, value in response.headers.items():
                    self.send_header(name, value)
                self.send_header("Content-Length", str(len(response.body.encode())))
                self.end_headers()
                self.wfile.write(response.body.encode())

            def log_message(self, format: str, *args: object) -> None:
                pass

        return Handler

    def start(self) -> None:
        threading.Thread(target=self._server.serve_forever, kwargs={"poll_interval": 0.01}, daemon=True).start()

    def stop(self) -> None:
        self._server.shutdown()
        self._server.server_close()
