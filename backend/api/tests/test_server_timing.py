import re

from fastapi.testclient import TestClient

from api.server_timing import SERVER_TIMING_HEADER

# e.g. 'total;dur=12.3;desc="/v1/queues/{queue_name}/message_count"'
_SERVER_TIMING = re.compile(r'^total;dur=(?P<ms>\d+\.\d);desc="(?P<route>[^"]+)"$')


def test_reports_how_long_the_api_took_under_the_route_template(
    client: TestClient,
):
    """The template, not the path: one entry per endpoint, not per file id."""
    response = client.get("/v1/queues/some-queue/message_count")

    match = _SERVER_TIMING.match(response.headers[SERVER_TIMING_HEADER])
    assert match is not None
    assert match.group("route") == "/v1/queues/{queue_name}/message_count"
    assert float(match.group("ms")) >= 0


def test_is_set_on_a_failed_request_too(client: TestClient):
    """The slow ones are often the ones that fail, so they need timing most."""
    response = client.get("/v1/does-not-exist")

    assert response.status_code == 404
    assert SERVER_TIMING_HEADER in response.headers
