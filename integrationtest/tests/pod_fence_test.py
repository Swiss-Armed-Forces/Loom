import pytest
from kubernetes import client, config
from kubernetes.stream import stream

NOT_FENCED_PODS = ("worker",)
PARTIAL_FENCED_PODS = ("gotenberg",)
FENCED_PODS = ("tika",)
ALL_PODS = NOT_FENCED_PODS + PARTIAL_FENCED_PODS + FENCED_PODS
# Note: Raw IPs should be included in EXTERNAL_HOSTS to test if not only DNS resolve is blocked
EXTERNAL_HOSTS = (
    "www.google.com",
    "www.admin.ch",
    "1.1.1.1",
)
INTERNAL_HOSTS = ("frontend",)


@pytest.fixture(autouse=True, scope="function", name="kub")
def init_kubernetes_client():
    config.load_kube_config()
    kv1 = client.CoreV1Api()
    return kv1


def get_pod_name(kub: client.api.core_v1_api.CoreV1Api, name: str) -> str | None:
    pods = kub.list_pod_for_all_namespaces(watch=False)
    for i in pods.items:
        if i.metadata.namespace == "loom":
            nparts = i.metadata.name.split("-")
            if len(nparts) >= 3 and nparts[2] == name:
                return i.metadata.name

    return None


def get_pod_ip(kub: client.api.core_v1_api.CoreV1Api, name: str) -> str | None:
    pods = kub.list_pod_for_all_namespaces(watch=False)
    for i in pods.items:
        if i.metadata.namespace == "loom":
            nparts = i.metadata.name.split("-")
            if len(nparts) >= 3 and nparts[2] == name:
                return i.status.pod_ip

    return None


def exec_curl(
    kub: client.api.core_v1_api.CoreV1Api, pod: str | None, host: str | None
) -> int:
    assert pod is not None
    assert host is not None

    response = stream(
        kub.connect_get_namespaced_pod_exec,
        name=pod,
        namespace="loom",
        command=["curl", host, "--max-time", "5"],
        stderr=True,
        stdin=False,
        stdout=True,
        tty=False,
        _preload_content=False,
    )

    response.run_forever(timeout=10)

    assert response.returncode is not None

    return response.returncode


@pytest.mark.parametrize(
    "pod,host", [(pod, host) for pod in ALL_PODS for host in EXTERNAL_HOSTS]
)
def test_external_connection_block(
    kub: client.api.core_v1_api.CoreV1Api, pod: str, host: str
):
    response = exec_curl(kub, get_pod_name(kub, pod), host)

    # Curl 28 error code: Timeout
    assert response == 28


@pytest.mark.parametrize(
    "pod,host",
    [
        (pod, host)
        for pod in FENCED_PODS + PARTIAL_FENCED_PODS
        for host in INTERNAL_HOSTS
    ],
)
def test_internal_connection_block(
    kub: client.api.core_v1_api.CoreV1Api, pod: str, host: str
):
    response = exec_curl(kub, get_pod_name(kub, pod), get_pod_ip(kub, host))

    # Curl 28 error code: Timeout
    assert response == 28


@pytest.mark.parametrize("pod", list(PARTIAL_FENCED_PODS))
def test_roundcube_connection_open(kub: client.api.core_v1_api.CoreV1Api, pod: str):
    response = exec_curl(kub, get_pod_name(kub, pod), get_pod_ip(kub, "roundcube"))

    # Curl 0 error code: OK
    assert response == 0


@pytest.mark.parametrize(
    "pod,host", [(pod, host) for pod in NOT_FENCED_PODS for host in INTERNAL_HOSTS]
)
def test_internal_connection_open(
    kub: client.api.core_v1_api.CoreV1Api, pod: str, host: str
):
    response = exec_curl(kub, get_pod_name(kub, pod), get_pod_ip(kub, host))

    # Curl 0 error code: OK
    assert response == 0
