# The GPU and the AI services

## The rule

The AI services follow the GPU. An appliance that offloads to a GPU deploys Ollama and gets the
summarisation, translation and RAG features; one built without a GPU deploys neither. If Ollama is
simply not in the cluster, that is a property of how this image was built, not a fault to fix from
the console.

```bash
loom-platform-info                    # the GPU, its memory split, and whether a container can see it
kubectl --namespace loom get pods --selector app=loom-ollama
```

The selector is `app=loom-ollama`, not `app.kubernetes.io/component`: that label is set on the
Deployment's own metadata and not on the pod template (`charts/templates/ollama/_deployment.yaml`
builds those from `app:` plus `app.labels.custom`, and every `customLabels` is empty), so a
component selector returns `No resources found` on a perfectly healthy GPU box -- which reads
exactly like the "built without a GPU" case above.

`loom-platform-info` is the first and usually the last command here. It reports the GPU, the
firmware VRAM carve-out beside the GTT pool, and — the part that actually matters — whether the GPU
reaches a container at all: the CDI specs, `nvidia-ctk`, and the docker runtimes.

## When the cluster will not start because of the GPU

A GPU that does not enumerate stops Loom from starting at all, not just the AI parts. The symptoms
are specific and are documented with their causes:

- `Error response from daemon: AMD CDI spec not found` on a box with no AMD hardware in it.
- `invalid Node Allocatable configuration` with an `ephemeral-storage` capacity of zero.

Both are in `## Troubleshooting` in `/home/loom/loom/Documentation/appliance.md`, with the full
explanation and what fixes each. Read it before concluding anything — the messages say more than
they appear to, and in one case the error is itself proof that the driver loaded correctly.

Neither is fixable from this console. The fix is a new stick, and `--no-gpu` is the way to get a
working CPU-only box out of the one in hand meanwhile.

## When Ollama is up but the AI features do not work

An air-gapped box only has the models that were baked into the image. There is no way to fetch
another.

```bash
kubectl --namespace loom logs deploy/production-loom-ollama --tail 100
kubectl --namespace loom exec deploy/production-loom-ollama -- ollama list   # what is on the box
curl --insecure https://ollama.loom/                            # answers "Ollama is running"
```

Every workload is `production-loom-<component>` -- see `reference/kubernetes.md`. `deploy/ollama`
is a `NotFound`, including on the `exec` that is the only real check below.

A Ready `ollama` pod proves nothing about its model store — the readiness probe answers on an empty
one. `ollama list` is the real check.

If the assistant pane itself is failing every question, the model it is pinned to is probably not in
that list.

## More

`/home/loom/loom/Documentation/appliance.md`:

- `## GPU support`
- `### When the GPU does not come up`
- `### AI services follow the GPU`
