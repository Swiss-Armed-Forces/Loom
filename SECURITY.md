# Security Policy

[[_TOC_]]

Loom indexes documents that its operators usually care about keeping private. This file
says how to report a flaw in it, what happens after you do, and — at some length —
which properties of Loom are deliberate and which are defects. The second part matters
more here than it does for most projects, because a great deal of what Loom does would
be alarming in a different system and is load-bearing in this one.

## Reporting a vulnerability

**Do not open a public issue, merge request, or discussion for a security problem.**
The issue tracker is public, and a report filed there is a disclosure to everyone
reading it before there is anything to upgrade to.

Two private channels, either is fine:

- **A confidential issue** —
  [open one with the confidential flag already set](https://gitlab.com/swiss-armed-forces/cyber-command/cea/loom/-/issues/new?issue%5Bconfidential%5D=true).
  A confidential issue is visible only to project members; if you hold the Guest role
  you can file one and will still see your own. This is the channel that lands where
  the work happens, and the one to prefer.
- **Email** — <loom-open-source@vtg.admin.ch>. Use this if you would rather not create
  a GitLab account, or if the finding is sensitive enough that you want to talk before
  filing anything at all.

The GitHub repository at `Swiss-Armed-Forces/Loom` is a mirror. Reports sent through it
reach us more slowly; please use one of the two channels above.

## What to include

A report we can act on without a round trip usually has:

- **Which version.** A release tag (`1.5.1`), or the commit if you are on `main`.
- **Which deployment schema** — Single Node, Multi Node, or Appliance. This is not
  bookkeeping: the same behaviour can be a vulnerability in one schema and a documented
  property of another, and it is the first thing we will ask.
- **What you did**, concretely enough to reproduce. For anything reachable through an
  ingested document, the document itself is the most useful thing you can send.
- **What you got** — the observable result, not only the inference you drew from it.
- **What you think it means**, and any mitigation you already know of.

Loom's own configuration is relevant surprisingly often. If you changed anything in
`charts/values-overwrites.yaml`, `charts/values-user.yaml`, or passed flags to `up.sh`,
say so.

## What happens next

A report moves through the same stages every time:

- **Acknowledgement.** A person confirms we have it, not an autoresponder.
- **Assessment.** We work out whether it is a vulnerability, which deployment schemas it
  affects, and how serious it is. If we cannot reproduce it we will come back to you
  rather than close it quietly.
- **A fix**, developed privately. Loom has no upgrade path between versions, so a fix
  reaches users as a new release rather than as a patch to the one they are running.
- **Coordinated disclosure.** We agree a publication date with you rather than setting
  one unilaterally, and we would rather publish once a fixed release exists than before.
  If we learn a flaw is being exploited, we will tell you and move accordingly.

We will keep you posted as a report moves between those stages, and you are welcome to
ask where it has got to at any point.

**We do not publish response time targets.** Loom is maintained by a small team whose
availability varies, and a deadline we publish and then miss is worth less than no
deadline at all. What we will not do is leave you without an answer.

## Supported versions

**Only the most recent release receives security fixes.** Release candidates (`-rcN`)
and the `main` branch are not supported; `main` is a development branch and may be
broken at any commit.

This is stated as a rule rather than a table of version numbers, because a table goes
stale and then publicly claims the shipping release is unsupported.

It follows from how Loom is meant to be run. There is no upgrade path between versions
and none is planned: a deployment is self-contained, and moving to a new version means
deploying a fresh instance and re-indexing, not migrating. A Loom that has been running
long enough for the supported-version question to be interesting is already outside the
model below.

## Threat model

Read this before deciding whether what you found is a vulnerability. Much of Loom's
design only makes sense if these hold, and a report that assumes otherwise is one we
will close as working-as-intended — not because the concern is silly, but because the
answer is "yes, and here is why".

### What every deployment assumes

Three assumptions hold in all three deployment schemas. They are not defaults to be
hardened; they are the premise.

- **There is no user management, and every user is fully trusted.** Loom has no
  accounts, no login, no sessions, no roles, no API keys and no audit trail of who did
  what. Reaching the frontend is the whole of the authorisation. Everyone who can reach
  a deployment can read everything in it, export it, and destroy it.
- **A deployment is not fit for public exposure.** Loom is meant to run inside a
  trusted environment — a segment, a lab, a box on a desk — and the perimeter around
  that environment is doing the work that authentication would do elsewhere. Putting
  Loom on the public internet is not a configuration we support, and findings that
  depend on having done so are not vulnerabilities in Loom.
- **A deployment is ephemeral and task-specific.** Deploy it, ingest the material for
  one task, analyse, export, shut it down. Loom is not a service to run for a year.

What that leaves is the part that _is_ a boundary, and it is a real one: **the
documents Loom ingests are not trusted.** Files arrive from wherever the material came
from, and the pipeline parses, extracts, renders, OCRs and summarises them with a large
stack of third-party software. That is where our attention goes, and it should be where
yours goes too.

### Single Node

`up.sh` on one machine, running Kubernetes through minikube. This is the evaluation and
small-deployment path.

- **The host is the boundary.** Everything runs on one machine, and anyone who can
  reach that machine's `*.loom` names can reach everything listed below. `up.sh` writes
  those names into the host's `/etc/hosts`.
- **Every service the chart routes is exposed by name, and none of them authenticate.**
  That is not only the API and the frontend: the search index, the object store, the
  message broker, the metrics stack and the inference server are all routed by name and
  all answer without credentials. `hostnames.ingress` in `charts/values.yaml` is the
  list, and it changes with the chart. This is how the stack is meant to be operated and
  debugged.
- **Loom answers over TLS only**, with a certificate it signed itself, because no public
  authority can issue one for `*.loom`. Port 80 carries a redirect and nothing else. A
  browser will warn, and clicking through a warning on a network you do not control
  means trusting whatever answered.
- **The development profile is not a deployment.** `up --development` and
  `up --integrationtest` apply `charts/values-development-http.yaml`, which moves every
  ingress onto the cleartext entrypoint, and the development environment uses a fixed,
  published archive encryption key. Neither is a configuration to put data in.

### Multi Node

The Helm chart on a Kubernetes cluster you already run. This is the schema with the most
of its security posture in the operator's hands rather than ours.

- **The namespace is the boundary, and you own it.** Loom's objects assume the cluster
  around them is trusted. Anyone with access to the namespace — or to a cluster role
  that reaches it — has the data.
- **The document parsers are fenced; everything else reaches everything else.** The
  chart ships Egress policies only, so any workload in the namespace can open a
  connection to any other, and the internal services ask a caller that is already inside
  for no credentials. The exception is the components that parse and render untrusted
  documents: they carry `net: fenced` and get a deny-all egress policy — no other pod,
  no DNS, no Kubernetes API, nothing off the cluster. They answer connections and make
  none. That is the chart's containment for the one boundary this file calls live, and
  it is the thing to check against before reporting a request forgery out of a parser.
  Everything unfenced gets the namespace, DNS and the API server's node address, and no
  route off the cluster.
- **`egress.enabled` removes every NetworkPolicy in the namespace** rather than adding a
  rule to them. It exists so Loom can reach an external S3 source or inference endpoint,
  and turning it on means the namespace has no network policy at all — the parser fence
  above included, so a parser that can be made to issue a request can then issue it
  anywhere. Decide that deliberately.
- **The ingress is yours to place.** The chart renders Ingress objects; which networks
  can reach them is a question about your cluster. `certificate.requireClientCert`
  turns on mutual TLS so that reaching the ingress is no longer enough — note that it
  applies to the routes _this_ chart renders, and that the sibling Traefik chart routes
  its own dashboard without it.
- **Secrets are yours to supply.** The External Secrets Operator integration exists so
  the archive encryption key and the service credentials can come from your own store
  instead of from the chart's pre-install Job. `trustedCertificates` is how an internal
  CA reaches the pods.

### Appliance

A standalone box provisioned from a single USB stick, serving its own network. The
design only makes sense if these hold.

- **The USB stick is the key.** The internal disk is LUKS2, and the key is 4096 random
  bytes on the stick. Pull the stick and the box will not boot. Every stick gets its own
  key.
- **The stick has to stay plugged in.** A running box is watched: remove the key and it
  powers itself off ten seconds later, and a box that booted from a stick it can no
  longer read powers off after three minutes.
- **Box and stick together are not protected.** If both are seized at once, the
  encryption buys you nothing. The design assumes the stick is removed, or travels
  separately, whenever the box is unattended. `--lock-key` changes this — it puts a
  passphrase over the stick's key, so holding the stick stops being enough. It costs
  unattended boot.
- **Lose the stick and the data is gone**, unless somebody wrote down the recovery
  passphrase that the installer prints and that the console shows on its login screen at
  every boot. `--key-backup` takes a second copy.
- **There is no remote access.** No sshd, no accounts but the local operator. The
  console is the only way in — and it is not an authentication boundary: it shows the
  banner, waits for a keypress, and then opens a root-capable session with no password.
  The monitor and keyboard are the whole attack surface. The one exception is an image
  built with `--debug`, which runs an SSH server keyed to a keypair the build generates.
  Such an image announces itself in red on its own login screen and is not something to
  hand to anybody.
- **The console runs an AI agent that can act on the box, and it does not ask first.**
  The bottom pane is `opencode` wired to the cluster's own Ollama — it reads and writes
  files and runs commands as `loom`, which is in `wheel` and `docker`, and its
  permission ruleset is `allow`. It talks to nothing outside the box, so this adds no
  network exposure; what it adds is a way for anyone already at the keyboard to act
  through natural language instead of a shell. Given the bullet above that crosses no
  boundary physical access did not already cross, but it is one more reason the box must
  not be left unattended with the stick in it. Only on a box with a GPU: `nuc12` ships
  neither it nor Ollama.
- **Any USB medium plugged in is mounted and indexed.** A USB port is therefore an
  unauthenticated data-injection path: anyone who can reach the box can put arbitrary
  content into the index, and kernel and FUSE filesystem drivers parse structures that
  whoever plugged it in controls. Media is mounted read-only and never executed, and the
  LUKS key stick is positively excluded — but the parsing itself is the exposure.
- **Booting the stick installs the box.** The installer counts down for 60 seconds and
  then provisions the internal disks by itself. It refuses when the disks already hold a
  Loom pool that _this_ stick's key unlocks, and refuses a second attempt in the same
  boot. Neither covers a stick pointed at somebody else's hardware — treat a Loom stick
  as a device that erases whatever it is booted on.
- **The certificate the appliance serves is self-signed, and a visitor has to decide to
  trust it.** No public authority can issue a certificate for `*.loom`, so the box
  signed its own. The captive portal publishes the anchor and its SHA-256 fingerprint,
  and the fingerprint is also on the box's own console — comparing the two is the step
  that turns clicking through into trusting a specific box.
- **Anyone who can reach the appliance segment can use Loom.** On a cabled box that
  means whoever is on the wire; with `--wifi` it means whoever holds the passphrase.
  `--require-client-cert` is the one build where this is not true — it admits only
  clients holding an issued certificate. On that build the captive portal carries a
  password that mints certificates, the password is on the box's own login screen, and
  so the console screen becomes as sensitive as the keyboard in front of it.
- **The captive portal page is served by the box, not by the cluster**, so it answers
  from the moment the machine is up, before Loom exists. What it hands out by default is
  the certificate the box already presents to anyone opening a TLS connection, which is
  public by definition.
- **Bluetooth is disabled in every image**, and WiFi the same way unless the image was
  built with `--wifi`, which turns the box into an access point and changes most of the
  bullets above. This is a software guarantee — a root shell on the box can undo it — so
  disable the radios in firmware as well if the site requires it.

`Documentation/appliance.md` covers each of these in detail, including what `--debug`,
`--lock-key` and `--require-client-cert` change.

## In scope

Things we want to hear about, in rough order of how much we care:

- **Anything an ingested document can do beyond being indexed.** This is the live
  boundary. Server-side request forgery out of a parser or renderer, XXE, command
  injection, deserialisation, a path traversal that escapes an extraction directory,
  memory-safety bugs in a bundled parser, a decompression bomb that takes a deployment
  down. If a crafted file makes Loom do something that is not "index this file", we want
  it.
- **Anything that breaks a guarantee this file makes.** A fenced component egressing
  anywhere at all; a way to read the LUKS-encrypted disk without the stick; a way past
  `--require-client-cert`; a route that serves Loom in cleartext when it should redirect;
  the USB key guard not firing.
- **Cryptographic failures in archive handling.** Archives are the format in which data
  leaves a deployment. A flaw that lets one deployment's archives be read by someone
  who should not be able to, or that makes the encryption weaker than it claims, is in
  scope.
- **Secrets going somewhere they should not** — credentials or key material written into
  logs, into the search index, into an exported archive, or into a container image.
- **Supply chain.** A published image or chart containing something it does not declare,
  or a dependency fetched without integrity checking.

If you are unsure, report it. We would rather triage something out of scope than not
hear about it.

## Out of scope

These are consequences of the model above rather than defects, and we will close reports
about them. They are listed so you do not spend time on them.

- **No authentication on anything.** Every component the chart routes answers without
  credentials — not only the API and the frontend, but the infrastructure behind them,
  the operational and debugging UIs that ship alongside it, and the Traefik dashboard
  from the sibling chart. There are no accounts to attack, so there is no authentication
  bypass, no privilege escalation, no session handling and no CSRF defence to defeat.
- **Destructive endpoints without authentication**, `/wipe_data` among them. Destroying
  the deployment is a thing trusted users are allowed to do.
- **Insecure direct object references.** File, thumbnail and rendered-document
  identifiers are not checked against a requesting identity, because there is no
  identity to check them against. Everyone may read everything.
- **No upload size limit and no MIME-type validation on the API.** A trusted user
  filling the disk is their own problem.
- **Pod-to-pod reachability inside the namespace**, and the absence of credentials on
  the internal services. Note the distinction that matters: a workload in the namespace
  _reaching_ the search index is the design, whereas _a parsed document_ reaching it is
  the first item in the in-scope list — and a way around the parser fence is the second.
- **The fixed, published archive encryption key under `environment: development`**, and
  the rest of the development profile — cleartext ingresses included. The development
  profile is for development.
- **Self-signed certificate warnings**, and that `*.loom` is not publicly resolvable.
- **Physical access to an appliance**, including the passwordless console session and
  the agent pane that runs in it. The threat model assumes the box is physically
  controlled; everything about the console follows from that.
- **Anything that requires the attacker to already be on the trusted network and does
  not escape it.** "An attacker on the Loom segment can read the documents" is the
  design.
- **Denial of service through ordinary use** — indexing more than the hardware can
  handle, queuing more work than the workers can drain.
- **Findings against a deployment exposed to the public internet**, which is not a
  supported configuration.
- **Reports from automated scanners with no demonstrated impact**, missing hardening
  headers on an unauthenticated single-user tool, and version-fingerprint findings.

## Safe harbour

We will not pursue or support action against anyone who reports a vulnerability to us
in good faith, provided you test only against a deployment you own or have permission
to test, do not access, modify or destroy data belonging to anyone else, and give us a
reasonable chance to fix the problem before telling the world.

That is a statement about how we will behave. It is not authorisation to test somebody
else's Loom deployment, and it cannot waive anyone else's rights.

## Credit

We will name you in the advisory and the release notes if you would like us to, under
whatever name or handle you prefer, and we are equally happy to keep you anonymous. Tell
us which when you report.

We do not run a paid bounty programme.
