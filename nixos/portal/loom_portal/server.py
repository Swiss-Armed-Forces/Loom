"""The socket, and nothing else.

The only module here that knows what a port is. It converts what
`BaseHTTPRequestHandler` hands it into a `Request`, asks `Portal.handle` for a
`Response` and writes it back out -- so everything worth testing lives on the other side
of that call and the suite never binds anything. Same boundary `loom_ready` draws at
`Commands.run`.

Threaded, because a request that is waiting for the root issuer blocks for seconds and a
second visitor must not be made to queue behind it. `daemon_threads`, so a `systemctl
stop` does not hang on a wait that nobody is reading any more.
"""

import logging
from http.server import BaseHTTPRequestHandler, ThreadingHTTPServer

from loom_portal.http import Header, Request
from loom_portal.portal import Portal
from loom_portal.settings import PortalSettings

logger = logging.getLogger(__name__)

# Bodies this service accepts. nginx caps the same route at 4k; this is the half that
# applies to anything dialling the loopback port directly.
MAX_BODY_BYTES = 64 * 1024


def serve(portal: Portal, settings: PortalSettings) -> None:
    """Run until the process is stopped."""

    class Handler(BaseHTTPRequestHandler):
        # The version nginx is talking to, so keep-alive and chunked responses work.
        protocol_version = "HTTP/1.1"
        server_version = "loom-portal"
        # Suppress the stock `Python/3.x` banner. There is nothing to gain from telling
        # a visitor which interpreter is behind the proxy.
        sys_version = ""
        # Restated from BaseHTTPRequestHandler, which only ever sets it from inside
        # `handle_one_request`. `_body` writes to it to drop a connection it refused to
        # drain, and declaring it here is what makes that an assignment to a field of
        # this class rather than one invented at runtime. The value below is never the
        # one in force: the base class sets it per request before anything here runs.
        close_connection = False

        def _get(self) -> None:
            self._answer("GET")

        def _head(self) -> None:
            self._answer("HEAD")

        def _post(self) -> None:
            self._answer("POST")

        # `BaseHTTPRequestHandler.handle_one_request` dispatches on
        # `getattr(self, "do_" + self.command)`, so the names have to be these. Bound as
        # class attributes rather than written as `def do_GET`, so the three methods
        # above keep the repository's naming and nothing here needs a lint exemption.
        do_GET = _get
        do_HEAD = _head
        do_POST = _post

        def _answer(self, method: str) -> None:
            path, _, query = self.path.partition("?")
            response = portal.handle(
                Request(
                    method=method,
                    path=path,
                    query=query,
                    body=self._body(),
                    headers=[
                        Header(name, value) for name, value in self.headers.items()
                    ],
                )
            )

            self.send_response(response.status)
            seen_length = False
            for header in response.headers:
                if header.name.lower() == "content-length":
                    seen_length = True
                self.send_header(header.name, header.value)
            if not seen_length:
                self.send_header("Content-Length", str(len(response.body)))
            # Set when `_body` refused to read a body it was told was there. Saying so
            # is the difference between a client that moves on and one that waits out
            # a keep-alive that is not coming.
            if self.close_connection:
                self.send_header("Connection", "close")
            self.end_headers()

            # A HEAD carries the headers and no body, which is what some captive-portal
            # probes send.
            if method != "HEAD":
                self.wfile.write(response.body)

        def _body(self) -> bytes:
            """The request body, or nothing -- but never a half-read socket.

            `protocol_version` is HTTP/1.1, so the connection stays open after the
            response. Declining a body without taking it off the socket leaves those
            bytes to be parsed as the next request line, which desynchronises the
            connection: one POST with an oversized Content-Length then yields a 400 on
            garbage, or, with a crafted body, a second request of the client's
            choosing. Today nginx caps this route at 4k and proxies as HTTP/1.0, so
            only something dialling the loopback port directly can reach it -- one
            nginx-config change away from mattering.
            """
            try:
                length = int(self.headers.get("Content-Length", "0"))
            except ValueError:
                self.close_connection = True
                return b""
            if length <= 0:
                return b""
            if length > MAX_BODY_BYTES:
                self.close_connection = True
                return b""
            return self.rfile.read(length)

        def address_string(self) -> str:
            """What every logged line is prefixed with.

            Replaced rather than written. The appliance keeps no record of who used it,
            and this is the one process a visitor talks to -- so the one identifying
            thing `log_message` would print is taken out at the source, which is a
            smaller change than reimplementing the logging. Upstream's `log_message`
            then writes to stderr, and systemd puts that in the journal.

            It is also the address of nginx on loopback rather than of the visitor,
            since every request arrives through the proxy, so it was never worth
            printing in the first place.
            """
            return "-"

    httpd = ThreadingHTTPServer((settings.listen_address, settings.port), Handler)
    httpd.daemon_threads = True
    logger.info(
        "Serving the appliance page on %s:%d", settings.listen_address, settings.port
    )
    httpd.serve_forever()
