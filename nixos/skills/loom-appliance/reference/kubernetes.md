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

Every workload is named `production-loom-<component>`: `app.fullname` is
`<release>-<chart>`, and `up.sh` pins the release to `production` on this box. `kubectl
--namespace loom get deploy,statefulset` prints the real names, and the readiness banner shows
them too. The kind matters as much as the name -- half of these are StatefulSets, and
`deploy/<name>` on one of those is a `NotFound` that reads like a missing service.

| Component | Kind | What it is |
| --- | --- | --- |
| `api` | Deployment | The FastAPI REST API behind `https://api.loom` |
| `frontend` | Deployment | The web UI behind `https://frontend.loom` |
| `worker` | Deployment | Celery workers: content extraction, OCR, indexing, AI tasks |
| `crawler` | Deployment | Watches the S3 bucket and schedules work for new files |
| `beat` | Deployment | Celery beat — the periodic/scheduled tasks |
| `elasticsearch` | StatefulSet | The search index and document store |
| `seaweedfs-master`, `seaweedfs-volume` | StatefulSet | S3-compatible object storage for uploaded files |
| `seaweedfs-filer`, `seaweedfs-admin` | Deployment | The rest of SeaweedFS |
| `redis`, `redis-cache`, `redis-filer` | StatefulSet | Caching and SeaweedFS metadata |
| `rabbit` | StatefulSet | RabbitMQ, the Celery message broker |
| `tika` | Deployment | Apache Tika, content and metadata extraction |
| `gotenberg` | Deployment | Document rendering to PDF |
| `ollama` | Deployment | The local LLM inference server, behind `https://ollama.loom` |
| `prometheus` | StatefulSet | Metrics |
| `grafana`, `kube-state-metrics` | Deployment | Dashboards and cluster metrics |
| `elasticvue`, `redisinsight` | Deployment | Browsers for Elasticsearch and Redis |
| `dovecot` | StatefulSet | The mail store |
| `roundcube`, `rspamd` | Deployment | The rest of the mail ingest path |
| `persister` | StatefulSet | Housekeeping |
| `reaper` | Deployment | Housekeeping |

A pod that is `Pending` on a one-node cluster is almost always waiting for resources or for a
volume. `kubectl --namespace loom describe pod <name>` says which.

## When files are not being indexed

The pipeline is: upload to SeaweedFS → `crawler` notices → a Celery task on RabbitMQ → `worker`
extracts and indexes → Elasticsearch. Check it in that order.

```bash
kubectl --namespace loom logs deploy/production-loom-crawler --tail 100
kubectl --namespace loom logs deploy/production-loom-worker --tail 200
```

Queue depths are visible in the RabbitMQ UI at `https://rabbit.loom`, and through the API at
`https://api.loom/v1/queues`.

## The dead-letter chain

Celery tasks that keep failing move down a chain rather than being retried forever. Seeing messages
pile up in the later queues means tasks are failing repeatedly, and the worker log is where the
reason is.

| Queue | Meaning |
| --- | --- |
| the regular queues | Normal execution, `x-delivery-limit` 5 |
| `loom:graveyard` | Exceeded the regular delivery limit (**5**) |
| `loom:dead` | Exceeded the graveyard delivery limit (**3**) |
| `loom:abyss` | Exceeded the dead delivery limit (1). Nothing consumes this; messages expire after 7 days |

The limits are `celery_deliver_limit`, `celery_graveyard_deliver_limit` and
`celery_dead_deliver_limit` in `backend/common/common/settings.py`. The queues appear in the
RabbitMQ UI under the `loom:` prefix, which is `celery_queue_name_prefix`.

## Restarting things

Mutating, like everything under the mutating heading in `loom-appliance/SKILL.md`: propose it, do not run it. Restarting
`worker` kills in-flight OCR and indexing tasks; `elasticsearch` is a single replica, so restarting
it is an outage.

The kind has to match the table above -- `deploy/` on a StatefulSet is a `NotFound`, which reads
like a workload that does not exist:

```bash
kubectl --namespace loom rollout restart <kind>/production-loom-<name>
kubectl --namespace loom rollout status <kind>/production-loom-<name>
```

Bringing the whole stack down and up is `loom-down` then `loom-up`, takes a long time, and is the
operator's decision — propose it, do not run it.
