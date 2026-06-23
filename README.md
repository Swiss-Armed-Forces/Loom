# ![Loom Logo](Frontend/src/features/common/branding/loom-logo-full-contour.svg) Document Search Engine

[![License: MIT](badge-mit-blue.svg)](LICENSE.txt)
[![Release Status](https://gitlab.com/swiss-armed-forces/cyber-command/cea/loom/-/badges/release.svg)](https://gitlab.com/swiss-armed-forces/cyber-command/cea/loom/-/releases)
[![GitLab Pipeline Status](https://gitlab.com/swiss-armed-forces/cyber-command/cea/loom/badges/main/pipeline.svg)](https://gitlab.com/swiss-armed-forces/cyber-command/cea/loom/-/pipelines?page=1&scope=all&ref=main)
[![Contributor Covenant](https://img.shields.io/badge/Contributor%20Covenant-v2.1%20adopted-ff69b4.svg)](https://www.contributor-covenant.org/version/2/1/code_of_conduct/)

**Loom** is a powerful, easily deployable open-source document search engine designed for
secure, task-specific deployments. It automates indexing of data sources, performs OCR,
extracts content and metadata, and enables powerful full-text search — enriched by AI features
such as RAG chat, auto-tagging, summarization, and translation.

[[_TOC_]]

## ✨ Key Features

- **🚀 Simple Deployment:** Get up and running quickly with asingle `up.sh` script.
- **🔍 Powerful Search:** Experience Google-like search across your documents and
  image content with a rich set of syntax options.
- **⚙️ Automatic Indexing:** Loom automatically monitors configured data sources
  and processes new and updated files.
- **📤 Flexible Data Ingestion:** Easily index data by uploading files directly through
  the simple file upload provided in the Loom frontend.
- **📚 Comprehensive Content Extraction:** Handles a vast array of file formats,
  including Office documents, PDFs, emails, archives, images, and more. Features robust
  OCR and efficient processing of large files.
- **🏷️ Metadata Extraction:** Automatically identifies and extracts relevant metadata
  from all supported file types during the indexing process.
- **🤖 AI Features:** Loom integrates AI throughout — chat with your documents via a
  RAG chatbot, automatically tag new documents based on existing tags, and get
  AI-generated summaries and image descriptions.
- **📦 Archive Creation:** Easily bundle selected search results or individual documents
  into archives for convenient data extraction and transfer.
- **📌 Tagging:** Organize and categorize your document collection with custom, user-defined tags.
- **🌍 Translation:** Built-in functionality to translate content from various languages
  into English.
- **🖼️ Secure Document Rendering:** View sanitized, rendered versions of documents and
  auto-generated thumbnails directly in the UI — without exposing the original file to the browser.
- **🔗 REST API:** Seamlessly integrate Loom's powerful search and other functionalities
  into your existing applications and workflows through our comprehensive REST API.

## 🚫 Limitations and Out-of-Scope Features

Loom is built as a modular and extensible toolkit for document indexing and search-fast to deploy,
easy to adapt, and intended for secure, task-specific use. However, it makes a number of deliberate
trade-offs in scope and design. The following points clarify what Loom is not intended to support:

- **🔄🚫 No upgrade path guarantees:** Loom is designed for ephemeral usage. You are expected to deploy
  a fresh instance, index a dataset, analyze the results, and shut it down. There is no support for
  migrating data or state across versions or long-running deployments.
- **🧑‍🚫 No user management:** Loom does not provide authentication, authorization, or role separation.
  All users accessing an instance are considered fully trusted. If isolation is needed, you must run
  separate Loom instances.
- **🌐🚫 Not suitable for public exposure:** Loom is not hardened for internet-facing use. It assumes a
  trusted environment and lacks defenses against malicious input. Exposing it without strict external
  protection (e.g., VPN, proxy authentication) carries significant security risks.
- **🧰🚫 Not a general-purpose SaaS product:** Loom is not a polished, multi-tenant solution. It’s a
  low-friction framework for building document analysis systems, meant to be shaped to your domain;
  not a turnkey platform for general use.

These boundaries reflect Loom’s focus on flexibility, transparency, and local control. Ideal for internal
deployments and exploratory workflows, but not for unmanaged or large-scale public scenarios.

## 🛠️ Installation

This section provides instructions for setting up Loom in a production-like environment.

### Dependencies

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

### System Requirements

Loom's resource profile spans two boundaries: what it needs to start, and what it could consume at
peak. Both matter depending on your deployment context.

#### Minimum Deployment Resources

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

#### Maximum Resource Limits

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

### Deployment Schemas

You have a couple of options for deploying Loom, depending on your needs:

- **Single Node Deployment:** This is a straightforward way to get Loom running on a single machine
  using the `up.sh` script. It's perfect for evaluation or smaller setups.
- **Multi Node Deployment:** For more extensive or production environments, you can deploy Loom
  on top of your existing Kubernetes cluster using our Helm chart.

### Single Node Deployment

This method is designed for simplicity and is a great starting point!

#### Single Node Installation Steps

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

After the up process is complete, you can open your web browser
and navigate to [https://frontend.loom](https://frontend.loom) to access Loom.

#### Single Node Offline usage

If you want to use loom fully offline, you need to start Loom using `./up.sh --offline --delete`
at least once **while connected to the internet** before you can disconnect your host
and re-start Loom in full offline mode: `./up.sh --offline`.

> ⚠️ Offline mode only works when you have checked out a specific Git tag (not on a branch like `main`).
> If you followed the installation steps above, you are already on a release tag.

#### Overriding Helm Values

To customize the deployment configuration, add your value
overrides to `charts/values-overwrites.yaml`. This file is intentionally left empty and
is automatically included during Skaffold deployments.

To deploy without resource requests or limits, pass `--no-resources` to `up.sh`.

### Multi Node Deployment

For a more scalable setup, you can deploy Loom using its Helm chart on your Kubernetes cluster.

> ⚠️ We currently only support Traefik as the ingress controller. We are tracking progress on
> integrating Nginx in issue #161.

#### Multi Node Installation Steps

1. You can find and deploy the Helm chart from our official package registry:

    ```bash
    helm repo add loom-prod https://gitlab.com/api/v4/projects/68343701/packages/helm/prod
    ```

2. To customize your deployment, we provide a set of value files located in the
    [`./charts`](./charts) directory of this repository. These files document all the available
    deployment variables, allowing you to tailor the installation to your specific needs.

3. For a true multi-node setup, apply `charts/values-multinode.yaml` as an additional values file:

    ```bash
    helm install loom loom-prod/loom --values charts/values-multinode.yaml
    ```

    This enables horizontal scaling, high availability, and resource quotas suited for multi-node clusters.

#### Multi Node Offline usage

To run Loom in an offline Kubernetes cluster, you need at least
one container image registry that mirrors `registry.gitlab.com/swiss-armed-forces/cyber-command/cea/loom`
within your offline network. Then, override the `image.registry` value in your
deployment scripts to point to your internal image registry.

### Helm Values Reference

All values files are located in the [`./charts`](./charts) directory. They can be combined with
`--values` (Helm) or added to `charts/values-overwrites.yaml` (Skaffold) to tailor your deployment.

- **[`values-overwrites.yaml`](./charts/values-overwrites.yaml)** — Your personal override file.
  Skaffold picks it up automatically on every deploy, so put any local customisations here rather
  than editing the defaults.
- **[`values-gpu.yaml`](./charts/values-gpu.yaml)** — Use this when your nodes have NVIDIA GPUs
  and you want faster AI inference and translation. Without it, all AI workloads run on CPU only.
- **[`values-multinode.yaml`](./charts/values-multinode.yaml)** — Use this when deploying across
  multiple nodes and you need services to scale out under load, storage and search to remain
  available if a node goes down, and resource usage to stay within defined cluster boundaries.
- **[`values-disable-ai-services.yaml`](./charts/values-disable-ai-services.yaml)** — Use this when
  you want to provide external AI endpoints or skip AI features entirely. Note: AI-powered indexing
  steps must also be disabled, otherwise they will fail at runtime.
- **[`values-external-tls-certificates.yaml`](./charts/values-external-tls-certificates.yaml)** —
  Use this when your cluster manages TLS certificates centrally via Vault and you do not
  want Loom to provision its own ClusterIssuer.
- **[`values-no-resources.yaml`](./charts/values-no-resources.yaml)** — Use this when resource
  requests are causing scheduling issues or limits are causing OOM kills or CPU throttling and you
  want containers to burst freely. Note that without requests, the Kubernetes scheduler has no
  resource information to base placement decisions on. Without limits, a single runaway container
  can starve other workloads on the same node.
- **[`values-development.yaml`](./charts/values-development.yaml)** — Use this when actively
  developing Loom locally. It trades model quality for fast iteration: lightweight models, hot
  reload, and all internal services exposed via ingress. Not suitable for production.

## 🚀 Getting Started

Once Loom is running, navigate to [https://frontend.loom](https://frontend.loom) to upload files,
search across your documents, tag results, and interact with the RAG chatbot.

For detailed usage instructions see the [Getting Started Guide](Documentation/getting-started.md).

## 📜 License

Loom is licensed under the MIT License. See the full text of the license in the [LICENSE.txt](LICENSE.txt) file.

## 🛠️ Development Setup

Below you will find the documented setup process for a portable development environment:

- [Development environment setup](Documentation/devenv-setup.md)

## ⚙️ Architecture

Multiple services that are useful for production and development purposes are started:

| Service       | Url                                                      | Description                                   | Remarks                                        |
| ------------- | -------------------------------------------------------- | --------------------------------------------- | ---------------------------------------------- |
| Frontend      | [https://frontend.loom](https://frontend.loom)           | The loom Frontend                             |                                                |
| Translate     | [https://translate.loom](https://translate.loom)         | Translation service powered by LibreTranslate |                                                |
| Open Webui    | [https://open-webui.loom](https://open-webui.loom)       | AI Webinterface                               |                                                |
| Roundcube     | [https://roundcube.loom](https://roundcube.loom)         | Email Webinterface                            |                                                |
| SeaweedFS     | [https://seaweedfs.loom](https://seaweedfs.loom)         | Admin UI for cluster management               |                                                |
| S3            | [https://s3.loom](https://s3.loom)                       | S3-compatible storage API                     |                                                |
| Api           | [https://api.loom](https://api.loom)                     | The loom api                                  | Swagger documentation: <https://api.loom/docs> |
| Flower        | [https://flower.loom](https://flower.loom)               | Monitor celery tasks                          |                                                |
| RabbitMQ      | [https://rabbit.loom](https://rabbit.loom)               | Monitor rabbit messages                       | user: `guest` password: `guest`                |
| Elasticvue    | [https://elasticvue.loom](https://elasticvue.loom)       | ElasticSearch management                      | use "predefined clusters"                      |
| ElasticSearch | [https://elasticsearch.loom](https://elasticsearch.loom) | Elasticsearch Database                        |                                                |
| Rspamd        | [https://rspamd.loom](https://rspamd.loom)               | Rspamd spam detection engine                  |                                                |
| RedisInsight  | [https://redisinsight.loom](https://redisinsight.loom)   | Manage the redis DB                           |                                                |
| Prometheus    | [https://prometheus.loom](https://prometheus.loom)       | Manage prometheus                             |                                                |
| Grafana       | [https://grafana.loom](https://grafana.loom)             | Statistics, Dashboards and alerting           |                                                |
| Traefik       | [https://traefik.loom](https://traefik.loom)             | Traefik reverse proxy                         |                                                |
| Apache Tika   | [https://tika.loom](https://tika.loom)                   | Tika content extraction engine                |                                                |
| Dovecot       | [imaps://dovecot.loom:443](imaps://dovecot.loom:443)     | Imap Server                                   | user: `user` password: `pass`                  |
| Ollama        | [https://ollama.loom](https://ollama.loom)               | AI Server                                     |                                                |
| Gotenberg     | [https://gotenberg.loom](https://gotenberg.loom)         | Document rendering                            |                                                |

![Context Diagram](Documentation/ContainerDiagram.svg)

> ℹ️ External access to most services is intentional. Loom is a toolkit — users may interact
> with the underlying services and their APIs directly.

## 🔗 More Documentation and Links

- [Getting Started Guide](Documentation/getting-started.md)
- [Development environment setup](Documentation/devenv-setup.md)
- [Contributing Guidelines](CONTRIBUTING.md)
- [Code of Conduct](CODE_OF_CONDUCT.md)
- [Third Party Licenses](THIRD-PARTY.md)
- [Frontend Documentation](Frontend/README.md)
- [Backend Documentation](backend/README.md)
- [Integration Testing Documentation](integrationtest/README.md)
- [CI/CD Pipeline Documentation](cicd/README.md)
- [Celery Flower canvas](https://docs.celeryq.dev/en/stable/userguide/canvas.html)
