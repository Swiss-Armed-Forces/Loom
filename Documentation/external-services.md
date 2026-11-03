# External services

Loom can be pointed at an S3 bucket it does not own and at an inference endpoint it does not run.
To the cluster both mean the same thing: a pod opening a connection to an address outside it. This
page covers what that costs, and what breaks silently when half of it is configured.

The two topics are here together because they share three mechanisms — egress, CA trust and
credential sourcing — and because both fail quietly rather than loudly.

## Before either: three things that apply to both

| Mechanism | Skip it and | Set it with |
| --------- | ----------- | ----------- |
| Egress | the connection is dropped, not refused — a timeout that looks like a provider outage | `egress.enabled: true` |
| CA trust | TLS verification fails, if the endpoint uses a private CA | `trustedCertificates.certs` |
| Credentials | the pod never starts, or authenticates as nobody | values, a Secret reference, or ESO |

### Egress is all-or-nothing

Nothing in Loom reaches outside the cluster by default. Both external S3 and external inference
need this:

```yaml
egress:
  enabled: true
```

> ⚠️ **This is not a per-feature switch and it is not scoped to the pods that need it.**
> `charts/templates/common/networkpolicy.yaml` wraps all three of its policies in
> `{{- if not .Values.egress.enabled }}`, so setting it to `true` does not add an allow rule — it
> **deletes every NetworkPolicy the chart ships**, for the whole namespace.

The blast radius is specific enough to be worth stating, because it makes this a decision rather
than a checkbox. The only workloads carrying the `net: fenced` label are **Tika** and
**Gotenberg** — exactly the two components that parse untrusted documents. A malicious PDF or
Office file is opened inside them, and the deny-all-egress policy is what stops a parser exploit
from calling home.

So the trade is explicit: reaching one external endpoint un-fences the two components with the
largest untrusted-input attack surface in the deployment. The chart has no narrower setting. If
that trade is unacceptable, the options are to write your own NetworkPolicy alongside — the chart
does not stop you — or to mirror the data in rather than crawl it out.

The `-allow-k8s-api` policy goes with them. On a cluster with no other policies that changes
nothing; on one with a namespace-scoped default-deny, check what you are left with.

> ℹ️ The policies are only enforced if your CNI implements NetworkPolicy. `up.sh` starts minikube
> with `--cni calico`, which does.

### A private CA: `trustedCertificates`

