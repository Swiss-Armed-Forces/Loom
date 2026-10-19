# CLAUDE.md

This file provides guidance to Claude Code (claude.ai/code) when working with code in this repository.

## Project Overview

**Loom** is an open-source document search engine that automates indexing of data sources, performs OCR,
extracts content and metadata, and offers powerful search capabilities with RAG chatbot functionality.
It's designed for ephemeral, secure, task-specific deployments - not as a long-running production service.

Key architectural principles:

- No upgrade path guarantees (deploy fresh, analyze, shut down)
- No user management (all users fully trusted)
- Not suitable for public exposure (trusted environment only)
- Modular, extensible toolkit approach

## Architecture

Loom uses a microservices architecture running on Kubernetes (via minikube for single-node deployments):

### Backend Services (Python)

The backend is organized into four Poetry-managed packages in `backend/`:

1. **common** - Shared infrastructure used by all other packages:
    - Celery app configuration and task infrastructure
    - Repository patterns (Elasticsearch via `es_repository.py`)
    - Services: file storage, encryption, queuing, IMAP
    - Models and domain objects
    - Message queue integration (RabbitMQ via `pubsub_service.py`)

2. **api** - FastAPI REST API (`backend/api/api/`):
    - Entry point: `main.py` and `api.py`
    - Routes in `routers/` directory
    - OpenAPI schema generation for frontend TypeScript types
    - Prometheus metrics integration

3. **worker** - Celery worker for file processing (`backend/worker/worker/`):
    - `index_file/` - File content extraction and indexing pipeline
    - `ai/` - AI-powered summarization, RAG, and translation
    - `create_archive/` - Archive generation tasks
    - `periodic/` - Scheduled background tasks
    - Entry point: `main.py` with Celery tasks in `tasks.py`

4. **crawler** - Watches S3 buckets and schedules file processing:
    - Monitors uploaded files via polling and triggers worker tasks

### Task Queue Architecture

Loom uses **Celery** with **RabbitMQ** as the message broker. Tasks flow through a dead-letter chain:

- Regular queues for task execution
- Graveyard queue for tasks that exceeded the regular delivery limit
- Dead queue for tasks that exceeded the graveyard delivery limit
- Abyss queue for unprocessable tasks (no worker consumes; messages expire via TTL)
- Delivery limits are configurable via `settings.py`; queue wiring in `common/celery_app.py`

### Frontend (TypeScript/React)

Located in `Frontend/`:

- Built with Vite + React + TypeScript
- API types auto-generated from backend OpenAPI schema
- Uses pnpm for package management (via corepack)

### Data Storage

- **Elasticsearch** - Full-text search and document indexing
- **Redis** - Caching layer
- **SeaweedFS** - S3-compatible object storage for uploaded files

### External Services

- **Apache Tika** - Content extraction engine
- **Gotenberg** - Document rendering to PDF
- **Ollama** - AI inference server for LLM features
- **Traefik** - Reverse proxy and ingress controller

All services accessible via `*.loom` domains (configured in /etc/hosts by `up.sh`).

## Development Environment

Loom uses **devenv** (Nix-based) for reproducible development environments. When you `cd` into the repo,
direnv automatically loads the environment.

**Run every nix command through the devenv shell** (`devenv shell -- …`, or `direnv exec <tree> …`).
`devenv.nix` sets `NIX_CONFIG` from `cachix.pull` there, and that is the only thing *in this
repository* pointing nix at `loom.cachix.org` — devenv applies `cachix.pull` to the invocations it
drives itself and to nothing else. A bare `nix-build ./nixos` outside the shell rebuilds the whole
appliance closure from source rather than fetching it, which under `--allow-cross` means emulating
an aarch64 kernel under qemu.

That `NIX_CONFIG` only takes effect for a caller in nix's `trusted-users`. The supported setup
instead names the caches in the machine's own `/etc/nix/nix.conf`, where the daemon reads them and
no account needs privilege — `./cicd/setup_devenv.py` writes it, and
`Documentation/devenv-setup.md` has the block. On a machine with neither, nix prints
`ignoring untrusted substituter 'https://loom.cachix.org'` and builds from source.

### Common Commands

All commands below are provided by devenv scripts (run `devenv-help` to see full list):

**Application lifecycle:**

- `up` - Start Loom (wraps `./up.sh`). `kubernetes.api` in `charts/values.yaml` is the minikube node
  address and the single authority for it: `vars.sh` reads it as `LOOM_MINIKUBE_IP`, `up.sh` pins the node
  with `minikube start --static-ip` and stops if the node lands elsewhere, and the same value is the
  `ipBlock` in the `-allow-k8s-api` NetworkPolicy. It has to be the *node's* address, not the API server's
  ClusterIP, because a NetworkPolicy is matched after kube-proxy has rewritten `10.96.0.1:443` to the node.
  Overriding it in `values-overwrites.yaml` moves the policy but not the node
- `up --resume-if-deployed` - Skip `install_third_party` and `run_skaffold` when the cluster already
  carries this checkout's chart versions, compared against the `helm.sh/chart` label on the live
  Deployments (`helm list` cannot answer: the loom and traefik skaffold configs render with
  `helm template` and apply with kubectl, so no helm release is recorded). For a host that runs
  `up.sh` at every boot — `loom.service` on the appliance passes it in run mode, and nothing else
  does, because a developer running `up` expects their working tree to reach the cluster. `minikube
  start` is never skipped. The check cannot see an edit under `charts/templates/` with no version
  bump in `charts/Chart.yaml`. Without it, `skaffold run`'s fresh `skaffold.dev/run-id` per
  invocation rolls every Deployment on every boot
- `down` - Stop Loom
- `build` - Build all Docker images

**Backend testing:**

- `backend-test` - Run all backend tests with pytest and coverage (always runs from `backend/` directory)
- `backend-test api/tests/test_foo.py` - Run specific test file (paths are relative to `backend/`)
- `backend-test worker/tests/test_bar.py::test_function` - Run specific test function
- Scope tests to relevant packages/files when possible — e.g. `backend-test api/` to run only API tests

**Ollama wrapper:**

- `ollama-test` - Run the tests for `ollama/ollama_wrapper.py`, the entrypoint of the Ollama
  container image (`ollama/tests`). Its own script because `backend-test` cds into `backend/` and
  cannot reach it, and because `appliance-pytest` is the appliance's suites sharing one pytest
  session. Also runs as a git hook on any change to `ollama/*.py`, so `devenv test` covers it and
  there is no CI job of its own. Extra arguments go to pytest.
  The wrapper decides `OLLAMA_NUM_PARALLEL` from the GPU it can see — NVML through `ctypes` for
  NVIDIA, amdgpu sysfs for AMD, since the ROCm image ships no `rocm-smi`; NVML rather than
  `nvidia-smi` because the container toolkit injects a NixOS host's driver executables without the
  ELF interpreter they need, so they cannot exec in a pod — and **refuses to start** when
  `LOOM_GPU_VENDOR` (set by `charts/values-{amd,nvidia}-gpu.yaml`) names a vendor whose device node
  is absent. It deliberately never sets `OLLAMA_CONTEXT_LENGTH`; see the "Ollama GPU Configuration"
  section in `Documentation/installation.md`

