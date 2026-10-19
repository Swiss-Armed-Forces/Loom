"""Server-Timing header for API responses.

Reports how long the API spent on a request, under the route that served it, so a slow
page of search results can be attributed to a specific endpoint from the browser's
network panel instead of being timed by hand. The header is read by devtools directly
and costs one monotonic clock read per request.
"""

import time
from collections.abc import Awaitable, Callable

from fastapi import FastAPI, Request, Response

SERVER_TIMING_HEADER = "Server-Timing"

# Metric names may not contain spaces or semicolons; the route template is used
# as the description instead, which devtools shows beside the duration.
_TOTAL_METRIC = "total"


def _route_description(request: Request) -> str:
    """The request path with its parameters put back as placeholders.

    Built from the request path rather than read off the matched route, whose `path` is
    relative to the router it was declared in and so loses the prefix `include_router`
    mounted it under. Substituting the values keeps one entry per endpoint instead of
    one per file id.
    """
    path = request.url.path
    for name, value in (request.scope.get("path_params") or {}).items():
        path = path.replace(str(value), "{" + name + "}", 1)
    return path


def init_server_timing(api: FastAPI) -> None:
    @api.middleware("http")
    async def add_server_timing(
        request: Request,
        call_next: Callable[[Request], Awaitable[Response]],
    ) -> Response:
        started = time.perf_counter()
        response = await call_next(request)
        elapsed_ms = (time.perf_counter() - started) * 1000

        # The route is only resolved once the request has been routed, so it is
        # read after the handler rather than before it.
        response.headers[SERVER_TIMING_HEADER] = (
            f'{_TOTAL_METRIC};dur={elapsed_ms:.1f};desc="{_route_description(request)}"'
        )
        return response
