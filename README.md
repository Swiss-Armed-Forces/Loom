# ![loom logo](loom-logo-full.png)

## Document Search Engine

[![License](./License-MIT-blue.svg)](./License.txt)

Loom is an open-source document search engine with automated
crawling, OCR, tagging and instant full-text search.

Loom defines a new way to implement full-text document search into your workflow.

- Easily deploy Loom with a single `up.sh`
- Perform Google-like search through your documents and contents of your images
- Tag your documents
- Translation of various languages to english
- Use a simple REST API to integrate Loom into your workflow

## Features

### Search

- Fuzzy Search (John~2), maximum allowed edit distance is 2
- Phrase Search ("John Smith")
- Search By Author (author:John)
- Search By File Path (filename:\*.txt)
- Search By Date (when: yesterday, today, lastweek, etc)
- Search By Size (size>1M)
- Search By Tags (tags:ocr)

### Crawling

Loom supports local fs crawling, if you need to crawl an SMB share of an FTP location
just mount it using standard linux tools.
Crawling is automatic, no schedule is needed.
Crawlers monitor the file system and automatically process new, changed and removed files.

### Content Extraction

**Loom supports large files**
Supported file types and features:

- ZIP archives
- Mail archives (PST)
- MS Office documents (Word, Excel, Powerpoint, Visio, Publisher)
- OCR over images
- Email messages with attachments
- Adobe PDF (with OCR)
- OCR languages: Eng, Deu, Fra, Por
- OpenOffice documents
- RTF, Plaintext
- HTML / XHTML
- Multithreaded processing
- ... many more ...

## Production Setup

Dependencies:

- `git`
- `git-lfs`
- `docker`
- `minikube` (>= [v1.33.1](https://minikube.sigs.k8s.io/docs/start/?arch=%2Flinux%2Fx86-64%2Fstable%2Fbinary+download))
- `helm` (>= [v3.14.0](https://helm.sh/docs/intro/install/))
- `kubectl` (>= [v1.30.0](https://kubernetes.io/de/docs/tasks/tools/install-kubectl/))
- `skaffold` (>= [v2.12.0](https://skaffold.dev/docs/install/))

```shell
git clone git@gitlab.com:swiss-armed-forces/cyber-command/cea/loom.git
cd loom
./up.sh
```

**NOTE**:

After the build finished, open your browser and go to <http://frontend.loom>

### Getting started

- See [here](Documentation/getting-started.md).

## Development Setup

Below you will find the documented setup process for a portable development environment:

- [Development environment setup](Documentation/devenv-setup.md)

## Architecture

Multiple services that are useful for development purposes are started:

| Service        | Url                                        | Description                                   | Usage                                         |
| -------------- | ------------------------------------------ | --------------------------------------------- | --------------------------------------------- |
| Frontend       | <http://frontend.loom>                    | The loom web-ui                              |                                               |
| Api            | <http://api.loom>                         | The loom api                                 | Swagger documentation: <http://api.loom/docs>|
| Flower         | <http://flower.loom>                      | Monitor celery tasks                          |                                               |
| Traefik        | <http://traefik.loom>                     | Traefik reverse proxy                         |                                               |
| RabbitMQ       | <http://rabbit.loom>                      | Monitor rabbit messages                       | user: `guest` password: `guest`               |
| Elasticvue     | <http://elasticvue.loom>                  | Manage elastic documents                      | connect to `http://elasticsearch.loom`       |
| Mongo Express  | <http://mongo-web.loom>                   | Manage the mongo DB                           |                                               |
| RedisInsight   | <http://redis-web-ui.loom>                | Manage the redis DB                           | connect to `redis:6379`                       |
| Apache tika    | <http://tika.loom>                        | Tika engine                                   |                                               |
| Libretranslate | <http://libretranslate.loom>              | Libretranslate engine                         |                                               |
| Rspamd         | <http://rspamd.loom>                      | Rspamd spam detection engine                  |                                               |
| cAdvisor       | <http://cadvisor.loom>                    | Resource usgage and performance of containers |                                               |
| Prometheus     | <http://prometheus.loom>                  | Monitoring system & time series database      |                                               |
| Grafana        | <http://grafana.loom>                     | Statistics, Dashboards and alerting           |                                               |
| Minio          | <http://minio.loom>                       | File upload                                   |  user: `minioadmin` password: `minioadmin`            |

![Context Diagram](/Documentation/c4-2-container.svg)

Hint: Run plantuml to generate the updated PNG (or an online tool like [PlantText](https://www.planttext.com/)).

### More Documentation

- [Frontend/README.md](Frontend/README.md): Documentation for the frontend component
- [backend/README.md](backend/README.md): Documentation for the backend components
- [integrationtest/README.md](integrationtest/README.md): Documentation for the integration testing
- [cic/README.md](/cicd/README.md): Documentation for the pipeline structure and runner installation