**aitools testing:**

- `aitools-test` - Run all `aitools` tests and the `cicd/tests/` tests covering the scripts
  beside it, with pytest (always runs from `cicd/` directory). `cicd/tests/` is also where the
  shell scripts under `charts/files/` are tested from, there being no other pytest root that can
  reach them
- `aitools-test aitools/tests/test_git_helpers.py` - Run specific test file (paths relative to `cicd/`)

**Frontend:**

- `frontend-test` - Run frontend tests
- `frontend-build` - Build frontend bundle
- `generate-frontend-api` - Regenerate TypeScript API types from backend OpenAPI schema

**Integration tests:**

- `run-integrationtest` - Run full integration test suite

**Data management:**

- `wipe-data` - Clear all indexed data from Loom

**Kubernetes/Docker:**

- `kubernetes-pause` - Pause cluster (saves resources)
- `kubernetes-stop` - Stop cluster
- `kubernetes-delete` - Delete cluster entirely
- `kubernetes-fetch-all-pod-logs` - Dump all pod logs to `logs/` directory
- `docker-minikube` - Docker CLI wrapper to communicate with minikube's Docker daemon

**Appliance image:**

- `build-appliance-image` - Build (and optionally flash) a NixOS appliance USB installer.
  `--platform` picks the box: `spark` (DGX Spark, aarch64), `evo-x2` (GMKtec EVO-X2, x86_64) or
  `nuc12` (Intel NUC 12 Pro, x86_64). The build host must match the platform's architecture unless
  `--allow-cross` is given. See `Documentation/appliance.md`
- `build-appliance-image --include-rc` - Let the default tag pick take a release candidate. Without
  `--tag`, the build takes the newest `X.Y.Z` in the checkout and skips every `X.Y.Z-rcN` above it,
  because between releases an rc is the newest thing tagged and a stick built from one looks exactly
  like the right one until somebody boots it. With no release to fall back to the build stops and
  names the rc it declined, rather than shipping it — the confirmation prompt is no guard here,
  since `--yes` skips it and both CI and `appliance-vm installer` always pass `--yes`. `--tag` takes
  any tag, rc included, with no flag needed. `appliance-vm installer` forwards this flag
- `build-appliance-image --no-gpu` - Build CPU-only for a platform that offloads to a GPU:
  `evo-x2` (Radeon 8060S via ROCm) or `spark` (GB10 Blackwell via CUDA). There is no `--gpu`: the
  GPU is declared per platform in `nixos/platforms/<id>.nix`. Use this when a box turns out not to
  enumerate its own GPU, which otherwise stops Loom from starting at all. Note it also drops the
  AI services, since those follow the GPU. On `spark` it keeps `hardware.nvidia` — that driver also
  runs the box's console — so it means "no offload", not "no NVIDIA"
- `build-appliance-image --interface NAME` - Pin the appliance NIC by the name the box reports
  (`enp2s0`, not `eth0`). Only needed when no platform matches the hardware; without it a wired
  port is claimed automatically
- `build-appliance-image --vm-serial` - Add a getty on ttyS0 to the installer and to the box it
  installs, so a VM can be driven from a terminal that copies and pastes. For
  `appliance-vm installer --serial`; refused alongside `--flash`, because the result is one unit
  different from a real stick
- `build-appliance-image --wifi` - Additionally run a bridged WiFi access point on the appliance.
  Radios are disabled in every other image. Related flags: `--wifi-ssid`, `--wifi-psk`,
  `--wifi-country`, `--wifi-interface`. Changes the appliance threat model - see
  `Documentation/appliance.md`
- `build-appliance-image --debug` - Additionally run an SSH server on the box, keyed to an ed25519
  pair generated for that image and left in a temp directory the build prints, along with two
  ready-made `ssh_config` files. This is the one flag that takes back the appliance's "no remote
  access" guarantee, so the box announces it in red at the bottom of its login screen, in the motd,
  in the console status line and on the second line of its boot menu entry (the title stays `Loom`,
  as it does for `first-time-setup`), and the image file is named `-debug`. It
  also boots without the splash and downgrades the USB key guard to a warning, so it does not behave
  like a real stick. Both boot modes run the sshd, first-time setup included - that mode is the one
  most worth reaching remotely, since its fetch needs the internet and takes hours, and the cost is
  that the port is then open on whatever network the box was plugged into rather than on the
  appliance segment. Refused when `$CI` is set; adds `loom-debug-bundle` to the box.
  It also makes the box a **nix remote builder** - the operator account goes into
  `nix.settings.trusted-users`, without which the daemon refuses `nix-store --serve --write` - so an
  aarch64 appliance can build for an x86_64 host natively where `--allow-cross` would mean qemu (47
  minutes against hours, for a kernel). The build writes the invocation to `nix-builder` beside the
  ssh configs; `NIX_SSHOPTS=-F <dir>/ssh_config` is the part that is not guessable. Debug images run
  `nix.gc` daily with a 7-day window, because an appliance disk is sized for Loom and a full one is
  not recoverable from the console.
  Read the threat-model section in `Documentation/appliance.md` before using it
- `build-appliance-image --lock-key` - Put the stick's 4096 LUKS key bytes inside a LUKS2 container
  on the same `loom-key` partition, under a generated word passphrase (`diceware`, EFF list) that is
  printed once and stored nowhere else. The stick stops being a bearer token - holding it is no
  longer enough - which is the one assumption `Documentation/appliance.md`'s threat model otherwise
  has to make. It costs unattended boot: stage 1 stops at a prompt, so the box does not come back on
  its own after a power cut, and the installer refuses to run unattended (`decision.py`'s
  `KEY_LOCKED`). The recovery passphrase is deliberately unchanged and remains a single-factor way
  in. Stage 1 asks three times (`loom.keyStore.attempts`, matching the installer's
  `PASSPHRASE_ATTEMPTS`), echoes what it is given, folds the count into the next prompt because the
  splash hides anything else, and offers a blank answer on the last try as the way to the recovery
  passphrase - falling into that prompt silently is what made a mistyped passphrase unreadable.
  Failures retyping cannot fix (not a container, busy, out of memory for argon2id) are named on the
  spot and do not burn a try. Related flags: `--lock-key-words N` (default 7, minimum 6),
  `--lock-key-out FILE` (refused if it names the same file as `--key-backup`). Only meaningful with
  `--flash`, and `appliance-vm installer` cannot boot such an image - it writes the key partition
  with a plain `dd`. Read the `## Locking the stick's key` section in `Documentation/appliance.md`
