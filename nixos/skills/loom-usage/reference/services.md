# The services on this box

Every name below resolves on the appliance network and is served by the box. Both `http` and
`https` work; `https` costs a self-signed-certificate warning in a browser.

The authoritative list for this deployment is `hostnames` in
`/home/loom/loom/charts/values.yaml`, and `grep loom /etc/hosts` on the box shows what actually
resolves.

## What people use

| Address | What it is |
| --- | --- |
| `frontend.loom` | The Loom web UI. Search, upload, browse, chat. Start here |
| `api.loom` | The REST API. `/docs` for interactive documentation |
| `grafana.loom` | Dashboards: indexing throughput, queue depth, resource use |

## Inspecting the stack

Useful when something looks wrong, and harmless to open.

| Address | What it is |
| --- | --- |
| `elasticvue.loom` | A browser for Elasticsearch — the indexed documents themselves |
| `redisinsight.loom` | A browser for Redis |
| `rabbit.loom` | The RabbitMQ management UI: queue depths, message routing |
| `prometheus.loom` | The raw metrics behind Grafana |
| `s3.loom`, `seaweedfs.loom` | The object store holding the uploaded files |
| `traefik.loom` | The reverse proxy's own dashboard |

## Engines Loom calls

These are internal. They answer directly, but there is rarely a reason to use them by hand.

| Address | What it is |
| --- | --- |
| `tika.loom` | Apache Tika — content and metadata extraction |
| `gotenberg.loom` | Document rendering to PDF |
| `ollama.loom` | The local LLM inference server, behind `/v1` |
| `elasticsearch.loom` | The search index itself |

## Mail ingest

| Address | What it is |
| --- | --- |
| `roundcube.loom` | Webmail |
| `dovecot.loom` | IMAP |
| `rspamd.loom`, `rspamd-worker.loom` | Mail filtering |

## Names with no web page

`redis.loom`, `redis-cache.loom` and `rabbit-amqp.loom` resolve but serve no browsable page — they
are protocol endpoints that other parts of Loom dial. Opening them in a browser does nothing
useful.
