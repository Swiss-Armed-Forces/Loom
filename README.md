# ![Loom Logo](Frontend/src/features/common/branding/loom-logo-full-contour.svg) Document Search Engine

[![License: MIT](badge-mit-blue.svg)](LICENSE.txt)
[![Release Status](https://gitlab.com/swiss-armed-forces/cyber-command/cea/loom/-/badges/release.svg)](https://gitlab.com/swiss-armed-forces/cyber-command/cea/loom/-/releases)
[![Offline Demo](https://img.shields.io/badge/Offline_Demo-Try_it-FC6D26)](https://swiss-armed-forces.gitlab.io/cyber-command/cea/loom/)
[![GitLab Pipeline Status](https://gitlab.com/swiss-armed-forces/cyber-command/cea/loom/badges/main/pipeline.svg)](https://gitlab.com/swiss-armed-forces/cyber-command/cea/loom/-/pipelines?page=1&scope=all&ref=main)
[![Contributor Covenant](https://img.shields.io/badge/Contributor%20Covenant-v2.1%20adopted-ff69b4.svg)](https://www.contributor-covenant.org/version/2/1/code_of_conduct/)

**Loom** is a powerful, easily deployable open-source document search engine designed for
secure, task-specific deployments. It automates indexing of data sources, performs OCR,
extracts content and metadata, and enables powerful full-text search enriched by AI features
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
- **🤖 AI Features:** Loom integrates AI throughout: chat with your documents via a
  RAG chatbot, automatically tag new documents based on existing tags, and get
  AI-generated summaries and image descriptions.
- **📦 Archive Creation:** Easily bundle selected search results or individual documents
  into archives for convenient data extraction and transfer.
- **📌 Tagging:** Organize and categorize your document collection with custom, user-defined tags.
- **🌍 Translation:** Built-in functionality to translate content from various languages
  into English.
- **🖼️ Secure Document Rendering:** View sanitized, rendered versions of documents and
  auto-generated thumbnails directly in the UI, without exposing the original file to the browser.
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

Full installation instructions for deploying Loom as an end user, covering dependencies, system
requirements, single-node and multi-node deployment, offline usage, and Helm values reference:

- [Installation Guide](Documentation/installation.md)

> ℹ️ These instructions are for deploying Loom as an end user. If you want to contribute or develop
> Loom, see [Development Setup](#️-development-setup) instead.

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

> ℹ️ External access to most services is intentional. Loom is a toolkit: users may interact
> with the underlying services and their APIs directly.

## 🔗 More Documentation and Links

- [Installation Guide](Documentation/installation.md)
- [Getting Started Guide](Documentation/getting-started.md)
- [Offline frontend demo](Documentation/demo-mode.md)
- [Development environment setup](Documentation/devenv-setup.md)
- [Contributing Guidelines](CONTRIBUTING.md)
- [Code of Conduct](CODE_OF_CONDUCT.md)
- [Third Party Licenses](THIRD-PARTY.md)
- [Frontend Documentation](Frontend/README.md)
- [Backend Documentation](backend/README.md)
- [Integration Testing Documentation](integrationtest/README.md)
- [CI/CD Pipeline Documentation](cicd/README.md)
- [Celery Flower canvas](https://docs.celeryq.dev/en/stable/userguide/canvas.html)