- `build-appliance-image --require-client-cert` - Deploy Loom with mutual TLS, so reaching the
  appliance segment is no longer enough to use Loom: every route refuses a client that presents no
  certificate, and `generate-client-certificate` is what issues one. It sets
  `certificate.requireClientCert` through `loom.applianceValues` **and** gives the box's own two
  clients a way through, which is the half that cannot be left out: `opencode` (the assistant pane)
  and `mc` (USB ingest) can both be handed a CA and neither can be handed an identity, so nginx —
  already on the box for the captive portal — reverse-proxies `ollama.loom` and `s3.loom` on two
  loopback ports and attaches the certificate itself. That identity is issued **on the box**, since
  the CA lives in the cluster: `loom-mtls-identity.service` waits for the secret, runs the same
  script an operator runs, and a daily timer reissues it; `loom-mtls-placeholder.service` writes a
  throwaway certificate first so nginx starts without waiting out a bring-up and the captive portal
  is not held up. It is also the one image that **drops `up.sh --enable-http`** — a plaintext
  entrypoint beside a client-certificate requirement is either a way around it or a 404 — so the
  portal page's "Open Loom" points at https there, and a visitor is refused at the handshake until
  they hold an identity. Which they get **from that page**: this is the one image whose portal
  carries a password field, and the password is on the box's own login screen and rotates daily
  (`nixos/portal.nix`), so "stood in front of the box" becomes the authorisation for getting into
  Loom. It also gains a TLS listener on the portal address, because a PKCS#12 carries an
  unencrypted private key and the appliance segment is a wire. See the
  `## Requiring a client certificate` section in `Documentation/appliance.md`, including what the
  password does to the threat model
- `build-appliance-image --values FILE` / `--set PATH=VALUE` - Deploy the box with custom Helm
  values, so tuning a stick for the data it will index (OCR languages, pipeline limits, sizing)
  needs no flag per knob. `--values` is repeatable and merged in order; `--set` lands after it and
  reads its value as JSON where it parses as JSON. They are written into
  `charts/values-user.yaml` of the seeded checkout, which skaffold applies **before**
  `values-up-flags.yaml` - the lowest layer on purpose, so nothing here can break a decision the
  platform or an `up.sh` flag made. The box's own facts are a layer above it in
  `charts/values-appliance.yaml` (`loom.applianceValues`), and `charts/values-overwrites.yaml`
  stays the operator's last word that **nothing in `nixos/` ever writes**. Refused before the build
  starts: a path the embedded tag's `charts/values.yaml` does not carry (there is no values schema,
  so helm would take a typo in silence - `--values-allow-new-keys` for the chart's free-form maps),
  values the chart cannot render (`helm template` dry-run, `--skip-values-check`), and
  `kubernetes.api`, `hostnames` or `image.registry`, each of which something outside the chart is
  built from. See the `## Custom Helm values` section in `Documentation/appliance.md`
- `build-appliance-image --keymap NAME` - Set the console keymap for the box, the installer **and
  stage 1**, as `loadkeys` names it (`de_CH-latin1`, `fr`, `uk`). Default is the kernel's built-in US
  QWERTY, which is what every image was before this existed. It matters for the three prompts nobody
  can see themselves type: the `--lock-key` passphrase and the LUKS recovery passphrase, both in
  stage 1, and the installer's `INSTALL`/`WIPE` interlocks. Under a US map a Swiss `-` arrives as
  `/` and `y`/`z` swap, so a generated passphrase was mistyped on QWERTZ hardware every time - hence
  also the `.` separator and the y/z-free wordlist, which make a default stick typeable on QWERTZ
  with no flag at all. AZERTY still needs this. A name that does not resolve fails the image build
  with a list of valid ones, rather than falling back to US on the box. See the
  `## Keyboard layout` section in `Documentation/appliance.md`
- `appliance-test` - Run the NixOS appliance tests (`nixos/tests/`). Takes any of `hardware`,
  `units`, `skills`, `appliance`, `install`, `dhcp`, `portal`, `wifi`, `mouse`, `usb-ingest`,
  `interface-fallback`, `key-store`, `debug`;
  with no argument it runs all of them, cheapest first. Defaults to the platform matching the host architecture — the VM tests boot
  a real kernel, so they cannot be cross-built. `--gc` collects garbage afterwards and
  `--min-free GB` sets how much space nix should free mid-build; see the disk budget section in
  `nixos/README.md`
- `appliance-test hardware units skills` - The three tests that boot nothing.
  `hardware` asserts what `nixos-hardware` gives each platform and that the Loom overrides still take
  the desktop userspace back off; `units` asserts the unit edges that put the appliance address on
  the interface before dnsmasq and nginx bind it — `network.target` does not imply a static address
  under this nixpkgs pin, and the default build once shipped with dnsmasq racing it; `skills`
  asserts what the assistant pane was given to read — that a GPU platform got skills and `nuc12` got
  none, that their frontmatter is what opencode will actually register, and that every `loom-*`
  command they name is one that image carries. None needs KVM, and `units` and `skills` build
  the `--wifi` configuration themselves so they cover a build a given machine may not be able to
  boot. `hardware units --platform all` checks those two for all three platforms from one machine in
  seconds; **`skills` cannot take `--platform all`** on a foreign architecture, because the skills
  directory and the instructions file it inspects are store paths of the *platform's* own nixpkgs,
  so an x86_64 host asking about the Spark gets a platform mismatch rather than a verdict — run it
  without `--platform`, which picks the platform matching the host. Run `hardware` after every
  renovate bump of the `nixos-hardware` pin, `units` after one of
  `nixpkgs-stable`, and `skills` after an `opencode` bump — its discovery rules and the frontmatter
  it accepts are undocumented and have changed between releases. `all` is refused for any selection
  that includes a VM test
- `appliance-test portal` - The captive portal page on a booted `--require-client-cert` box with no
  cluster behind it, which is the state every box is in for its first hours - and the one image
  nothing else boots. It is the only test that **sends** a probe rather than reading the decision
  about one off a configuration: which nginx server block answers is taken from two `server_name`
  values and a `default_server` flag together, and getting it wrong means every probe path answers
  200, Android stops offering "Sign in to network", and a phone silently falls back to mobile data.
  Also the daily password, the spool's permissions and that nginx started at all
- `appliance-test dhcp` - The default (non-`--wifi`) build actually serving DHCP on `loom0`. The
  only VM test where dnsmasq runs on a renamed physical port rather than on a bridge the
  configuration creates, which is the combination that shipped broken; the interface fallback
  renames the NIC during boot, so the start-ordering race is reproduced rather than simulated
- `appliance-test --no-kvm` - Build the VM tests without the `kvm` system feature, so qemu falls
  back to software emulation — correct, and five to ten times slower. With neither this nor
  `--kvm` (which fails rather than taking the slow path) the script probes `/dev/kvm` and says
  which way it went. This is what lets the tests run on a CI runner with no nested virtualisation
- `appliance-vm box` - Boot the appliance in a VM for manual testing. Fast (a minute, no tag, no
  image build) and shows everything above the disk: the console session, the branding, the units,
  the banner. Not the bootloader, the LUKS root or the installer — nixpkgs' qemu-vm module
  overrides those away. Opens a window and exposes a serial socket
- `appliance-vm box --debug` - The same VM built with `--debug`'s sshd, forwarding `localhost:2222`
  to the guest's port 22. The keypair lives in the VM's state directory rather than `/tmp`, so it is
  the same key across runs and `appliance-vm reset` deletes it with the disks. The cheapest way to
  try debug access, and the way to point an agent at an appliance with no hardware. `box` only
