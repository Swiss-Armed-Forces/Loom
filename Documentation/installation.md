# Installation

This page provides instructions for setting up Loom in a production-like environment.

[[_TOC_]]

## Dependencies

Before you begin, please ensure the following dependencies are installed on your system.
This will help make the setup process smooth and easy!

- `git`
- `git-lfs`
- `curl`
- `docker`
- `minikube` (>= [v1.33.1](https://minikube.sigs.k8s.io/docs/start/?arch=%2Flinux%2Fx86-64%2Fstable%2Fbinary+download))
- `helm` (>= [v3.14.0](https://helm.sh/docs/intro/install/))
- `kubectl` (>= [v1.30.0](https://kubernetes.io/de/docs/tasks/tools/install-kubectl/))
- `skaffold` (>= [v2.12.0](https://skaffold.dev/docs/install/))
- `yq` (>= [v3.0.0](https://github.com/kislyuk/yq#installation))
- `nvidia-smi` (for NVIDIA GPU users: part of NVIDIA CUDA toolkit)
- `rocm-smi-lib` (for AMD GPU users: `sudo apt install rocm-smi-lib`)

## System Requirements

Loom's resource profile spans two boundaries: what it needs to start, and what it could consume at
peak. Both matter depending on your deployment context.

### Minimum Deployment Resources

The minimum resources required to deploy and run Loom:

- **RAM:** 25Gi
- **CPU:** 8 Cores
- **Disk Space:** 200 GiB
- **GPU (Optional):** For enhanced performance with certain features, we recommend using at least 1 GPU(s).
  Please see the list of supported GPUs here: [https://docs.ollama.com/gpu](https://docs.ollama.com/gpu)

> ℹ️ The figures above are the resources Loom itself needs. `up.sh` additionally configures
> kubelet reservations (system-reserved, kube-reserved, eviction thresholds) on the minikube node,
> which are carved out of the host before Loom workloads are scheduled. The exact values are defined
> in `up.sh` and add several GiB of RAM and ephemeral storage overhead on top of Loom's own needs.
> If your machine is close to the minimum, pass `--no-resources` to `up.sh` to deploy without
> resource requests or limits and skip the host resource check.

### Maximum Resource Limits

The combined resource limits of all Loom containers — i.e., the maximum that could be consumed if
every container simultaneously hits its limit. In a cluster with
[Kubernetes ResourceQuotas](https://kubernetes.io/docs/concepts/policy/resource-quotas/#compute-resource-quota)
enforced, your namespace quota must be at least:

- **RAM:** 90Gi
- **CPU:** 66 Cores
- **Disk Space:** 200 GiB
- **GPU (Optional):** 1

For further scaling beyond a single node, see [Multi Node Deployment](#multi-node-deployment),
which supports enabling HPAs to scale services horizontally under load.

## Deployment Schemas

You have a couple of options for deploying Loom, depending on your needs:

- **Single Node Deployment:** This is a straightforward way to get Loom running on a single machine
  using the `up.sh` script. It's perfect for evaluation or smaller setups.
- **Multi Node Deployment:** For more extensive or production environments, you can deploy Loom
  on top of your existing Kubernetes cluster using our Helm chart.
- **Appliance Deployment:** A standalone, air-gapped box provisioned from a single USB stick. It
  serves its own network and resolves every `*.loom` name to itself, so a visitor plugs in a laptop
  and browses Loom with nothing to configure. See [Appliance Deployment](appliance.md).

## Single Node Deployment

This method is designed for simplicity and is a great starting point!

### Single Node Installation Steps

> ℹ️ Always install from the latest release tag. The `main` branch is for development only and may be unstable.

1. Clone the repository and check out the latest release:

    ```bash
    git clone https://gitlab.com/swiss-armed-forces/cyber-command/cea/loom.git
    cd loom
    git checkout tags/<tag-name>  # replace with the tag from the latest release
    ```

    Find the latest release tag on the [releases page](https://gitlab.com/swiss-armed-forces/cyber-command/cea/loom/-/releases/permalink/latest).

2. Run the setup script:
    - For a standard deployment (without GPU support):

      ```bash
      ./up.sh
      ```

    - If you have compatible GPUs and want to enable GPU support:

      ```bash
      ./up.sh --gpus nvidia    # For NVIDIA GPUs
      # or
      ./up.sh --gpus amd       # For AMD GPUs
      ```

> 💡 `up.sh` supports many more options (custom encryption keys, CA bundles, resource tuning,
> development mode, and more). Run `./up.sh --help` to see the full list.

After the up process is complete, you can open your web browser
and navigate to [https://frontend.loom](https://frontend.loom) to access Loom.

### Single Node Offline usage

If you want to use loom fully offline, you need to start Loom using `./up.sh --offline --delete`
at least once **while connected to the internet** before you can disconnect your host
and re-start Loom in full offline mode: `./up.sh --offline`.

> ⚠️ Offline mode only works when you have checked out a specific Git tag (not on a branch like `main`).
> If you followed the installation steps above, you are already on a release tag.

### Single Node Remote usage

If you want to access the loom UIs remotely, you need to start loom using `./up.sh --expose 0.0.0.0`.
Note that with IP 0.0.0.0 loom will listen on all available network interfaces. Replace 0.0.0.0 with an IP of a specific network interfaces to make loom listen only on that interface.

This flag runs `minikube tunnel`, which with the docker driver forwards each port over the system `ssh` client
rather than installing a route — so an `ssh` binary has to be on the `PATH`. Without one the tunnel starts,
logs `error starting ssh tunnel`, and binds nothing at all, which looks like a firewall problem rather than a
missing package.

On the remote machine you want to access loom from, you must make the `.loom` domain resolvable.
For example, via setting in `/etc/hosts`:

```bash
# Hosts for 'loom' domain
<serverip> frontend.loom
<serverip> api.loom
```

with `<serverip>` replaced with the IP of the machine running loom, and doing so for all loom services you require.

Note that the browser used to access loom running on the remote machine must support local domain resolution, under using `/etc/hosts` to define the `.loom` domain.

Some browsers allow to set directly host resolution rules via command line arguments, see for example `cicd/chrome_wrapped.sh` for chromium.

### Overriding Helm Values

To customize the deployment configuration, add your value
overrides to `charts/values-overwrites.yaml`. This file is intentionally left empty and
is automatically included during Skaffold deployments.

To deploy without resource requests or limits, pass `--no-resources` to `up.sh`. Elasticsearch and
Tika still bound their JVM heaps in that mode — without a limit to read they would size themselves
from the whole node — using the budget each declares as `memoryFallback` in `charts/values.yaml`.
Lower `elasticsearch.memoryFallback` or `tika.memoryFallback` in your overrides on a small machine.

## Multi Node Deployment

For a more scalable setup, you can deploy Loom using its Helm chart on your Kubernetes cluster.

> ⚠️ We currently only support Traefik as the ingress controller. We are tracking progress on
> integrating Nginx in issue #161.

### Multi Node Installation Steps

1. You can find and deploy the Helm chart from our official package registry:

    ```bash
    helm repo add loom-prod https://gitlab.com/api/v4/projects/68343701/packages/helm/prod
    ```

2. To customize your deployment, we provide a set of value files located in the
    [`./charts`](../charts) directory of this repository. These files document all the available
    deployment variables, allowing you to tailor the installation to your specific needs.

3. For a true multi-node setup, apply the scaling and distribution values files:

    ```bash
    helm install loom loom-prod/loom \
      --values charts/values-scaling.yaml \
      --values charts/values-distribution.yaml
    ```

    `values-scaling.yaml` enables autoscaling (KEDA/HPA) and resource quotas.
    `values-distribution.yaml` enables data replication and service redundancy across nodes.

### Multi Node Offline usage

To run Loom in an offline Kubernetes cluster, you need at least
one container image registry that mirrors `registry.gitlab.com/swiss-armed-forces/cyber-command/cea/loom`
within your offline network. Then, override the `image.registry` value in your
deployment scripts to point to your internal image registry.

## Helm Values Reference

All values files are located in the [`./charts`](../charts) directory. They can be combined with
`--values` (Helm) or added to `charts/values-overwrites.yaml` (Skaffold) to tailor your deployment.

- **[`values-overwrites.yaml`](../charts/values-overwrites.yaml)** — Your personal override file.
  Skaffold picks it up automatically on every deploy, so put any local customisations here rather
  than editing the defaults.
- **[`values-nvidia-gpu.yaml`](../charts/values-nvidia-gpu.yaml)** — Use this when your nodes have NVIDIA GPUs
  and you want faster AI inference and translation. Without it, all AI workloads run on CPU only.
- **[`values-amd-gpu.yaml`](../charts/values-amd-gpu.yaml)** — Use this when your nodes have AMD
  GPUs (ROCm) and you want faster AI inference and translation. Model images are GPU-agnostic and
  work with both NVIDIA and AMD runtime images.
- **[`values-scaling.yaml`](../charts/values-scaling.yaml)** — Enable autoscaling (KEDA for
  queue-driven services, HPA for CPU/memory-driven services) and cluster-wide resource quotas.
  Use with `up --scaling` or pass via `--values` to Helm.
- **[`values-distribution.yaml`](../charts/values-distribution.yaml)** — Enable data replication
  and service redundancy across nodes: Elasticsearch shard replicas, SeaweedFS volume replication,
  and Prometheus cluster-metrics handoff to central monitoring infrastructure.
- **[`values-disable-ai-services.yaml`](../charts/values-disable-ai-services.yaml)** — Use this when
  you want to provide external AI endpoints or skip AI features entirely. It also skips the
  AI-powered indexing steps (embedding, auto-tagging), so nothing retries against an Ollama that is
  not deployed.
- **[`values-external-tls-certificates.yaml`](../charts/values-external-tls-certificates.yaml)** —
  Use this when your cluster manages TLS certificates centrally via Vault and you do not
  want Loom to provision its own ClusterIssuer.
- **[`values-no-resources.yaml`](../charts/values-no-resources.yaml)** — Use this when resource
  requests are causing scheduling issues or limits are causing OOM kills or CPU throttling and you
  want containers to burst freely. Note that without requests, the Kubernetes scheduler has no
  resource information to base placement decisions on. Without limits, a single runaway container
  can starve other workloads on the same node. Elasticsearch and Tika are the exception: their
  heaps stay bounded by the `memoryFallback` budget each declares in `charts/values.yaml`.
- **[`values-development.yaml`](../charts/values-development.yaml)** — Use this when actively
  developing Loom locally. It trades model quality for fast iteration: lightweight models, hot
  reload, and all internal services exposed via ingress. Not suitable for production.

### Hostnames and the self-signed certificate

Loom serves every service under one domain (`domain`, `loom` by default), and `hostnames` in
`charts/values.yaml` lists every name it answers to — `ingress` for the services behind a route that
names them, `extra` for the ones Traefik tells apart by entrypoint:

```yaml
domain: loom

hostnames:
  ingress:
    - api
    - frontend
    # ...
  extra:
    - rabbit-amqp
    # ...
```

Three things are built from that list: the self-signed certificate, which has to name each host individually
(a `*.loom` wildcard is compared literally by OpenSSL and everything built on it, so it covers nothing), the
`dnsNames` of the cert-manager `Certificate` used when `certificate.enabled` is set, and the `/etc/hosts`
entries `up.sh` writes. **If you add your own Ingress to this chart, add its host here** — otherwise clients
get a hostname mismatch on it.

Overrides reach some of those and not others, and the gap is silent either way:

- A `domain` overridden in `values-overwrites.yaml` reaches the chart but not `/etc/hosts`, and not the
  Traefik dashboard route either — `traefik/values.yaml` hardcodes `Host("traefik.loom")`.
- `hostnames` overridden the same way reaches the certificate Job, but not `/etc/hosts` and not the
  `hostnames.ingress` check `cicd/check_chart_hostnames.sh` runs — both read `charts/values.yaml` directly.

A certificate you installed yourself, including via `up.sh --certificate`, is never replaced.

Nothing issues the generated certificate, so a client that trusts it trusts it as a root rather than
following a chain to one — the appliance's assistant pane and its USB ingest both do exactly that. A root has
to be allowed to have signed something, so the certificate carries **no `keyUsage`** at all, and the
cert-manager `Certificate` used when `certificate.enabled` is set names `cert sign` among its `usages`,
because cert-manager always emits a `keyUsage` extension and defaults it to one that disqualifies the
certificate. Without that, OpenSSL-based clients (`curl`, Python) and Go accept the certificate while
BoringSSL-based ones reject it with "unable to verify the first certificate" — so the breakage shows up in
one client and nowhere else.

### Crawling external S3 sources

By default Loom deploys a single S3 crawler that watches the internal SeaweedFS intake bucket.
You can add any number of additional crawlers that watch external S3-compatible endpoints by
listing them in `extraS3Sources`. Each entry spawns a dedicated crawler `Deployment` rendered
from the same Helm template as the built-in crawler.

> ⚠️ External S3 endpoints are outside the cluster. Set `egress.enabled=true` in your values
> override to allow the crawler pods to open outbound connections to them. Without it, the
> network policy blocks all external egress.

**With plain credentials:**

```yaml
egress:
  enabled: true

extraS3Sources:
  - name: archive-server          # unique identifier; used in the Deployment name
    s3Storage:
      host: minio.example.com:9000  # host[:port] of the external S3 endpoint
      bucketName: my-bucket
      accessKey: my-access-key
      secretKey: my-secret-key
      secureConnection: false       # set to true for HTTPS
    bucketAlias: "Archive Bucket"  # optional display name shown in file paths
    sourceId: archive-server       # optional source identifier, defaults to name
```

**With ESO-managed credentials** (credentials stored in a K8s Secret, e.g. via External Secrets
Operator — see [External Secrets Operator](#external-secrets-operator-eso)):

```yaml
extraS3Sources:
  - name: vault-managed-source
    s3Storage:
      host: minio.example.com:9000
      bucketName: my-bucket
      accessKeySecretRef:         # references a K8s Secret by name + key
        name: my-s3-credentials
        key: access_key
      secretKeySecretRef:
        name: my-s3-credentials
        key: secret_key
```

Multiple sources can be listed under `extraS3Sources`. Each produces an independent crawler
pod with its own intake storage credentials, so buckets on different servers or with different
credentials are all supported simultaneously.

### External Secrets Operator (ESO)

Loom supports [External Secrets Operator](https://external-secrets.io/) to pull sensitive
configuration from an external secret store (Vault, AWS Secrets Manager, Azure Key Vault, etc.)
instead of inlining secrets in Helm values or Kubernetes manifests.

> ℹ️ ESO itself must be installed in your cluster separately. Loom only ships the `ExternalSecret`
> resources; it does not deploy the ESO operator.

#### Shared store reference

All `ExternalSecret` resources created by the chart share one `SecretStore` (or
`ClusterSecretStore`) reference. Configure it once in your values override:

```yaml
externalSecrets:
  secretStoreRef:
    name: my-vault-store   # name of the SecretStore / ClusterSecretStore in your cluster
    kind: SecretStore      # or ClusterSecretStore
  refreshInterval: "1h"   # how often ESO re-reads from the store
```

#### Application credentials

Individual application settings (S3 credentials, LLM API keys, etc.) can each be sourced from
the external store instead of the settings ConfigMap. Every entry in `externalSecrets.secrets`
maps an environment-variable name to a path in the secret store:

```yaml
externalSecrets:
  secrets:
    # SeaweedFS / S3 credentials
    file_storage__access_key:
      enabled: true
      name: loom-file-storage-access-key
      remoteRef:
        key: secret/loom/s3
        property: access_key
    file_storage__secret_key:
      enabled: true
      name: loom-file-storage-secret-key
      remoteRef:
        key: secret/loom/s3
        property: secret_key

    # External LLM API key
    llm__rag_synthesize__api_key:
      enabled: true
      name: loom-llm-synthesize-api-key
      remoteRef:
        key: secret/loom/llm
        property: chat_api_key
```

When a secret is enabled, ESO creates a Kubernetes Secret named by `name` with the
environment-variable name as the data key. Loom pods automatically prefer such secrets over
the corresponding entry in the settings ConfigMap.

The full list of supported keys is documented in `charts/values.yaml` under
`externalSecrets.secrets`.

### Ollama GPU Configuration

Ollama runs on the CPU unless you tell it otherwise. With `up.sh` there is nothing to configure —
`--gpus nvidia` or `--gpus amd` applies the right values file, enables the matching device plugin
and checks the host for you.

Deploying the chart directly, set three things: the GPU vendor, the Ollama image for it, and the
resource key its device plugin advertises. Your cluster needs that device plugin already installed.

```yaml
# NVIDIA GPUs -- charts/values-nvidia-gpu.yaml
ollama:
  gpuVendor: nvidia
  runtimeImage:
    repository: swiss-armed-forces/cyber-command/cea/loom/ollama-runtime-nvidia
  resources:
    requests:
      nvidia.com/gpu: 1
    limits:
      nvidia.com/gpu: 1

# AMD GPUs (ROCm) -- charts/values-amd-gpu.yaml
ollama:
  gpuVendor: amd
  runtimeImage:
    repository: swiss-armed-forces/cyber-command/cea/loom/ollama-runtime-rocm
  resources:
    requests:
      amd.com/gpu: 1
    limits:
      amd.com/gpu: 1
```

`gpuVendor` reaches the container as `LOOM_GPU_VENDOR` and does two jobs. It picks how the
container reads the GPU's memory — `nvidia-smi` for NVIDIA, amdgpu's sysfs attributes for AMD,
since the ROCm image carries no `rocm-smi` — and it makes a pod that was deployed as a GPU
workload **refuse to start** when the device never arrived, rather than quietly falling back to
the CPU. If the pod logs `LOOM_GPU_VENDOR=... but /dev/... is absent` and exits, the device plugin
is missing or the wrong values file was applied. Leave `gpuVendor` empty and the container
autodetects instead, with a silent CPU fallback.

What it reads the memory _for_ is `OLLAMA_NUM_PARALLEL`, which Ollama defaults to 1 and which
multiplies the context to give the KV cache — so the container sizes it against the memory it can
actually see. Set `OLLAMA_NUM_PARALLEL` in the environment yourself and it is honoured untouched.

Do not size a GPU node for that concurrency, though: on the two models the production image
carries, Ollama's scheduler forces a single slot whatever this variable says — an embedding model
has no completion capability, and the chat model's architecture is on the server's no-parallel
list. The value computed here only buys anything for a model whose architecture supports batching.
See [**Raising `OLLAMA_NUM_PARALLEL` is not the other option**](ai.md#thinking) in `ai.md` for what
the real options are.
`OLLAMA_CONTEXT_LENGTH` is deliberately left alone: Ollama sizes the context from its own VRAM
measurement and will walk it back down if a load fails, and setting the variable turns that off.

Models are shipped in a separate image from the Ollama runtime and copied into Ollama's storage
when the pod starts, so switching between CPU, NVIDIA and AMD never re-downloads them. Keep
`ollama.pvc.enabled: true` (the default) and that copy happens once — with it off, every pod
restart repeats it.

## Troubleshooting

This section covers known issues and their solutions. If you encounter a problem not listed here,
check the pod logs with `kubectl logs -n loom <pod-name>` or open an issue on the
[issue tracker](https://gitlab.com/swiss-armed-forces/cyber-command/cea/loom/-/issues).

### KEDA DNS resolution

The KEDA autoscaler metrics-server requires DNS resolution to the keda-operator in the cluster.local domain.
In some unfortunate setups this may not work properly as the request may be forwarded and resolved upstream
before the keda-operator is registered in local DNS. If this occurs in your setup, one possible solution
would be to switch off fallthrough for cluster.local domains by changing the corresponding CoreDNS
configuration via

```bash
kubectl edit configmap coredns -n kube-system
```

followed by restarting CoreDNS

```bash
kubectl rollout restart deployment coredns -n kube-system
```
