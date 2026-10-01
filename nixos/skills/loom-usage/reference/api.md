# The REST API

Loom's API is a FastAPI application behind `api.loom`. There is no authentication — everyone who
can reach the box is trusted.

## Where the documentation is

The API documents itself, and that is always more current than this file:

```text
http://api.loom/docs           Swagger UI, interactive
http://api.loom/redoc          ReDoc, easier to read
http://api.loom/openapi.json   the raw OpenAPI schema
```

From the box's own console:

```bash
curl --silent http://api.loom/openapi.json | jq '.paths | keys'
curl --silent http://api.loom/openapi.json | jq -r '.paths | to_entries[] | "\(.key)"' | sort
```

That last command is the right answer to "what endpoints are there" — it reads the live schema
rather than trusting a written list.

## The shape of it

Everything is under `/v1`. The routes are grouped by what they act on:

| Prefix | What it covers |
| --- | --- |
| `/v1/files` | The core: list, search, fetch, preview, upload, per-file actions |
| `/v1/files/index` | Indexing |
| `/v1/files/tags` | Tags |
| `/v1/files/translation` | Translation |
| `/v1/files/summarization` | Summarisation |
| `/v1/files/image_description` | Image description |
| `/v1/ai` | The chat and RAG endpoints |
| `/v1/archive` | Archive generation |
| `/v1/queues`, `/v1/celery-inspect` | Queue depths and task inspection |
| `/v1/metrics` | Metrics |
| `/v1/caching` | The cache |
| `/v1/imap` | Mail ingest |
| `/v1/beat` | Scheduled tasks |
| `/v1/websocket` | Live updates |
| `/v1/wipe-data` | Destroys all indexed data |

## Reading the box's own copy

The source is on this box and is the final authority:

```text
/home/loom/loom/backend/api/api/routers/      one file per group above
/home/loom/loom/backend/api/api/api.py        where the prefixes are assigned
```

## A caution

`/v1/wipe-data` destroys everything Loom has ingested, and some `/v1/files` routes dispatch work
that takes a long time on a loaded box. Say what a call would do before suggesting anyone make it,
and never issue a destructive one to answer a question.
