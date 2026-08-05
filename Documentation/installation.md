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
      ./up.sh --gpus all
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

### Overriding Helm Values

To customize the deployment configuration, add your value
overrides to `charts/values-overwrites.yaml`. This file is intentionally left empty and
is automatically included during Skaffold deployments.

To deploy without resource requests or limits, pass `--no-resources` to `up.sh`.

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
- **[`values-gpu.yaml`](../charts/values-gpu.yaml)** — Use this when your nodes have NVIDIA GPUs
  and you want faster AI inference and translation. Without it, all AI workloads run on CPU only.
- **[`values-scaling.yaml`](../charts/values-scaling.yaml)** — Enable autoscaling (KEDA for
  queue-driven services, HPA for CPU/memory-driven services) and cluster-wide resource quotas.
  Use with `up --scaling` or pass via `--values` to Helm.
- **[`values-distribution.yaml`](../charts/values-distribution.yaml)** — Enable data replication
  and service redundancy across nodes: Elasticsearch shard replicas, SeaweedFS volume replication,
  and Prometheus cluster-metrics handoff to central monitoring infrastructure.
- **[`values-disable-ai-services.yaml`](../charts/values-disable-ai-services.yaml)** — Use this when
  you want to provide external AI endpoints or skip AI features entirely. Note: AI-powered indexing
  steps must also be disabled, otherwise they will fail at runtime.
- **[`values-external-tls-certificates.yaml`](../charts/values-external-tls-certificates.yaml)** —
  Use this when your cluster manages TLS certificates centrally via Vault and you do not
  want Loom to provision its own ClusterIssuer.
- **[`values-no-resources.yaml`](../charts/values-no-resources.yaml)** — Use this when resource
  requests are causing scheduling issues or limits are causing OOM kills or CPU throttling and you
  want containers to burst freely. Note that without requests, the Kubernetes scheduler has no
  resource information to base placement decisions on. Without limits, a single runaway container
  can starve other workloads on the same node.
- **[`values-development.yaml`](../charts/values-development.yaml)** — Use this when actively
  developing Loom locally. It trades model quality for fast iteration: lightweight models, hot
  reload, and all internal services exposed via ingress. Not suitable for production.

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
    llm__chat__api_key:
      enabled: true
      name: loom-llm-chat-api-key
      remoteRef:
        key: secret/loom/llm
        property: chat_api_key
```

When a secret is enabled, ESO creates a Kubernetes Secret named by `name` with the
environment-variable name as the data key. Loom pods automatically prefer such secrets over
the corresponding entry in the settings ConfigMap.

The full list of supported keys is documented in `charts/values.yaml` under
`externalSecrets.secrets`.

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
