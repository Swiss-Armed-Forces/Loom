from unittest.mock import MagicMock, patch

from fastapi.testclient import TestClient


def _make_mock_repo_type(index_name: str, backup_index_name: str):
    mock_repo = MagicMock()
    mock_repo.index_name = index_name
    mock_repo.reinit.return_value = backup_index_name

    mock_repo_type = MagicMock(return_value=mock_repo)
    mock_repo_type.__name__ = "MockRepo"
    return mock_repo_type, mock_repo


def test_reinit_all_elasticsearch(client: TestClient):
    mock_repo_type, mock_repo = _make_mock_repo_type("test-index", "test-index-backup")

    with patch("api.routers.init_elasticsearch.ES_REPOSITORY_TYPES", [mock_repo_type]):
        response = client.post("/v1/init/elasticsearch")

    response.raise_for_status()
    assert response.json() == {
        "results": [{"index": "test-index", "backup_index": "test-index-backup"}]
    }
    mock_repo.reinit.assert_called_once()


def test_reinit_all_elasticsearch_multiple_repos(client: TestClient):
    mock_repo_type_a, mock_repo_a = _make_mock_repo_type("index-a", "index-a-backup")
    mock_repo_type_b, mock_repo_b = _make_mock_repo_type("index-b", "index-b-backup")

    with patch(
        "api.routers.init_elasticsearch.ES_REPOSITORY_TYPES",
        [mock_repo_type_a, mock_repo_type_b],
    ):
        response = client.post("/v1/init/elasticsearch")

    response.raise_for_status()
    assert response.json() == {
        "results": [
            {"index": "index-a", "backup_index": "index-a-backup"},
            {"index": "index-b", "backup_index": "index-b-backup"},
        ]
    }
    mock_repo_a.reinit.assert_called_once()
    mock_repo_b.reinit.assert_called_once()


def test_reinit_elasticsearch_index(client: TestClient):
    mock_repo_type, mock_repo = _make_mock_repo_type("test-index", "test-index-backup")

    with patch("api.routers.init_elasticsearch.ES_REPOSITORY_TYPES", [mock_repo_type]):
        response = client.post("/v1/init/elasticsearch/test-index")

    response.raise_for_status()
    assert response.json() == {
        "index": "test-index",
        "backup_index": "test-index-backup",
    }
    mock_repo.reinit.assert_called_once()


def test_reinit_elasticsearch_index_only_reinits_matching_repo(client: TestClient):
    mock_repo_type_a, mock_repo_a = _make_mock_repo_type("index-a", "index-a-backup")
    mock_repo_type_b, mock_repo_b = _make_mock_repo_type("index-b", "index-b-backup")

    with patch(
        "api.routers.init_elasticsearch.ES_REPOSITORY_TYPES",
        [mock_repo_type_a, mock_repo_type_b],
    ):
        response = client.post("/v1/init/elasticsearch/index-a")

    response.raise_for_status()
    mock_repo_a.reinit.assert_called_once()
    mock_repo_b.reinit.assert_not_called()


def test_reinit_elasticsearch_index_not_found(client: TestClient):
    mock_repo_type, mock_repo = _make_mock_repo_type("test-index", "test-index-backup")

    with patch("api.routers.init_elasticsearch.ES_REPOSITORY_TYPES", [mock_repo_type]):
        response = client.post("/v1/init/elasticsearch/non-existent-index")

    assert response.status_code == 404
    mock_repo.reinit.assert_not_called()
