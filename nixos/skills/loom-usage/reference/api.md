# The REST API

Loom's API is a FastAPI application behind `api.loom`. The application has no authentication of its
own: every request that reaches it is trusted. What stands in front of it may not be — a box built
with `--require-client-cert` refuses a client that presents no certificate, on this route and every
other. `loom-appliance/facts.md` says which kind of box this is.

## Where the documentation is

The API documents itself, and that is always more current than this file:

```text
http://api.loom/docs           Swagger UI, interactive
http://api.loom/redoc          ReDoc, easier to read
http://api.loom/openapi.json   the raw OpenAPI schema
```

Those are for a browser on a laptop, so they are spelled `http` — on a `--require-client-cert` box
it is `https` and the browser needs an identity. From the box itself, use `loom-curl`:

```bash
loom-curl --silent https://api.loom/openapi.json | jq '.paths | keys'
loom-curl --silent https://api.loom/openapi.json | jq -r '.paths | to_entries[] | "\(.key)"' | sort
```

That last command is the right answer to "what endpoints are there" — it reads the live schema
rather than trusting a written list.

`loom-curl` is curl told the two things about this box that no stock trust store knows: Loom's
certificate is self-signed, and where a client certificate is required it holds one. Everything
else it passes through untouched, so curl's own arguments work. Plain `curl` fails on the first
count everywhere, and on both where certificates are required. Use `https` — every image serves
it.

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
| `/v1/init/elasticsearch` | Rebuilds every search index (slow; search is degraded while it runs) |
| `/v1/about`, `/v1/complete-estimate` | Version information, and the indexing-progress estimate |

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

`/v1/init/elasticsearch` is the one to be careful of for a different reason: it is a no-body `POST`
with an inviting name, and it is **expensive rather than destructive**. It clones every index to a
backup, waits for green, then deletes, recreates and reindexes from the clone -- so no data is
lost, search is degraded for as long as the async reindex takes, and a backup index is left behind.
Nothing about the schema above says any of that, which is why it is said here.