- `appliance-vm installer` - The real stick image, virtually flashed onto a file and booted under
  UEFI against emulated NVMe. Runs the actual installer onto an actual pool, reboots into what it
  installed, and persists across runs. Needs a tag, since the image embeds a tagged checkout — the
  newest release by default, or `--include-rc` to let a `-rcN` win, or `--tag` to name one.
  `--serial` adds a getty on ttyS0 so the VM can be driven from a terminal that copies and pastes —
  one unit more than a real stick carries, so it refuses to be flashed. Related flags: `--disks`,
  `--disk-size`, `--usb DIR`, `--memory`, `--cores`, `--no-gui`, `--force`
- `appliance-vm attach` - Connect to a running VM's serial port. Lands in the same tmux session
  tty1 is showing, as the only client
- `appliance-vm reset` - Delete a platform's VM state (`.appliance-vm/<platform>/`): the disks, the
  flashed stick and the UEFI variables. Gigabytes
- `appliance-check` - The appliance checks that boot nothing, in about a minute: `appliance-pytest`
  then `appliance-eval`, both of them below. Runs both even when the first fails. Needs neither KVM
  nor a matching architecture, which is why this is the appliance job that runs on every CI pipeline
  while the VM tests are gated on what the MR touched
- `appliance-pytest` - The appliance's own pytest suites: `nixos/installer/tests`,
  `nixos/ready/tests`, `nixos/portal/tests`, `nixos/usb-ingest/tests`,
  `nixos/console-mouse/tests`, `nixos/tests/scripts/tests` (the VM tests' own helpers) and
  `nixos/skills/tests`. Each also runs
  in its package's `checkPhase`, so a mistake fails an image build too; running them here needs
  nothing built. `nixos/skills/tests` is the exception and runs here alone: it checks the assistant
  pane's skills against the headings they cite in `Documentation/`, and no derivation's `src` holds
  both. The half that has to fail an image build is `nixos/tests/appliance-skills.nix` instead.
  Extra arguments go to pytest
- `appliance-eval` - Instantiates the stick image for all three platforms — six times each: plain,
  `--debug`, `--lock-key`, `--require-client-cert`, `--values` and `--keymap`, since
  `nixos/debug.nix`, `nixos/key-store.nix`, `nixos/mtls.nix` and `repo.nix`'s user values layer are
  inert otherwise and would rot unevaluated — and the
  tests for this one, building nothing. Catches a module that no longer evaluates, a renamed option, a failed
  assertion and a typo in a test file. `--platform` (repeatable), `--verbose`
- `loom-platform-info` - Report this box's hardware — wired ports with their drivers, PCI ids and
  multi-port ids, radios and whether they do AP mode, GPU with the firmware VRAM carve-out beside
  the GTT pool, whether the GPU reaches a container (CDI specs, `nvidia-ctk`, docker runtimes),
  CPU frequency driver, firmware version with any pending `fwupd` update, and Secure Boot / Setup
  Mode read from the EFI variables — and, on an appliance, how that compares with what
  `nixos/platforms/<id>.nix` declared. Plain bash with no Nix dependency
  (`nixos/scripts/platform_info.sh`), so it also runs on a box that is not running Loom yet — a
  DGX Spark still on DGX OS included, which is where its firmware and Secure Boot checks have to
  happen. This is how the guessed values in a platform file get checked against real hardware.
  `--json` (everything but the `fwupd` block, which shells out to a daemon), `--output`
- `build-ingest-test-stick --device /dev/disk/by-id/usb-...` - Prepare any USB stick of 4 GiB or
  more as a USB-ingest test fixture: 26 partitions, one filesystem each, so that plugging it into an
  appliance takes every branch of `nixos/usb-ingest`'s `plan_mount` at once — the sixteen `KNOWN`
  types, the six `REFUSED` signatures, three tier-3 candidates and a deliberately blank partition —
  with `integrationtest/assets` on every mountable one. Nothing about the device is baked in: the
  table is a fixed 2976 MiB whatever the capacity, so any stick gives the identical layout and the
  remainder is left unallocated. **Destructive, and runs under sudo**; `sudo` resets `PATH`, so
  invoke it as `sudo "$(command -v build-ingest-test-stick)"`. Prints the plan and writes nothing
  until `--i-know-this-erases <serial>` repeats the serial it printed, and refuses outright anything
  that is not a `by-id` USB whole disk, is mounted, or carries `/`, `/boot` or `/nix/store`. It does
  not inspect what is already on the stick — a retired Loom key or installer stick is a valid
  fixture, and the serial is the authorisation. Related flags: `--only N[,N...]` / `--skip N[,N...]` (reformat some rows
  without re-cutting the table), `--assets DIR`, `--keep-work`. See the ingest test stick section in
  `nixos/README.md`, which also records the three bugs building it turned up

**Utilities:**

- `./cicd/setup_devenv.py` - Interactive first-time setup of a development machine: Nix, the binary
  caches, devenv, direnv, docker, and `direnv allow` on the checkout. Run directly, not through
  devenv — it is what installs devenv, so it is stdlib-only Python with no Nix dependency. Each
  step prints what it is for and the literal command before asking, and a bare Enter declines;
  anything already in place is reported as done rather than asked about again, so re-running it
  doubles as a way to check a machine. `--dry-run`, `--yes`, `--only STEP`, `--skip STEP`.
  The `caches` step is the one that matters: it writes `extra-substituters` and
  `extra-trusted-public-keys` into `/etc/nix/nix.conf` between managed markers, which is what
  makes the Loom cache reachable **without anyone being in `trusted-users`** — a client may name a
  substituter when either it is trusted or the daemon already names the cache, and only the second
  avoids handing out what the nix manual calls the equivalent of root. On NixOS that file is
  generated, so the step turns into a `configuration.nix` snippet to paste instead of a write.
  `--only verify` on its own answers "does this machine actually have the caches?"
- `poetry-lock` - Regenerate all Poetry lockfiles (run after adding dependencies to `common`).
  Discovers projects by walking every tracked `pyproject.toml`, so a newly added package is locked
  without editing a list — `backend/common` first, the root project last, the rest in between.
  This covers every appliance package under `nixos/` as well; see the lockfile section in
  `nixos/README.md` for why their locks do not govern what an image ships
- `generate-openapi-schema` - Print OpenAPI schema JSON
- `generate-client-certificate --name NAME --out-dir DIR` - Issue a client identity for the mutual
  TLS that `certificate.requireClientCert` switches on, signing it against the CA the chart's
  pre-install hook puts in the `self-signed-mtls-cert` secret. Writes four things plus a `README.txt`:
  `NAME.p12` (certificate and key, **no password**, for a browser), `NAME.crt` and `NAME.key` (the
  same pair as PEM, for `curl --cert/--key`, `mc`, nginx), and `loom-server-ca.pem` — which is the
  separate half that matters. **A PKCS#12 bundle carries certificates, not trust**: a CA put inside
  one is stored, handed back by `-cacerts`, and granted nothing by any browser or system store, so
  importing the `.p12` does not stop the `*.loom` certificate warning. The anchor is a file of its
  own with a deliberate per-OS install step, and it is `self-signed-cert` — the certificate Traefik
  serves — not the mTLS CA. Refuses to issue a certificate that would outlive its issuer: the
  pre-install Job replaces that CA within 30 days of expiry and the replacement verifies nothing the
  old one signed, so the usable life ends a month before the date on the CA. Other flags: `--days N`
  (default 60), `--namespace`, `--force`, and `--legacy-pbe` for importers that reject OpenSSL 3's
  AES-256 PKCS#12 outright. See the mutual TLS section in `Documentation/installation.md`
- `chrome-loom-wrapped [SERVER [HTTP_PORT [HTTPS_PORT]]]` - Open the frontend in a chromium that
  resolves every `*.loom` name to `SERVER` via `--host-rules`, so a remote Loom needs no `/etc/hosts`
  entry. With no arguments it points at `127.0.0.1:8080`/`8443`, the pair `appliance-vm` forwards;
  with a server named, at its `80`/`443`. The two ports are mapped **separately and must be given as
  a pair** - a single catch-all rule rewrites the port as well as the host, so it sends the `https`
  that every ingress redirects to (all of them are on Traefik's `websecure` entrypoint; only
  `charts/values-http.yaml` widens that to `web`, which `up --enable-http` applies — as does
  `up -d` and `up --integrationtest` implicitly) back at the http port, where Traefik answers 404 on
  a perfectly healthy stack. Expect one self-signed certificate interstitial
- `generate-third-party` - Regenerate `THIRD-PARTY.md`, its `Frontend/public/` copy and
  `THIRD-PARTY.lock`. A section is a syft scan of an image's *package inventory*, so the lock keys
  it on the inputs that can change that inventory and on nothing else: the image's Dockerfile
  (where every `FROM` pins its base by digest, and the apt, apk, plugin and model versions are
  pinned too), the build arguments its Skaffold configuration declares, and whatever
  `cicd/third_party_inputs.yaml` adds for it - dependency lockfiles and installer scripts. A
  section is reused byte-for-byte while that key is unchanged, so a change to application source,
  configuration or documentation scans nothing, builds nothing and leaves the lock alone.
  **The generated file must depend on the repository alone** - it is committed by CI, and a
  generator that answers differently on two runners pushes a commit per pipeline forever, which is
  why build arguments are hashed as written rather than as resolved (`DOCKER_REGISTRY` expands to a
  dependency-proxy prefix in CI and to `docker.io` elsewhere). **Adding an image, or a `COPY` that
  installs something, means declaring it in `cicd/third_party_inputs.yaml`** - the tests in
  `cicd/tests/test_third_party_inputs.py` fail until every image has an entry and every `COPY`
  source is either keyed or listed as `not_keyed`, because the alternative fails silently: a
  licence document that no longer describes what the image ships. Pass `--refresh` to rescan every
  image regardless of the lock, which is the only way to notice inventories no file hash can track
  - `roundcube` composer-requires its plugins at build time with no lockfile, `alpine` uses `~=`
  apk pins, `worker` and `tika` use apt version wildcards, and `ollama-models` pulls mutable model
  tags.
  **All three files are merged by keeping the copy of the branch being merged into**, through the
  `keep-ours` driver `.gitattributes` names and `cicd/set_generated_file_merge_driver.sh`
  configures on devenv entry. A pipeline commits them on every branch, so two branches that have
  each run one differ in files nobody edited, and both sides are right for the branch that
  produced them - there is nothing to review in that conflict. The next pipeline recomputes the
  keys, rescans whatever the merge actually changed and commits the correction, which is what
  resolving by hand was doing anyway. A checkout that has never entered devenv has no such driver
  and conflicts the way it always did
- `cicd/check_chart_hostnames.sh` - Assert that `hostnames.ingress` in `charts/values.yaml` is
  exactly the set of hosts the chart routes by name - `spec.rules[].host` on an Ingress and
  HostSNI(`<name>.<domain>`) on an IngressRouteTCP - and that each Ingress's `spec.tls[].hosts` is a
  subset of its own rules. Runs as a git hook on any change under `charts/`, to the checker itself or
  to `vars.sh`, and needs no cluster (`helm template` is client-side). **Adding a service with an
  Ingress means adding its name to `hostnames.ingress`** - that list is what the pre-install Job puts
  in the TLS certificate's `subjectAltName` and what `charts/templates/common/certificate.yaml`
  renders into `dnsNames`, one entry per host, and a wildcard cannot stand in for it (`*.loom` has
  one dot, and OpenSSL will not expand a wildcard under a single-label parent). A host served by
  entrypoint rather than by a route that names it goes in `hostnames.extra` instead. See the
  `## Hostnames and the self-signed certificate` section in `Documentation/installation.md`

**AI developer tools (`aitools` subcommands):**

- `aitools mr-review [<MR URL or IID>] [--fix]` - Run a multi-agent AI review of an MR and
  post findings as inline GitLab comments; omit the MR argument to auto-detect the MR for
  the current branch; pass `--fix` to auto-apply findings instead of posting them as comments
- `aitools mr-watch [<MR URL or IID>]` - Watch an MR's pipeline and auto-fix CI failures
- `aitools mr-fix [<MR URL or IID>]` - Address unresolved MR review comments using Claude
  in agentic mode; omit the argument to fix the MR for the current branch
- `aitools mr-create` / `mr-describe` / `mr-update` - MR lifecycle helpers
- `aitools job-diagnose <job-id>` - Diagnose a specific CI job failure
- All `aitools` subcommands operate on the branch of the *current* working tree, checking it out
  in place - run them from your worktree, never from the user's primary checkout

## Development Workflow

### Making Code Changes

**Backend (Python):**

- Code is organized by domain in each package's subdirectory
- All Python uses **Poetry** for dependency management
- When adding dependencies to `common`, run `poetry add <package>` in `backend/common/`, then `poetry-lock` to update all dependent packages
- Tests use pytest with fixtures; configuration in `pytest.ini`
- Type hints enforced via mypy
- Code style: black (formatter), isort (import sorting), autoflake (unused imports)
- Pre-commit hooks auto-format on commit

**Frontend (TypeScript):**

- Use `cd Frontend && pnpm <command>` or run via corepack
- API types regenerated with `generate-frontend-api` - don't manually edit `src/app/api/generated/`
- ESLint requires staged files (uses `git ls-files`), so stage deletions/renames before committing
- Changes auto-reload when `up --development` is running

### Testing

**When to write tests:**

- Before adding a test, ask yourself: will this test actually test critical functionality, and will
  it add real value? Since we have types, tests that merely verify type constraints or trivially
  re-test what types already enforce are not valuable. Focus on behaviour, edge cases, and logic
  that types cannot capture.
- All new backend features require unit tests
- Integration tests for user-facing workflows

**Running tests:**

- Backend unit tests: `backend-test` (runs all tests in `backend/*/tests/`)
- Frontend unit tests: `frontend-test`
- `aitools` unit tests: `aitools-test` (runs all tests in `cicd/aitools/tests/` and
  `cicd/tests/`, the latter covering the scripts at the root of `cicd/`) — always from
  `cicd/`, not from `cicd/aitools/`, where the `aitools.py` module shadows the `aitools` package
  and every import fails
- Integration tests: `run-integrationtest` — simulates full workflows against a running Loom instance
- Tests create temp artifacts in `.pytest_tmp` (not `/tmp`) to avoid RAM usage
- CI/CD pipeline runs the full test suite and linting via git-hooks

**Integration test design — class vs. no class:**

The `wipe_data` fixture in `conftest.py` is `scope="class"` and `autouse=True`. It purges all
queues, terminates running Celery tasks, and waits for the worker to be idle before the test runs.
The scope controls how often that cleanup happens:

- **No class (module-level functions):** `wipe_data` runs before *every* test function. Use this
  when each test needs a clean slate — e.g. it uploads files, dispatches tasks, or calls anything
  that leaves queues non-empty or state dirty for subsequent tests.
- **Class:** `wipe_data` runs once before the first test in the class, then the class shares that
  state. Use a class only when tests genuinely share a common dataset and none of them contaminate
  state for the others (e.g. a read-only search test suite that loads a fixed corpus once).

**Key rule:** if a test uploads a file, triggers a Celery pipeline, or leaves RabbitMQ queues
non-empty, it must not share a class with tests that depend on an idle worker — particularly any
test that calls a task which internally calls `wait_for_idle`. When in doubt, use module-level
functions (no class).

**When to use `disable_periodic_tasks`:**

Apply `pytestmark = pytest.mark.usefixtures("disable_periodic_tasks")` (or the fixture directly)
when periodic beat tasks would interfere with what the test is asserting. Specifically:

- The test calls a task that uses `wait_for_idle` — beat tasks continuously add messages to queues,
  which prevents `wait_for_idle` from ever returning `True`.
- The test inspects queue depths, task counts, or file storage contents and needs a stable
  background with no surprise writes or deletions from periodic jobs.
- The test is sensitive to the `flush_file_storage_service_task` or similar maintenance tasks
  removing objects the test just created.

You do **not** need it for tests that simply upload a file and wait for it to be indexed — those
are not affected by periodic tasks running in the background.

**Monkey patching:**

Avoid monkey patching (`monkeypatch`, `unittest.mock.patch`, etc.) by default. Patching replaces
things at runtime behind the code's back, which couples tests to implementation details.
Using `MagicMock` or other test doubles is fine — the issue is *how* they reach the code under
test: pass them in via dependency injection rather than patching them into place.

Before reaching for a patch, ask yourself:

- **Is this test actually valuable?** If the only way to test something is to patch out most of its
  internals, the test may be asserting implementation details rather than behaviour.
- **Can the code be restructured for better testability?** Prefer dependency injection, small
  focused functions, and clear boundaries so that test doubles can be passed in directly.

Only patch when there is no reasonable alternative (e.g. a global external side effect that cannot
be injected). If you find yourself patching, treat it as a signal to reconsider the design first.

**Retry classification:**

A Celery task's `autoretry_for` must name exactly the exception the code below it raises for a
*transient* failure — nothing wider, nothing narrower. Getting it wrong is silent in both
directions: too narrow and a service outage is treated as a property of the document, too wide and
a deterministic failure occupies a worker for the whole backoff budget (with `retry_backoff=True`
and `max_retries=15`, roughly an hour, multiplied by the chunk count of every affected document).

- **The service layer classifies**, because it is the only layer that sees the status code. It
  raises a distinct type per outcome under one base — see `TikaTransientError` /
  `TikaPermanentError` in `worker/services/tika_service.py`, and the matching pairs in
  `rspamd_service.py` and `common/llm/exceptions.py`. A service that wraps an exception
  (`raise XError from exc`) has to be checked against what the task declares: `TikaError` wrapping
  `requests.HTTPError` while the task declared `RequestException` is what made every Tika 5xx
  degrade a PDF to the strings extractor without a single retry.
- **Classify from what the service actually reports, not from the status class.** The default for
  an unrecognised failure is transient, because a wasted retry budget is cheaper than silently
  discarding work that would have succeeded — but check each 5xx before assuming it. Gotenberg
  answers `500` on a document's own route when LibreOffice cannot open the file, so there it is a
  verdict and only `503`/`502`/`429`/`408` are worth retrying; Tika answers `5xx` when its forked
  parser was killed and keeps refusals to `4xx`, so there the whole `5xx` range is transient.
  Misreading a verdict as transient is not a wasted budget — it holds the file out of the index for
  the entire backoff before degrading to the same answer.
- **The task decides degrade-vs-fail with `BaseTask.is_last_attempt`**, never by comparing
  `self.request.retries` against the limit by hand.
- **A task that degrades logs a warning.** Degrading silently is why the Tika defect went unnoticed
  for so long: the only trace it left was `tika_handled_by` on the indexed document.

### Issue and Merge Request Templates

Both templates are tracked in this repo. **Read the file at the moment you write the issue or MR
description** — do not reproduce its structure from memory, it changes.

**Issues** → `.gitlab/issue_templates/Default.md`. One combined form for bug reports and feature
requests: tick exactly one `📝 Issue Type` box (`[ ]` → `[x]`), fill the section matching that
type, and delete the section that does not apply along with the `<!-- -->` hint comments. Keep the
headings and their emoji verbatim — they are what makes issues scannable.

**Merge requests** → `.gitlab/merge_request_templates/Default.md`. `# 📌 Summary` gets a short
paragraph followed by `Added:` / `Changed:` / `Removed:` / `Fixed:` bullet lists; `## 🔗 Issue
Reference` gets `Closes #<issue-number>`.

**The MR title and description are not commentary about the change — they become the title and
message of the squashed commit on `main`.** Write both as the commit message you want in the
history, and nothing else.

That has two consequences, and both are gotten wrong by default:

- **The title is a conventional commit subject**, `type(scope): description`, max 72 characters,
  lowercase after the colon, describing *what* changed — exactly the rule in `### Git Commit
  Format` below, because it ends up being that commit's subject. Use the same types the history
  uses: `feat`, `fix`, `refactor`, `docs`, `chore`, with the scope naming the area
  (`feat(api): serve chart metadata from the cluster on /v1/about`,
  `fix(worker): retry on the exceptions services actually raise`). A sentence-style title like
  "Add X and port Y to Python" is wrong, however descriptive it reads.
- **The description contains the template's headings and nothing else.** Do not add sections of
  your own — no "Notes for review", "Testing", "Background", "Implementation notes", no trailing
  summary of what you did. Anything extra becomes permanent commit message on `main`. Review
  commentary belongs in an MR *comment*, which is not part of the commit.

The `%{...}` placeholder under the Summary heading is a GitLab expansion variable that only fires
when an MR is created through the **web UI**. Sent through the REST API it stays in the
description verbatim, so replace it with the real summary text whenever you write a description
any other way.

This applies no matter how the issue or MR is created — GitLab UI, REST API, `glab`, or
`aitools mr-create` / `mr-describe` / `mr-update`.

### Documentation Check Before Committing

Before committing any implementation, review whether the changes affect user-facing behaviour,
configuration, or deployment — and if so, update the relevant documentation:

- **New Helm values files** (`charts/values-*.yaml`) → add an entry to the `## Helm Values Reference`
  section in `Documentation/installation.md`
- **New settings or configuration knobs** → check `Documentation/` for any guide that covers
  configuration and update it
- **New CLI flags, scripts, or devenv commands** → update `CLAUDE.md` (Common Commands) and any
  relevant `Documentation/` page
- **Changed defaults or behaviour** → update any doc that describes the old behaviour

If none of the documentation files need updating, proceed directly to the commit.

### Implementing Plans in a Git Worktree

Implementation work that ends in a commit belongs in a dedicated git worktree.
**Never implement directly in the primary checkout.** That checkout is where the user runs the
cluster and keeps their own branch checked out, and every `aitools` subcommand checks out branches
in the *current* working tree — running one there moves the user's branch under their feet.

- Create the issue and let GitLab's "Create Merge Request" button name the branch (see
  `### Git Workflow` below), then `git worktree add ../loom-worktrees/<branch> <branch>`
