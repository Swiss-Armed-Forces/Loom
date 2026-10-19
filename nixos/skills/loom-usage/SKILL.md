---
name: loom-usage
description: "Using Loom to work with documents. Use ONLY when the question is about searching, uploading or ingesting files, OCR, indexing, tags, archives, summarisation, translation, the RAG chatbot, the REST API, or which web address serves what. Not for diagnosing the box, systemd, kubernetes, networking, hardware or anything named loom-* — that is the loom-appliance skill."
---

# Using Loom

Loom indexes documents, extracts their content and metadata, runs OCR, and lets you search the
result and ask questions about it. On this appliance it is reached from a laptop plugged into the
box's ethernet port — there is no browser on the box itself.

## Getting to it

```text
http://frontend.loom
```

A client on the appliance network gets an address by DHCP and the box answers DNS for every `.loom`
name, so that address works with no configuration on the client side.

`https://frontend.loom` is served too. It costs a browser warning, because the certificate is
self-signed and nothing on the client can verify it — which is why the plain `http` spelling is the
one to hand to a visitor.

**Unless this box was built with `--require-client-cert`.** There only `https` is served, and only
to a client holding a certificate this box issued: port 80 carries nothing but the redirect, and a
visitor with no identity is refused during the TLS handshake, which is the intended answer rather
than a fault. A visitor gets an identity from the captive portal at `http://portal.loom`, using the
password shown on the box's own login screen. `loom-appliance/facts.md` says which image this is.

## Getting documents in

Two ways, and on an appliance the first is the normal one:

- **A USB stick.** Plug it into the box. It is mounted read-only and its contents are copied into
  Loom automatically. `loom-usb-status` on the console reports what happened.
- **The web UI.** Upload through `http://frontend.loom`.

Either way the file lands in object storage, the crawler notices it, and a worker extracts,
OCRs and indexes it. Nothing is searchable until that finishes, so a file that was just added and
cannot be found has probably not been processed yet rather than failed.

## What else is on this box

Every service has a name under `.loom`. `reference/services.md` lists them all and says what each
one is for. The ones worth knowing without looking:

| Address | What it is |
| --- | --- |
| `http://frontend.loom` | The Loom web UI — this is the one to use (`https` on a `--require-client-cert` box) |
| `http://api.loom/docs` | The REST API, with interactive documentation |
| `http://grafana.loom` | Dashboards and metrics |

## Going deeper

| File | What is in it |
| --- | --- |
| `reference/services.md` | Every `.loom` address and what it serves |
| `reference/api.md` | The REST API: where the docs are and what the routes are |
| `reference/search.md` | Searching, indexing, and the AI features |

## The documentation on this box

- `/home/loom/loom/Documentation/appliance.md`, `## Using Loom on the appliance` — using Loom from
  a laptop, and `### Ingesting data from USB` for the stick route.
- `/home/loom/loom/Documentation/ai.md` — the AI features in depth, including `## RAG Pipeline`.
- `/home/loom/loom/README.md` — what Loom is and what it does.

## What Loom is not

Worth saying plainly, because it changes what advice is sensible: Loom is built for ephemeral,
task-specific deployments. There is no user management — everyone who can reach it is fully
trusted — there is no upgrade path between versions, and it is not meant to be exposed to an
untrusted network. A box is deployed, used, and shut down.
