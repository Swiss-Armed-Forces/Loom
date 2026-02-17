# ![Loom Logo](Frontend/src/features/common/branding/loom-logo-full-contour.svg) Document Search Engine

[![License: MIT](badge-mit-blue.svg)](LICENSE.txt)
[![Release Status](https://gitlab.com/swiss-armed-forces/cyber-command/cea/loom/-/badges/release.svg)](https://gitlab.com/swiss-armed-forces/cyber-command/cea/loom/-/releases)
[![GitLab Pipeline Status](https://gitlab.com/swiss-armed-forces/cyber-command/cea/loom/badges/main/pipeline.svg)](https://gitlab.com/swiss-armed-forces/cyber-command/cea/loom/-/pipelines?page=1&scope=all&ref=main)
[![Contributor Covenant](https://img.shields.io/badge/Contributor%20Covenant-v2.1%20adopted-ff69b4.svg)](https://www.contributor-covenant.org/version/2/1/code_of_conduct/)

**Loom** is a powerful and easily deployable open-source document search engine.
It automates indexing of configured data sources, performs OCR, extracts content
and metadata, enables tagging, and offers powerful search and interaction capabilities.

## ✨ Key Features

* **🚀 Simple Deployment:** Get up and running quickly with asingle `up.sh` script.
* **🔍 Powerful Search:** Experience Google-like search across your documents and
image content with a rich set of syntax options (see [Search Capabilities](#-search-capabilities)).
* **⚙️ Automatic Indexing:** Loom automatically monitors configured data sources
and processes new, updated, or deleted files.
* **📤 Flexible Data Ingestion:** Easily index data by uploading files directly through
the simple file upload provided in the Loom frontend.
* **📚 Comprehensive Content Extraction:** Handles a vast array of file formats,
including Office documents, PDFs, emails, archives, images, and more. Features robust
OCR and efficient processing of large files.
* **🏷️ Metadata Extraction:** Automatically identifies and extracts relevant metadata
from all supported file types during the indexing process.
* **🤖 RAG Chatbot:** Engage in intelligent conversations about your indexed documents.
Our Retrieval-Augmented Generation (RAG) chatbot uses the context of your search queries
to provide insightful answers directly based on your document content.
* **📝 Document Summarization:** Quickly grasp the essence of lengthy documents with
automatically generated concise summaries, available directly within the user interface.
* **📦 Archive Creation:** Easily bundle selected search results or individual documents
into archives for convenient data extraction and transfer.
* **📌 Tagging:** Organize and categorize your document collection with custom,
user-defined tags.
* **🌍 Translation:** Built-in functionality to translate content from various languages
into English.
* **🔗 REST API:** Seamlessly integrate Loom's powerful search and other functionalities
into your existing applications and workflows through our comprehensive REST API.

## 🚫 Limitations and Out-of-Scope Features

Loom is built as a modular and extensible toolkit for document indexing and search-fast to deploy,
easy to adapt, and intended for secure, task-specific use. However, it makes a number of deliberate
trade-offs in scope and design. The following points clarify what Loom is not intended to support:

* **🔄🚫 No upgrade path guarantees:** Loom is designed for ephemeral usage. You are expected to deploy
a fresh instance, index a dataset, analyze the results, and shut it down. There is no support for
migrating data or state across versions or long-running deployments.
* **🧑‍🚫 No user management:** Loom does not provide authentication, authorization, or role separation.
All users accessing an instance are considered fully trusted. If isolation is needed, you must run
separate Loom instances.
* **🌐🚫 Not suitable for public exposure:** Loom is not hardened for internet-facing use. It assumes a
trusted environment and lacks defenses against malicious input. Exposing it without strict external
protection (e.g., VPN, proxy authentication) carries significant security risks.
* **🧰🚫 Not a general-purpose SaaS product:** Loom is not a polished, multi-tenant solution. It’s a
low-friction framework for building document analysis systems, meant to be shaped to your domain;
not a turnkey platform for general use.

These boundaries reflect Loom’s focus on flexibility, transparency, and local control. Ideal for internal
deployments and exploratory workflows, but not for unmanaged or large-scale public scenarios.

## 🛠️ Installation

This section provides instructions for setting up Loom in a production-like environment.

### Dependencies

Before you begin, please ensure the following dependencies are installed on your system.
This will help make the setup process smooth and easy!

* `git`
* `git-lfs`
* `curl`
* `docker`
* `minikube` (>= [v1.33.1](https://minikube.sigs.k8s.io/docs/start/?arch=%2Flinux%2Fx86-64%2Fstable%2Fbinary+download))
* `helm` (>= [v3.14.0](https://helm.sh/docs/intro/install/))
* `kubectl` (>= [v1.30.0](https://kubernetes.io/de/docs/tasks/tools/install-kubectl/))
* `skaffold` (>= [v2.12.0](https://skaffold.dev/docs/install/))

### Deployment Schemas

You have a couple of options for deploying Loom, depending on your needs:

* **Single Node Deployment:** This is a straightforward way to get Loom running on a single machine
using the `up.sh` script. It's perfect for evaluation or smaller setups.
* **Multi Node Deployment:** For more extensive or production environments, you can deploy Loom
on top of your existing Kubernetes cluster using our Helm chart.

### Single Node Deployment

This method is designed for simplicity and is a great starting point!

#### Minimal System Specifications

To ensure Loom runs smoothly, your system should ideally meet these minimum requirements:

* **RAM:** At least 25 GiB
* **CPU:** 8 Cores
* **Disk Space:** 200 GiB
* **GPU (Optional):** For enhanced performance with certain features, we recommend using at least 2 GPUs.
Please see the list of supported GPUs here: [https://github.com/ollama/ollama/blob/main/docs/gpu.md](https://github.com/ollama/ollama/blob/main/docs/gpu.md)

#### Single Node Installation Steps

1. Clone the repository:

    ```bash
    git clone https://gitlab.com/swiss-armed-forces/cyber-command/cea/loom.git
    cd loom
    ```

2. Run the setup script:

    * For a standard deployment (without GPU support):

      ```bash
      ./up.sh
      ```

    * If you have compatible GPUs and want to enable GPU support:

      ```bash
      ./up.sh --gpus all
      ```

After the up process is complete, you can open your web browser
and navigate to [https://frontend.loom](https://frontend.loom) to access Loom.

#### Single Node Offline usage

If you want to use loom fully offline, you need to start Loom using `./up.sh --offline --delete`
at least once **while connected to the internet** before you can disconnect your host
and re-start Loom in full offline mode: `./up.sh --offline`.

⚠️ Offline mode only works when you have checked out a specific Git tag (not on a branch like `main`).
To check out a tag:

```bash
git fetch --tags
git tag -l                    # List available tags
git checkout tags/<tag-name>  # Check out a specific tag (e.g., tags/v1.0.0)
```

#### Overriding Helm Values

To customize the deployment configuration, add your value
overrides to `charts/values-overwrite.yaml`. This file is intentionally left empty and
is automatically included during Skaffold deployments.

### Multi Node Deployment

For a more scalable setup, you can deploy Loom using its Helm chart on your Kubernetes cluster.

> ⚠️ We currently only support Traefik as the ingress controller. We are tracking progress on
integrating Nginx in issue #161.

#### Multi Node Installation Steps

1. You can find and deploy the Helm chart from our official package registry:

    ```bash
    helm repo add loom-prod https://gitlab.com/api/v4/projects/68343701/packages/helm/prod
    ```

2. To customize your deployment, we provide a set of value files located in the
[`./charts`](./charts) directory of this repository. These files document all the available
deployment variables, allowing you to tailor the installation to your specific needs.

#### Multi Node Offline usage

To run Loom in an offline Kubernetes cluster, you need at least
one container image registry that mirrors `registry.gitlab.com/swiss-armed-forces/cyber-command/cea/loom`
within your offline network. Then, override the `image.registry` value in your
deployment scripts to point to your internal image registry.

## 🚀 Getting Started

This section provides a few quick examples to get you started with Loom. For more detailed
instructions, please refer to the full [Getting Started Guide](Documentation/getting-started.md).

**Indexing Your Data:**

To index your data, use the simple file upload feature available directly in the Loom frontend:

1. **Open the Loom Frontend:** Navigate to [https://frontend.loom](https://frontend.loom)
in your web browser.
2. **Upload Files:** Look for the "Upload" option in the user interface (typically in a
sidebar or as a button). Click on it to open a file selection dialog.
3. **Select Files:** Choose the files you want to index and click "Open" or the equivalent button.
4. **Automatic Processing:** Once the files are selected and uploaded through the frontend,
Loom will automatically process them.

**Searching for a File:**

Use the query box at the top to search for your documents. For example:

* To search for a specific PDF file, try: `filename:"your_document.pdf"`
* To find documents containing the phrase "important information", use: `"important information"`
* To search for documents tagged as "project-report", try: `tags:project-report`

**Viewing Raw JSON:**

To see the raw indexed data of a file:

1. Search for the file.
2. Select it from the search results.
3. Click on the "View content" button.
4. Navigate to the "RAW" tab to see the underlying JSON structure.

**Tagging Files:**

You can tag files individually from the file details view (click the tag icon near the filename)
or use the "Add tag" functionality in the left sidebar to tag multiple files.

**Querying by File Extension:**

To find files of a specific type, use the `extension:.` syntax. For example:

* To find all PDF files: `extension:.pdf`
* To find all text files: `extension:.txt`

## 🔍 Search Capabilities

Loom offers a flexible and intuitive search experience with the following options:

* **Fuzzy Search:** Find terms even with minor typos using the tilde operator followed
by the maximum edit distance (e.g., `term~2`).
* **Phrase Search:** Search for exact sequences of words by enclosing them in double
quotes (e.g., `"exact phrase"`).
* **Metadata Filtering:** Narrow down your search results by specifying metadata fields
and their values. Supported fields include:
  * `author:name` (e.g., `author:John Doe`)
  * `filename:*.pdf` (e.g., `filename:report*.pdf`)
  * `when:lastweek` (Supports various date/time formats and relative terms)
  * `size>1M` (Supports size comparisons using units like `K`, `M`, `G`)
  * `tags:important` (Search for documents tagged with "important")

## 📚 Content Extraction

Loom is designed to efficiently extract both text content and valuable metadata from a wide
range of file types:

* **Archives:** ZIP archives and Mail archives (PST).
* **MS Office:** Documents created with Microsoft Word, Excel, PowerPoint, Visio, and Publisher.
* **PDF:** Including full Optical Character Recognition (OCR) to extract text from scanned
documents and images within PDFs.
* **Images:** Performs OCR to extract text content from various image formats.
* **Emails:** Processes EML message files, including the content of attachments.
* **Other Formats:** Supports OpenOffice documents, Rich Text Format (RTF), Plain Text files,
HTML, XHTML, and many other common document formats.

Loom is engineered to handle **large files** effectively by utilizing multi-threaded processing,
ensuring efficient indexing without excessive resource consumption.

## 📜 License

Loom is licensed under the MIT License. See the full text of the license in the [LICENSE.txt](LICENSE.txt) file.

## 🛠️ Development Setup

Below you will find the documented setup process for a portable development environment:

* [Development environment setup](Documentation/devenv-setup.md)

## ⚙️ Architecture

Multiple services that are useful for production and development purposes are started:

| Service        | Url                                                        | Description                                   | Remarks                                       |
| -------------- | ---------------------------------------------------------- | --------------------------------------------- | --------------------------------------------- |
| Frontend       | [https://frontend.loom](https://frontend.loom)             | The loom Frontend                             |                                               |
| Translate      | [https://translate.loom](https://translate.loom)           | Translation service powered by LibreTranslate |                                               |
| Open Webui     | [https://open-webui.loom](https://open-webui.loom)         | AI Webinterface                               |                                               |
| Roundcube      | [https://roundcube.loom](https://roundcube.loom)           | Email Webinterface                            |                                               |
| Minio          | [https://minio.loom](https://minio.loom)                   | File upload                                   | user: `minioadmin` password: `minioadmin`     |
| Api            | [https://api.loom](https://api.loom)                       | The loom api                                  | Swagger documentation: <https://api.loom/docs>|
| Flower         | [https://flower.loom](https://flower.loom)                 | Monitor celery tasks                          |                                               |
| RabbitMQ       | [https://rabbit.loom](https://rabbit.loom)                 | Monitor rabbit messages                       | user: `guest` password: `guest`               |
| Elasticvue     | [https://elasticvue.loom](https://elasticvue.loom)         | ElasticSearch management                      | use "predefined clusters"                     |
| ElasticSearch  | [https://elasticsearch.loom](https://elasticsearch.loom)   | Elasticsearch Database                        |                                               |
| Mongo Express  | [https://mongo-web.loom](https://mongo-web.loom)           | mongoDB management                            |                                               |
| Rspamd         | [https://rspamd.loom](https://rspamd.loom)                 | Rspamd spam detection engine                  |                                               |
| RedisInsight   | [https://redis-insight.loom](https://redis-insight.loom)   | Manage the redis DB                           | connect to `production-loom-redis:6379`       |
| Prometheus     | [https://prometheus.loom](https://prometheus.loom)         | Manage prometheus                             |                                               |
| Grafana        | [https://grafana.loom](https://grafana.loom)               | Statistics, Dashboards and alerting           |                                               |
| Traefik        | [https://traefik.loom](https://traefik.loom)               | Traefik reverse proxy                         |                                               |
| Apache Tika    | [https://tika.loom](https://tika.loom)                     | Tika content extraction engine                |                                               |
| Dovecot        | [imaps://dovecot.loom:443](imaps://dovecot.loom:443)       | Imap Server                                   | user: `user` password: `pass`                 |
| Ollama         | [https://ollama.loom](https://ollama.loom)                 | AI Server                                     |                                               |
| Gotenberg      | [https://gotenberg.loom](https://gotenberg.loom)           | Document rendering                            |                                               |

![Context Diagram](Documentation/ContainerDiagram.svg)

**Note**: We allow external access to quite a few services. This is by design.
Loom is supposed to be a powerful toolkit that enables users to use the tools and their
APIs directly, if needed.

### 🔗 More Documentation and Links

* [Getting Started Guide](Documentation/getting-started.md)
* [Development environment setup](Documentation/devenv-setup.md)
* [Contributing Guidelines](CONTRIBUTING.md)
* [Code of Conduct](CODE_OF_CONDUCT.md)
* [Third Party Licenses](THIRD-PARTY.md)
* [Frontend Documentation](Frontend/README.md)
* [Backend Documentation](backend/README.md)
* [Integration Testing Documentation](integrationtest/README.md)
* [CI/CD Pipeline Documentation](cicd/README.md)
* [Celery Flower canvas](https://docs.celeryq.dev/en/stable/userguide/canvas.html)