- Place worktrees **outside** the repo — there is no `.dockerignore`, so a nested worktree leaks
  into Docker build contexts, pytest collection and Skaffold watches
- Run `direnv allow` once in the new worktree; devenv files are tracked, but direnv trust is
  per directory
- `direnv allow` only marks the directory trusted — it builds nothing. **Enter the environment
  once with `direnv exec <worktree> true`**, which creates the worktree's own `.venv`, `.devenv`
  and `.pre-commit-config.yaml`, then run every command there as
  `direnv exec <worktree> <command>`. Until that happens the worktree has no environment of its
  own and inherits the primary checkout's `PATH`, so `python`, `pytest` and the linters resolve
  editable path dependencies — `aitools` among them — to the *primary checkout's* sources and
  report on code that is not the code under test
- Each checkout installs its git hooks into its own git directory — `.git/hooks` in the main
  worktree, `.git/worktrees/<name>/hooks` in a linked one — pointed there by
  `cicd/set_worktree_hooks_path.sh` before devenv installs them. The hook *set*, its excludes and
  its pinned tools therefore come from the `devenv.nix` of the tree you commit in, and deleting a
  worktree cannot break committing in the others. A worktree has no hooks of its own until devenv
  is entered in it once
- A branch cannot be checked out twice → on "already checked out", ask the user to move the
  primary checkout off that branch rather than working in place

