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

## System Requirements

Loom's resource profile spans two boundaries: what it needs to start, and what it could consume at
peak. Both matter depending on your deployment context.

### Minimum Deployment Resources

The minimum resources required to deploy and run Loom:

- **RAM:** 25Gi
- **CPU:** 8 Cores
- **Disk Space:** 200 GiB
- **GPU (Optional):** For enhanced performance with certain features, we recommend using at least 3 GPUs.
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
- **GPU (Optional):** 3

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

3. For a true multi-node setup, apply `charts/values-multinode.yaml` as an additional values file:

    ```bash
    helm install loom loom-prod/loom --values charts/values-multinode.yaml
    ```

    This enables horizontal scaling, high availability, and resource quotas suited for multi-node clusters.

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
- **[`values-multinode.yaml`](../charts/values-multinode.yaml)** — Use this when deploying across
  multiple nodes and you need services to scale out under load, storage and search to remain
  available if a node goes down, and resource usage to stay within defined cluster boundaries.
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
