# ![Loom Logo](Frontend/src/features/common/branding/loom-logo-full-contour.svg) Document Analysis Platform

[![License: MIT](https://img.shields.io/badge/License-MIT-blue.svg)](LICENSE.txt)
[![Release](https://img.shields.io/gitlab/v/release/swiss-armed-forces%2Fcyber-command%2Fcea%2Floom?gitlab_url=https%3A%2F%2Fgitlab.com)](https://gitlab.com/swiss-armed-forces/cyber-command/cea/loom/-/releases)
[![Interactive Demo](https://img.shields.io/badge/Interactive_Demo-Try_it-FC6D26)](https://swiss-armed-forces.gitlab.io/cyber-command/cea/loom/)
[![Pipeline Status](https://img.shields.io/gitlab/pipeline-status/swiss-armed-forces%2Fcyber-command%2Fcea%2Floom?branch=main&gitlab_url=https%3A%2F%2Fgitlab.com)](https://gitlab.com/swiss-armed-forces/cyber-command/cea/loom/-/pipelines?page=1&scope=all&ref=main)

**Loom** is an open-source document analysis platform that lets you import documents,
search, analyze, and export them from a single deployment. It extracts text and
metadata from a wide range of file formats, including OCR for scanned documents,
and enriches your collection with AI features like an intelligent chatbot, automatic
tagging, summarization, and translation. Loom runs completely offline, making it
suitable for organizations handling confidential or classified data.

[[_TOC_]]

## 🎬 Try the Demo

Scan the QR code or open the [interactive frontend demo](https://swiss-armed-forces.gitlab.io/cyber-command/cea/loom/).

<!-- markdownlint-disable MD033 -->
<a href="https://swiss-armed-forces.gitlab.io/cyber-command/cea/loom/">
  <img src="Frontend/public/demo-link-qr.gif" alt="Loom live demo QR code" width="220">
</a>
<!-- markdownlint-enable MD033 -->

## ✨ Key Features

- **🚀 Simple Deployment:** Get up and running quickly with a single command.
- **🔍 Powerful Search:** Full-text search across your documents and image content
  with a rich set of search filters and options.
- **⚙️ Automatic Indexing:** Loom automatically monitors configured data sources
  and processes new and updated files.
- **📤 Flexible Data Import:** Easily add data by uploading files directly through
  the Loom frontend.
- **📚 Comprehensive Content Extraction:** Handles a vast array of file formats,
  including Office documents, PDFs, emails, archives, images, and more. Features robust
  OCR and efficient processing of large files.
- **🏷️ Metadata Extraction:** Automatically identifies and extracts relevant metadata
  from all supported file types during the indexing process.
- **🤖 AI Features:** Loom integrates AI throughout: an intelligent chatbot that can
  search, navigate, and act on documents for you; automatic tagging of new documents
  based on existing tags; and AI-generated summaries and image descriptions.
- **📦 Archives:** Bundle search results or individual documents into encrypted archives.
  Archives can be transferred securely between Loom instances and include a built-in
  command-line viewer to explore the data without a Loom installation.
- **📌 Tagging:** Organize and categorize your document collection with custom, user-defined tags
  in addition to the AI-driven automatic tagging.
- **🌍 Translation:** Built-in functionality to translate content from various languages
  into English.
- **🖼️ Secure Document Previews:** View safe previews of documents and auto-generated
  thumbnails directly in the UI, without exposing the original file to the browser.
- **🔗 REST API:** Integrate Loom's search and AI features into your own applications
  through a well-documented REST API.

## 🚫 Limitations

Loom is a platform you adapt to your use case, not a turnkey product. It makes deliberate
trade-offs in scope:

- **🔄 No upgrade path guarantees:** Each deployment is self-contained. When moving to a new
  version, deploy a fresh instance and re-index your data. There is no support for migrating
  state between versions.
- **👩 No user management:** Loom does not provide authentication, authorization, or role
  separation. All users have admin-level access. If isolation is needed, run separate instances.
- **🌐 Not suitable for public exposure:** Loom is not hardened for internet-facing use. Without
  external protection (e.g., VPN, proxy authentication), exposing it publicly carries significant
  security risks.

## 🛠️ Installation

Full installation instructions for deploying Loom as an end user, covering dependencies, system
requirements, single-node and multi-node deployment, offline usage, and Helm values reference:

- [Installation Guide](Documentation/installation.md)

> ℹ️ These instructions are for deploying Loom as an end user. If you want to contribute or develop
> Loom, see [Development Setup](#️-development-setup) instead.

## 🚀 Getting Started

Open [https://frontend.loom](https://frontend.loom). An interactive guided tour will walk you
through all features on your first visit. Upload documents, search your corpus, and use the
AI chatbot to explore and analyze your data.

## 🛠️ Development Setup

Below you will find the documented setup process for a portable development environment:

- [Development environment setup](Documentation/devenv-setup.md)

## 📜 License

Loom is licensed under the MIT License. See the full text of the license in the [LICENSE.txt](LICENSE.txt) file.

## 🔗 More Documentation and Links

- [Installation Guide](Documentation/installation.md)
- [Interactive frontend demo](Documentation/demo-mode.md)
- [Development environment setup](Documentation/devenv-setup.md)
- [Architecture Overview](ARCHITECTURE.md)
- [Contributing Guidelines](CONTRIBUTING.md)
- [Code of Conduct](CODE_OF_CONDUCT.md)
- [Third Party Licenses](THIRD-PARTY.md)
- [Frontend Documentation](Frontend/README.md)
- [Backend Documentation](backend/README.md)
- [Integration Testing Documentation](integrationtest/README.md)
- [CI/CD Pipeline Documentation](cicd/README.md)
- [Technical AI Integration Concept](Documentation/ai.md)