**State that does not follow into a worktree:**

- `devenv.local.nix` → gitignored, holds `GITLAB_TOKEN`; copy it across or every `aitools` GitLab
  command fails (see `Documentation/devenv-setup.md`)
- `charts/values-overwrites.yaml`, `charts/values-up-flags.yaml` and `charts/values-user.yaml` →
  tracked but flagged `--skip-worktree` in the primary index, so a worktree silently gets the
  near-empty committed versions; copy them if local Helm overrides matter
- `.claude/settings.local.json` → untracked, so expect extra permission prompts; never edit
  settings files to silence them

**Keep cluster work in the primary checkout:** `up`, `down`, `build`, `wipe-data`,
`run-integrationtest` and all `kubernetes-*` commands. There is one cluster per machine and every
checkout talks to it — `MINIKUBE_HOME` resolves to the main worktree, matching the `~/.kube/config`
that minikube writes — so these commands do not fail in a worktree, they succeed *against the
primary checkout's running system*: `up` redeploys it from the worktree's sources, and `wipe-data`
and `kubernetes-delete` destroy it. Safe in a worktree: `backend-test`, `frontend-test`,
`frontend-build`, `generate-frontend-api`, `poetry-lock`, and all `git` and `aitools` commands.

**The appliance commands in a worktree:** `appliance-check`, `appliance-pytest`, `appliance-eval`,
`appliance-test`, `ollama-test` and `aitools-test` are safe — they read the worktree's own sources,
build nothing outside the nix store and never touch the cluster. `appliance-vm` is safe but keeps
its state in `.appliance-vm/` *of the tree it ran in*, so a worktree gets its own disks and its own
gigabytes, and `appliance-vm reset` in one does nothing for the other. `build-appliance-image` is
safe in the sense that matters here and misleading in another: it seeds the image from a **git tag**,
never from the working tree, so uncommitted worktree changes do not reach the stick however many
times it is rebuilt. `build-ingest-test-stick` ignores the checkout entirely and erases a USB
device under sudo — which worktree it is run from is the least of what to check first.

