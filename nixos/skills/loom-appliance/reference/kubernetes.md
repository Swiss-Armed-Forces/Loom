# The cluster

Loom runs on a single-node minikube cluster in the `loom` namespace. Everything below assumes
`--namespace loom`; nothing Loom owns lives anywhere else.

## Looking at it

```bash
kubectl --namespace loom get pods
kubectl --namespace loom get pods --output wide
kubectl --namespace loom describe pod <name>        # events are at the bottom; read those first
kubectl --namespace loom logs <name> --tail 200
kubectl --namespace loom logs <name> --previous     # the container before the last restart
kubectl --namespace loom get events --sort-by .lastTimestamp | tail -40
loom-k9s                                            # interactive, already pinned to the namespace
```

If `kubectl` itself fails, the cluster is not up and this is the wrong file — go back to
`reference/units.md` and check `loom.service`.

## What the workloads are

| Workload | What it does |
| --- | --- |
| `api` | The FastAPI REST API behind `https://api.loom` |
| `frontend` | The web UI behind `https://frontend.loom` |
| `worker` | Celery workers: content extraction, OCR, indexing, AI tasks |
| `crawler` | Watches the S3 bucket and schedules work for new files |
| `beat` | Celery beat — the periodic/scheduled tasks |
| `elasticsearch` | The search index and document store |
| `seaweedfs` | S3-compatible object storage for uploaded files |
| `redis`, `redis-cache`, `redis-filer` | Caching and SeaweedFS metadata |
| `rabbit` | RabbitMQ, the Celery message broker |
| `tika` | Apache Tika, content and metadata extraction |
| `gotenberg` | Document rendering to PDF |
| `ollama` | The local LLM inference server, behind `https://ollama.loom` |
| `prometheus`, `grafana`, `kube-state-metrics` | Metrics and dashboards |
| `elasticvue`, `redisinsight` | Browsers for Elasticsearch and Redis |
| `dovecot`, `roundcube`, `rspamd` | The mail ingest path |
| `persister`, `reaper` | Housekeeping |

A pod that is `Pending` on a one-node cluster is almost always waiting for resources or for a
volume. `kubectl --namespace loom describe pod <name>` says which.

## When files are not being indexed

The pipeline is: upload to SeaweedFS → `crawler` notices → a Celery task on RabbitMQ → `worker`
extracts and indexes → Elasticsearch. Check it in that order.

```bash
kubectl --namespace loom logs deploy/crawler --tail 100
kubectl --namespace loom logs deploy/worker --tail 200
```

Queue depths are visible in the RabbitMQ UI at `https://rabbit.loom`, and through the API at
`https://api.loom/v1/queues`.

## The dead-letter chain

Celery tasks that keep failing move down a chain rather than being retried forever. Seeing messages
pile up in the later queues means tasks are failing repeatedly, and the worker log is where the
reason is.

| Queue | Meaning |
| --- | --- |
| the regular queues | Normal execution |
| `graveyard` | Exceeded the regular delivery limit (3 by default) |
| `dead` | Exceeded the graveyard delivery limit (1 by default) |
| `abyss` | Unprocessable. Nothing consumes this; messages expire after 7 days |

## Restarting things

Restarting a single deployment is reasonable and cheap:

```bash
kubectl --namespace loom rollout restart deploy/<name>
kubectl --namespace loom rollout status deploy/<name>
```

Bringing the whole stack down and up is `loom-down` then `loom-up`, takes a long time, and is the
operator's decision — propose it, do not run it.
