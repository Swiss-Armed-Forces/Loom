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
* **🌐 Translation:** Built-in functionality to translate content from various languages
into English.
* **🔗 REST API:** Seamlessly integrate Loom's powerful search and other functionalities
into your existing applications and workflows through our comprehensive REST API.

## ⚠️ Security

Loom is not intended for public exposure. Its attack model assumes that anyone with access
to any component might also directly access the data, file system, or infrastructure. Loom
does not provide authentication, authorization, or user isolation-these must be managed
externally. None of its components are designed to be secure for unknown audiences, and the
risk of injections or code execution is high for anyone with access.

**Never expose Loom to the internet without an additional authorization layer.**

## 🛠️ Installation

This section provides instructions for setting up Loom in a production-like environment.

**Dependencies:**

Before you begin, please ensure the following dependencies are installed on your system.
This will help make the setup process smooth and easy!

* `git`
* `git-lfs`
* `docker`
* `minikube` (>= [v1.33.1](https://minikube.sigs.k8s.io/docs/start/?arch=%2Flinux%2Fx86-64%2Fstable%2Fbinary+download))
* `helm` (>= [v3.14.0](https://helm.sh/docs/intro/install/))
* `kubectl` (>= [v1.30.0](https://kubernetes.io/de/docs/tasks/tools/install-kubectl/))
* `skaffold` (>= [v2.12.0](https://skaffold.dev/docs/install/))

### Deployment Schemas

You have a couple of options for deploying Loom, depending on your needs:

* **Single Node Deployment:** This is a straightforward way to get Loom running on a single machine
using the `up.sh` script. It's perfect for evaluation or smaller setups.
* **Multi-Node Deployment:** For more extensive or production environments, you can deploy Loom
on top of your existing Kubernetes cluster using our Helm chart.

### Single Node Deployment

This method is designed for simplicity and is a great starting point!

**Minimal System Specifications:**

To ensure Loom runs smoothly, your system should ideally meet these minimum requirements:

* **RAM:** At least 25 GiB
* **CPU:** 8 Cores
* **Disk Space:** 200 GiB
* **GPU (Optional):** For enhanced performance with certain features, we recommend using at least 2 GPUs.
Please see the list of supported GPUs here: [https://github.com/ollama/ollama/blob/main/docs/gpu.md](https://github.com/ollama/ollama/blob/main/docs/gpu.md)

**Installation Steps:**

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

**Note:** After the build process is complete, you can open your web browser
and navigate to [https://frontend.loom](https://frontend.loom) to access Loom.

### Multi-Node Deployment

For a more scalable setup, you can deploy Loom using its Helm chart on your Kubernetes cluster.

**Installation Steps:**

1. You can find and deploy the Helm chart from our official package registry:
[https://gitlab.com/swiss-armed-forces/cyber-command/cea/loom/-/packages](https://gitlab.com/swiss-armed-forces/cyber-command/cea/loom/-/packages)
2. To customize your deployment, we provide a set of value files located in the
[`./charts`](./charts) directory of this repository. These files document all the available
deployment variables, allowing you to tailor the installation to your specific needs.

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
| Frontend       | [https://frontend.loom](https://frontend.loom)             | The loom web-ui                               |                                               |
| Api            | [https://api.loom](https://api.loom)                       | The loom api                                  | Swagger documentation: <https://api.loom/docs>|
| Flower         | [https://flower.loom](https://flower.loom)                 | Monitor celery tasks                          |                                               |
| Traefik        | [https://traefik.loom](https://traefik.loom)               | Traefik reverse proxy                         |                                               |
| RabbitMQ       | [https://rabbit.loom](https://rabbit.loom)                 | Monitor rabbit messages                       | user: `guest` password: `guest`               |
| Elasticvue     | [https://elasticvue.loom](https://elasticvue.loom)         | Manage elastic documents                      | connect to <https://elasticsearch.loom>       |
| Mongo Express  | [https://mongo-web.loom](https://mongo-web.loom)           | Manage the mongo DB                           |                                               |
| RedisInsight   | [https://redis-web-ui.loom](https://redis-web-ui.loom)     | Manage the redis DB                           | connect to `redis:6379`                       |
| Apache tika    | [https://tika.loom](https://tika.loom)                     | Tika engine                                   |                                               |
| Translate      | [https://translate.loom](https://translate.loom)           | Translation service powered by LibreTranslate |                                               |
| Rspamd         | [https://rspamd.loom](https://rspamd.loom)                 | Rspamd spam detection engine                  |                                               |
| cAdvisor       | [https://cadvisor.loom](https://cadvisor.loom)             | Resource usgage and performance of containers |                                               |
| Prometheus     | [https://prometheus.loom](https://prometheus.loom)         | Monitoring system & time series database      |                                               |
| Grafana        | [https://grafana.loom](https://grafana.loom)               | Statistics, Dashboards and alerting           |                                               |
| Minio          | [https://minio.loom](https://minio.loom)                   | File upload                                   |  user: `minioadmin` password: `minioadmin`    |
| Dovecot        | [https://dovecot.loom](https://dovecot.loom)               | Imap Server                                   |  user: `user` password: `pass`                |
| Roundcube      | [https://roundcube.loom](https://roundcube.loom)           | Email Webinterface                            |                                               |

![Context Diagram](Documentation/c4-2-container.svg)

### 🔗 More Documentation and Links

* [Getting Started Guide](Documentation/getting-started.md)
* [Development environment setup](Documentation/devenv-setup.md)
* [Contributing Guidlines](/CONTRIBUTING.md)
* [Code of Conduct](/CODE_OF_CONDUCT.md)
* [Third Party Licenses](/THIRD-PARTY.md)
* [Frontend Documentation](Frontend/README.md)
* [Backend Documentation](backend/README.md)
* [Integration Testing Documentation](integrationtest/README.md)
* [CI/CD Pipeline Documentation](cicd/README.md)