**Finishing up:** commit and push from the worktree — git config and refs are shared. Then
**take the MR out of Draft and start a pipeline for it** (see `### Finishing an MR` below), and
report the worktree path, the branch, the MR and the pipeline so the user can review the diff
there. Leave the worktree in place. **Never merge, rebase the primary checkout, or remove the
worktree on your own.** Remove one only when asked, with `git worktree remove <path>` and never
`--force`.

### Git Workflow

Per `CONTRIBUTING.md`:

- Implement in a dedicated worktree, not the primary checkout (see the section above)
- Always create an issue first, filling `.gitlab/issue_templates/Default.md` (see
  `### Issue and Merge Request Templates` above)
- Use GitLab's "Create Merge Request" button from the issue (auto-links and names branch)
- Open MR early as **Draft**, with the description following
  `.gitlab/merge_request_templates/Default.md`
- MR title is a conventional commit subject (`type(scope): description`, max 72 chars) and
  becomes the release note entry — see `### Issue and Merge Request Templates` above
- Squash merging used - individual commit messages don't matter, but the **MR title and
  description do**: they become the squashed commit on `main`. Keep the description to the
  template's headings and add no sections of your own
- Use `Closes #issue-number` under the MR description's `## 🔗 Issue Reference` heading
- Remove Draft status when the work is done, and start a pipeline yourself (see below)

### Finishing an MR

**When you are done working — the change is committed, pushed and its tests pass — undraft the
MR and start a pipeline for it.** Do both, in that order, without waiting to be asked. A Draft MR
is invisible to CI, so leaving one behind means nobody finds out whether the change builds.

Why both steps are needed, per the `workflow:rules:` in `.gitlab-ci.yml`:

- Merge request pipelines only run when the title does **not** start with `Draft`, and branch
  pipelines are skipped outright while an MR is open (`$CI_COMMIT_BRANCH && $CI_OPEN_MERGE_REQUESTS`
  → `when: never`). So **a Draft MR runs no pipeline at all**, however often you push.
- Undrafting is a title change, and a title change does not create a pipeline. Removing the
  `Draft:` prefix therefore leaves the MR with the *stale* pipeline status it already had — the
  pipeline has to be created explicitly.

Undraft by stripping the `Draft:` prefix from the title (`mr.title`, then `mr.save()`), then
create the pipeline with `mr.pipelines.create()` — the MR-pipelines endpoint, not
`project.pipelines.create()`, whose branch pipeline the rules above discard. Afterwards
`aitools mr-watch` follows that pipeline and fixes what fails.

