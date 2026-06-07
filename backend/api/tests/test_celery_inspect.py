from common.dependencies import get_celery_inspect_service
from fastapi.testclient import TestClient


def test_get_taskgroup_paused_returns_true(client: TestClient):
    get_celery_inspect_service().is_taskgroup_paused.return_value = True

    response = client.get("/v1/celery-inspect/task-groups/dispatch/paused")
    response.raise_for_status()

    assert response.json() is True
    get_celery_inspect_service().is_taskgroup_paused.assert_called_once_with("dispatch")


def test_set_taskgroup_paused_true(client: TestClient):
    inspect_mock = get_celery_inspect_service()

    response = client.put("/v1/celery-inspect/task-groups/dispatch/paused?paused=true")

    assert response.status_code == 204
    inspect_mock.set_taskgroup_paused.assert_called_once_with("dispatch", True)


def test_set_taskgroup_paused_false(client: TestClient):
    inspect_mock = get_celery_inspect_service()

    response = client.put("/v1/celery-inspect/task-groups/dispatch/paused?paused=false")

    assert response.status_code == 204
    inspect_mock.set_taskgroup_paused.assert_called_once_with("dispatch", False)


def test_get_task_paused_returns_true(client: TestClient):
    task_name = "worker.index_file.dispatch_tasks.dispatch_index_file"
    get_celery_inspect_service().is_task_paused.return_value = True

    response = client.get(f"/v1/celery-inspect/tasks/{task_name}/paused")
    response.raise_for_status()

    assert response.json() is True
    get_celery_inspect_service().is_task_paused.assert_called_once_with(task_name)


def test_get_task_paused_returns_false(client: TestClient):
    task_name = "worker.index_file.dispatch_tasks.dispatch_index_file"
    get_celery_inspect_service().is_task_paused.return_value = False

    response = client.get(f"/v1/celery-inspect/tasks/{task_name}/paused")
    response.raise_for_status()

    assert response.json() is False


def test_set_task_paused_true(client: TestClient):
    task_name = "worker.index_file.dispatch_tasks.dispatch_index_file"
    inspect_mock = get_celery_inspect_service()

    response = client.put(f"/v1/celery-inspect/tasks/{task_name}/paused?paused=true")

    assert response.status_code == 204
    inspect_mock.set_task_paused.assert_called_once_with(task_name, True)


def test_set_task_paused_false(client: TestClient):
    task_name = "worker.index_file.dispatch_tasks.dispatch_index_file"
    inspect_mock = get_celery_inspect_service()

    response = client.put(f"/v1/celery-inspect/tasks/{task_name}/paused?paused=false")

    assert response.status_code == 204
    inspect_mock.set_task_paused.assert_called_once_with(task_name, False)
