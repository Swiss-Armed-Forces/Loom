from common.dependencies import get_wipe_service
from fastapi.testclient import TestClient

from api.routers.wipe_data import WipeComponent


def test_wipe_all_no_components(client: TestClient):
    wipe_service_mock = get_wipe_service()
    response = client.post("/v1/wipe-data/", params={"confirmation": "wipe"})
    response.raise_for_status()
    for component in WipeComponent:
        getattr(wipe_service_mock, f"wipe_{component}").assert_called_once()


def test_wipe_selected_components(client: TestClient):
    wipe_service_mock = get_wipe_service()
    response = client.post(
        "/v1/wipe-data/",
        params={"confirmation": "wipe", "components": ["elasticsearch", "redis"]},
    )
    response.raise_for_status()
    wipe_service_mock.wipe_elasticsearch.assert_called_once()
    wipe_service_mock.wipe_redis.assert_called_once()
    for component in WipeComponent:
        if component not in (WipeComponent.ELASTICSEARCH, WipeComponent.REDIS):
            getattr(wipe_service_mock, f"wipe_{component}").assert_not_called()


def test_wrong_confirmation_returns_400(client: TestClient):
    wipe_service_mock = get_wipe_service()
    response = client.post("/v1/wipe-data/", params={"confirmation": "wrong"})
    assert response.status_code == 400
    for component in WipeComponent:
        getattr(wipe_service_mock, f"wipe_{component}").assert_not_called()


def test_empty_confirmation_returns_400(client: TestClient):
    wipe_service_mock = get_wipe_service()
    response = client.post("/v1/wipe-data/", params={"confirmation": ""})
    assert response.status_code == 400
    for component in WipeComponent:
        getattr(wipe_service_mock, f"wipe_{component}").assert_not_called()