**When the MR stops tracking its branch, close and reopen it.** GitLab sometimes leaves an MR
stuck on an old head commit, and everything downstream then misbehaves:
`mr.pipelines.create()` answers **405** while `mr.detailed_merge_status` is `preparing`, `mr.sha`
keeps reporting a commit the branch has long moved past, and `generate_frontend_static` fails on
purpose rather than run CI on what it sees as a stale commit. Pushing again does not clear it.
Closing and reopening the MR (`state_event`) does, within seconds: the status becomes `unchecked`,
`mr.sha` catches up with the branch, and the pipeline can be created. Compare `mr.sha` against
`project.branches.get(<branch>).commit` to tell this apart from a real failure.

Keep the MR in Draft only while it is deliberately unfinished — an MR opened early for discussion
before the work exists, or one the user asked you to leave alone.

### Git Commit Format

- First line: conventional commit format — `type(scope): description`, max 72 characters
- Blank line after the title
- Body in markdown (headers with `#`, bullet points with `-`)
- Describe **what** changed, not why
- Do **not** add `Co-Authored-By` or any self-referencing author trailer

### Debugging

- Check pod logs: `kubectl logs <pod-name> -n loom`
- Or dump all logs: `kubernetes-fetch-all-pod-logs`
- RabbitMQ UI shows queue depths and message routing

**Attaching a debugger.** `up --development` runs `skaffold dev` and forwards exactly the ports
listed under `portForward` in the `dev` profile of `skaffold.yaml` — nothing is discovered
automatically. Each one matches an attach configuration in `.vscode/launch.json`, so the two lists
have to be changed together:

| Component | Port | Listener declared in |
| --------- | ---- | -------------------- |
| api | 4401 | `backend/api/Dockerfile` (dev stage `CMD`) |
| worker | 5500 | `charts/values-development.yaml` (`worker.command`) |
| reaper | 5501 | `charts/values-development.yaml` (`reaper.command`) |
| persister | 5502 | `charts/values-development.yaml` (`persister.command`) |
| beat | 5503 | `charts/values-development.yaml` (`beat.command`) |
| crawler | 6601 | `backend/crawler/Dockerfile` (dev stage `CMD`) |

Two things to know when a debugger will not attach:

- **`localPort` is a request, not a reservation.** If anything already holds 4401 — a leftover
  `kubectl port-forward` from a previous run is the usual culprit — skaffold forwards on the next
  free port instead and says so. Read its `Port forwarding ... -> 127.0.0.1:<port>` lines rather
  than assuming the configured port.
- **Only one pod per workload is forwarded.** Scale a component past one replica (`replicaCount`,
  HPA or KEDA) and the other replicas have no forward at all.

A pod paused on a breakpoint would normally be restarted by its probes;
`charts/values-debug-probes.yaml` prevents that and is applied automatically by `--development`.

## Important Technical Details

### Python Package Dependencies

The overarching `pyproject.toml` at repo root is dev-only and references all backend packages as path
dependencies. This enables IDE tooling (Pylance) to see across packages.

Each backend package has its own `pyproject.toml` and `poetry.lock`. After changing `common` dependencies,
you **must** run `poetry-lock` to update all lockfiles.

Editing the root `pyproject.toml` stales **two** lockfiles, not one: `integrationtest` takes the root
project as a path dependency (`loom-overarching-dev = {path = "../"}`), so its lock carries the root
manifest too. The `poetry-check_root` and `poetry-check_root-integrationtest` git hooks check one project each,
both firing on the root manifest, and fail the commit if either has drifted — `poetry-lock` is the
fix. A stale lock is not cosmetic: `poetry install` refuses to run against one, so
committing it breaks `devenv` for everyone until it is regenerated.

### File Processing Pipeline

1. Files uploaded to SeaweedFS bucket (via S3 API)
2. Crawler detects and schedules processing
3. Worker tasks (Celery):
    - Extract content via Tika
    - Perform OCR on images/PDFs
    - Extract metadata
    - Index in Elasticsearch
4. Frontend queries Elasticsearch via API

### Deployment Customization

Override Helm values in `charts/values-overwrites.yaml` (empty by default, automatically included by Skaffold).

## Code Style and Conventions

**Always ask the user before:**

- Adding linter-disabling rules (e.g. `# noqa`, `# type: ignore`, `# pylint: disable`, `# flake8: noqa`)

**NEVER put imports inside functions.** All imports must be at the top of the file. This is a hard rule
with almost no exceptions. Putting an import inside a function hides dependencies, makes code harder to
read and refactor, and is never necessary for normal code. If you think you need an import inside a
function, **stop and ask the user first** — there is almost certainly a better way.

- Python: Follow PEP 8, enforced by black + flake8 + pylint
- Use type hints everywhere (mypy enforced)
- **EXTREMELY IMPORTANT: Never use `dict`, `tuple`, or other generic collection types as function
  return types — not even for private helpers.** Always define and use a proper named type (Pydantic
  model, dataclass, `TypedDict`, or `NamedTuple`). Define a new type if one does not already exist.
  Raw `tuple[str, str]`, `tuple[X, Y]`, etc. are forbidden as return types. Callers should not need
  to remember what position 0 or 1 means — use a named type with descriptive field names instead.
- Pydantic models for validation and serialization
- **`cicd/` is a linted Python root like any backend package.** Its scripts go through black,
  isort, autoflake, docformatter, flake8, pylint and mypy, with mypy configured by
  `cicd/mypy.ini` because mypy reads its settings from the directory a tool runs in. Tests for
  them live in `cicd/tests/`. `cicd/aitools` is a root nested inside it; `nestedSubdirExcludes`
  in `devenv.nix` keeps each file linted by the innermost root that contains it, so adding a
  python root under another one needs no further wiring. A long shell script in `cicd/` is
  better rewritten in Python than grown - the tools above only cover the Python
- Repository pattern for data access (see `common/models/`)
- Dependency injection via FastAPI dependencies and Celery task context
- Async/await where appropriate (FastAPI routes)
- **Helm: a container's shell script belongs in `charts/files/<component>/*.sh`, not inline in the
  template.** Anything past a couple of lines is a file mounted through a ConfigMap - see
  `charts/templates/pre-install/` for the pattern (a short `until nc -vz ...; do sleep 2; done` wait
  loop can stay inline). A script inlined into a template is a YAML string that shellcheck never
  sees, and the repo runs shellcheck with `-o all`. Values reach the script through the container's
  `args:` as long options, and the script parses them in a `while`/`case` loop and asserts each one
  is set

## Additional Documentation

- `Documentation/devenv-setup.md` - Development environment setup
- `Documentation/appliance.md` - NixOS appliance image and air-gapped deployment
- `nixos/README.md` - The appliance Nix code and how to build/test it
- `Documentation/performance.md` - Finding out what is slow
- `Documentation/frontend-debugging.md` - Driving the running frontend with Playwright, which is
  a devDependency of `Frontend/` for this purpose. Covers getting past the guided tour, the data
  attributes to select on, and CDP profiling. **Debug scripts go in a scratch directory, never
  in the repository** - they are not tests, nothing runs them, and they rot in place; port what
  you learn to a vitest test instead
- `CONTRIBUTING.md` - Full Git workflow and collaboration guidelines
- `README.md` - Project overview and features