This is the other direction of trust from
[Hostnames and the self-signed certificate](installation.md#hostnames-and-the-self-signed-certificate):
that section is about the certificate Loom **serves**, this one is about CAs Loom has to **trust**
when it dials something else. An endpoint presenting a certificate signed by a corporate or
internal CA fails verification without it, and the only symptom is a TLS error in the pod log.

Either set it directly:

```yaml
trustedCertificates:
  certs:
    - name: corporate-root
      data: |
        -----BEGIN CERTIFICATE-----
        ...
        -----END CERTIFICATE-----
```

or let `up.sh` split a PEM bundle for you, which writes the same block into
`charts/values-up-flags.yaml`:

```bash
./up.sh --trusted-ca-bundle /path/to/corporate-ca.pem
```

> ⚠️ **Do not use both.** `certs` is a list, and Helm replaces lists wholesale rather than merging
> them. `values-overwrites.yaml` is applied after `values-up-flags.yaml`, so a `trustedCertificates`
> block in your overrides silently discards everything `--trusted-ca-bundle` put there.

What it renders, and only while `certs` is non-empty: a ConfigMap plus a `ca-installer` init
container that appends your PEMs to the image's own bundle, mounts the result over
`/etc/ssl/certs/ca-certificates.crt`, and sets `SSL_CERT_FILE`, `REQUESTS_CA_BUNDLE` and
`NODE_EXTRA_CA_CERTS`. An empty `certs` list and an absent `trustedCertificates` key behave
identically.

Not every pod gets both halves:

| Pods | What they get |
| ---- | ------------- |
| api, worker, reaper, persister, beat, crawler, frontend, ollama | Mount **and** environment variables |
| The infrastructure pods (Elasticsearch, Redis, RabbitMQ, Tika, Gotenberg, Grafana, …) | The mount only, which is the default path their runtimes already read |
| The SeaweedFS workloads and the pre-install Jobs | Neither — they have no `trustedCerts` include |

Every pod that dials an external endpoint is in the first group, so both external S3 and external
inference are covered.

> ⚠️ **Editing the rendered ConfigMap by hand does not restart anything.** The Deployments carry no
> `checksum/config` annotation, so pods keep the bundle they started with. `kubectl rollout restart`
> the affected Deployments, or redeploy.

### Credentials

| What you have | What to use |
| ------------- | ----------- |
| Static values you are willing to put in a values file | `accessKey` / `secretKey`, `llm.<client>.api_key` |
| A Kubernetes Secret you created yourself | `accessKeySecretRef` / `secretKeySecretRef` |
| A secret store — Vault, AWS Secrets Manager, Azure Key Vault | [External Secrets Operator](installation.md#external-secrets-operator-eso) |
| An IAM role, IRSA, or an instance profile | **Not supported.** Static keys only |

> ⚠️ The chart creates no Secret for `accessKeySecretRef` / `secretKeySecretRef`. Those names must
> already exist in the namespace, by whatever means you like. The chart's own
> `externalSecrets.secrets` machinery cannot produce them either: it always names the Secret's data
> key after the environment variable, and these two are read under keys you choose.

---

## Inference endpoints outside the cluster

Loom deploys Ollama and wires twelve LLM clients to it. Pointing those clients at a GPU host you
already run, or at a hosted service, is done per client — there is no global switch.

Two things that look like that switch and are not: `values-disable-ai-services.yaml` turns AI
*off* rather than pointing it elsewhere, and `ollama.service.externalHost` never existed as working
configuration. Both are covered under
[Things that look like the knob and are not](#things-that-look-like-the-knob-and-are-not).

### There are twelve clients and no global switch

| Client | Dialled by | What it does |
| ------ | ---------- | ------------ |
| `embedding` | worker, reaper, persister, beat | Chunk vectors at index time, question vectors at RAG time |
| `agent` | **api** | The chatbot agent loop |
| `suggest_queries` | worker | Lucene query candidates |
| `summarization_key_points` | worker | Map stage of summarization |
| `summarization` | worker | The summary |
| `summarization_refine` | worker | Refine stage |
| `rag_hyde` | worker | Hypothetical-document generation |
| `rag_rerank` | worker | Per-chunk relevance scoring |
| `rag_synthesize` | worker | The final grounded answer |
| `vision` | worker | Image description |
| `language_detection` | worker | Language detection |
| `translation` | worker | Translation |

`agent` is the only one built in the api pod. The rest are constructed in the worker image, which
reaper, persister and beat also run.

> ⚠️ **A client whose `endpoint` you leave unset is not unconfigured — it is pointed at the
> in-cluster Ollama.** `charts/templates/common/settings-configMap.yaml` renders every one of the
> twelve as `.endpoint | default $ollamaEndpoint`, where `$ollamaEndpoint` is the in-cluster
> Ollama Service — `http://loom-loom-ollama:11434/v1/` for a release named `loom`. There is no "not set" state, and overriding the
> `_llmDefaults` anchor in your own values file changes nothing — YAML anchors are resolved within
> the file that defines them. All twelve have to be named individually, under exactly the keys in
> the table above. The chart has no values schema, so a key that is not one of these is accepted in
> silence.

### Pick the provider, or get Ollama's behaviour against a hosted API

> ⚠️ `provider` is the one field that *does* default, and it defaults to `ollama`. Setting
> `endpoint` without setting `provider` builds Loom's Ollama provider against your endpoint: it
> withholds `max_completion_tokens`, claims the model supports thinking, and demotes every system
> message after the first to user-role text. None of that errors — the answers just get worse.

| Value | For |
| ----- | --- |
| `ollama` | Ollama spoken to directly, including one you run outside the cluster |
| `litellm` | A LiteLLM proxy. In Loom's deployments it fronts vLLM |
| `infomaniak` | Infomaniak's AI service, which serves open weights under short slugs |
| `openai` | Hosted OpenAI, or a gateway that matches it exactly |

`openai` is the only value that neither claims thinking support nor merges system messages,
because OpenAI's own table knows its models per model. Why each of the others differs is in
[AI Chatbot Architecture → Provider](ai.md#provider); this page does not restate it.

> ℹ️ An unrecognised value fails at pod startup with the accepted options listed, not at deploy
> time. The chart does not validate it; the settings model does.

One rule from that page is operational rather than architectural and is worth repeating here: on
LiteLLM or vLLM, where the served name is whatever the operator configured, **name the deployment
after the weights**. The model family — and with it the JSON-schema transformer used for structured
output — is matched off the model name. A deployment served as `prod-deployment-1` matches nothing,
gets generic rules, and structured output degrades with no error.

### A complete worked example

Every client pointed at one endpoint, in `charts/values-overwrites.yaml`. Copy it whole and change
the values at the top.

> ℹ️ The `&external-llm` anchor is local to this file. The `&llm-defaults` anchor in
> `charts/values.yaml` is not in scope here, which is why this defines its own — under a different
> key name, so it does not shadow the chart's.

```yaml
# charts/values-overwrites.yaml

# Required to reach anything outside the cluster. Read what this deletes first:
# it removes every NetworkPolicy in the namespace, un-fencing Tika and Gotenberg.
egress:
  enabled: true

# Just this. Not values-disable-ai-services.yaml, which also skips embedding.
ollama:
  enabled: false

# The one place to change the endpoint. Not named `_llmDefaults`: that key exists in
# charts/values.yaml, and shadowing a key the chart defines is a trap for later.
_externalLlm: &external-llm
  # Without this you get Loom's Ollama provider against a service that is not Ollama.
  provider: openai                         # ollama | litellm | infomaniak | openai
  endpoint: https://llm.example.com/v1/    # a private CA needs trustedCertificates
  api_key: REPLACE-ME                      # or source it from ESO, below
  model: qwen3-32b-instruct                # the name the endpoint serves it under
  max_tokens: 8192                         # keep below the model's context window

llm:
  embedding:
    <<: *external-llm
    model: Qwen/Qwen3-Embedding-8B
    # See the warning below: these three are not optional for a non-nomic model.
    dimensions: 4096
    document_prefix: ""
    query_prefix: ""

  agent:
    <<: *external-llm
  suggest_queries:
    <<: *external-llm
  summarization_key_points:
    <<: *external-llm
  summarization:
    <<: *external-llm
  summarization_refine:
    <<: *external-llm
  rag_hyde:
    <<: *external-llm
    max_tokens: 400          # a passage to embed, not an answer
  rag_rerank:
    <<: *external-llm
  rag_synthesize:
    <<: *external-llm
  vision:
    <<: *external-llm
  language_detection:
    <<: *external-llm
  translation:
    <<: *external-llm
```

`rag_hyde` overriding `max_tokens` is the merge key working as intended: `<<:` supplies a key only
where the block does not set it itself.

To keep the API key out of the values file, drop `api_key` from the anchor and enable the matching
`externalSecrets.secrets` entries instead — there is one per client,
`llm__<client>__api_key`, all twelve already present in `charts/values.yaml`. See
[External Secrets Operator](installation.md#external-secrets-operator-eso). An enabled ESO entry
wins: the settings ConfigMap omits the plaintext key entirely.

> ⚠️ The embedding client needs more than an endpoint swap, and it is the one client whose
> misconfiguration is invisible. `dimensions` sizes the Elasticsearch `dense_vector` field and is
> never sent to the API, so a wrong value is rejected at index time and a changed value means
> recreating the index. `document_prefix` and `query_prefix` default to
> `nomic-embed-text-v2-moe`'s and are prepended by Loom rather than by the model, so leaving them
> set for a different model injects literal `search_document:` text into every vector and merely
> makes retrieval worse. See the `llm.embedding` keys in `charts/values.yaml`.

### Turning the in-cluster Ollama off

```yaml
ollama:
  enabled: false
```

That, and nothing else.

> ⚠️ **Do not use `charts/values-disable-ai-services.yaml` for this**, and do not use
> `up.sh --disable-ai`, which applies it. That file sets `ollama.enabled: false` *and*
> `pipeline.skip_embedding_while_indexing: true` and
> `pipeline.skip_auto_tag_file_while_indexing: true`. With those on nothing is ever embedded, so
> RAG retrieves from an empty set and the chatbot answers from nothing — while every service is up
> and nothing is logged, because the skips are deliberate.

The right failure mode comes for free once Ollama is gone:

> ℹ️ `ollama.enabled: false` removes the Service as well as the Deployment, so a client you forgot
> does not quietly keep working — it resolves nothing and its task retries into the dead-letter
> chain. That is the good failure mode, and the reason to turn Ollama off rather than leave it
> running as a fallback you will not notice you are using.

`skip_summarize_while_indexing`, `skip_translate_while_indexing` and
`skip_image_description_while_indexing` already default to on, so there is nothing to turn off
there. Those capabilities stay reachable on demand through the API and the agent's tools.

### Checking you did not miss one

```bash
kubectl get configmap -n loom <release>-loom-settings -o jsonpath='{.data}' \
  | tr ',' '\n' | grep 'llm__.*__endpoint'
```

Twelve lines, and none of them should still name the in-cluster Ollama Service. Any that does is a
client you missed, pointed at an Ollama you are about to remove. Run the same check for `llm__.*__provider`: twelve
again, and a missing one is a client silently on `ollama`.

### Things that look like the knob and are not

| Looks like it | Actually |
| ------------- | -------- |
| `values-disable-ai-services.yaml` | Turns AI off, including the indexing steps. See above |
| `up.sh --disable-ai` | Applies that same file. Same answer |
| `extraEnv` | Lands in the settings ConfigMap verbatim, so it *can* set `llm__*` keys. Use the values above instead — one way, with ESO integration and no silent typos |

---

## S3 buckets outside the cluster

By default Loom deploys a single S3 crawler that watches the internal SeaweedFS intake bucket. Any
number of additional crawlers can watch external S3-compatible endpoints, listed under
`extraS3Sources`. Each entry spawns a dedicated crawler `Deployment` rendered from the same Helm
template as the built-in one.

> ⚠️ Set `egress.enabled: true`. Read [Egress is all-or-nothing](#egress-is-all-or-nothing) first —
> it deletes every NetworkPolicy in the namespace, not just the crawler's.

### What an entry contains

| Key | Required | What it does |
| --- | -------- | ------------ |
| `name` | yes | Suffix on the Deployment name, and must be unique |
| `s3Storage` | yes | Endpoint and credentials |
| `sourceId` | no | The `source` search facet, as `<sourceId>/<bucketName>`. Defaults to `name` |
| `bucketAlias` | no | Display root in file paths, as `//<alias>/<key>`. Defaults to the bucket name |
| `replicaCount` | no | Defaults to 1. Leave it there — see below |
| `resources` | no | Falls back to `crawler.resources` |

`bucketAlias` is what a user sees in the folder tree; `sourceId` is what they filter on with
`source:`. They can be set to unrelated strings, so it is worth keeping them consistent.

**With plain credentials:**

```yaml
egress:
  enabled: true

extraS3Sources:
  - name: archive-server          # unique identifier; used in the Deployment name
    s3Storage:
      host: minio.example.com:9000  # host[:port] of the external S3 endpoint, no scheme
      bucketName: my-bucket
      accessKey: my-access-key
      secretKey: my-secret-key
      secureConnection: true        # set false only for a plaintext endpoint
    bucketAlias: "Archive Bucket"  # optional display name shown in file paths
    sourceId: archive-server       # optional source identifier, defaults to name
```

**With credentials from a Kubernetes Secret** — one you created yourself, or one an External
Secrets Operator `ExternalSecret` produces. The chart does not create it; see
[Credentials](#credentials).

```yaml
extraS3Sources:
  - name: vault-managed-source
    s3Storage:
      host: minio.example.com:9000
      bucketName: my-bucket
      secureConnection: true
      accessKeySecretRef:         # references a K8s Secret by name + key
        name: my-s3-credentials
        key: access_key
      secretKeySecretRef:
        name: my-s3-credentials
        key: secret_key
```

Multiple sources can be listed. Each produces an independent crawler pod with its own intake
storage credentials, so buckets on different servers or with different credentials are all
supported simultaneously.

> ⚠️ Omitting `bucketName` does not fail. The pod inherits the default `loom-intake` and goes
> looking for a bucket called `loom-intake` **on the external host**.

### What Loom needs to be allowed to do

The crawler performs exactly three operations on the source bucket: `ListObjectsV2`, `GetObject`,
and ranged `GetObject` for archive pre-screening. **No writes and no deletes** — indexing leaves
the bucket unchanged. A read-only credential is correct and sufficient:

- `s3:ListBucket` on the bucket
- `s3:GetObject` on `<bucket>/*`
- `s3:GetBucketLocation` additionally, and only on a bare `s3.amazonaws.com` host

### Files are copied into Loom, not read in place

> ⚠️ Every object the crawler sees is downloaded and stored permanently in SeaweedFS. Nothing is
> streamed from the source at search or preview time. **Size SeaweedFS for the entire external
> corpus, not for an index of it.** Deleting an object from the source bucket does not remove it
> from Loom.

A crawler restart — a node drain, an OOM kill, a redeploy — re-downloads the whole bucket. The
record of what has been seen lives in the process, not on disk. Duplicates are discarded at index
time by fingerprint, so storage does not grow and the index is not corrupted, but the bandwidth and
the source-side request bill are spent again. On a large bucket over a metered link this is the
cost that surprises people.

> ⚠️ For the same reason, leave `replicaCount` at 1. Two replicas each list and fetch every object
> and dedup them at index time. It buys nothing and doubles the egress.

### Addressing, region and TLS

| Fact | Consequence |
| ---- | ----------- |
| The client is the MinIO SDK, not boto3 | `host` is `host[:port]` with **no scheme**. `https://minio.example.com` is wrong; use `secureConnection` |
| Addressing is path-style for everything except AWS and Alibaba | A vendor requiring virtual-host style will not work |
| There is no `region` setting | Every non-AWS endpoint is signed with `us-east-1`. An endpoint that enforces region in the signature cannot be used |
| Credentials are static keys | No IAM roles, no IRSA, no instance profiles |

For AWS S3 proper: `secureConnection: true` and a region-qualified hostname such as
`s3.eu-central-1.amazonaws.com`. A private CA on the endpoint needs
[`trustedCertificates`](#a-private-ca-trustedcertificates).

### Checking it works

```bash
kubectl get deploy -n loom | grep crawler
kubectl logs -n loom deploy/<release>-loom-crawler-<name> --tail=50
```

A connection that hangs and times out rather than being refused is the egress fence. A TLS
verification error is the missing CA.

> ℹ️ `extraS3Sources` has no automated test coverage anywhere in this repository. Verify a new
> source against a throwaway bucket before pointing it at the real one.
