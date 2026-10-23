# shellcheck shell=bash
#
# The body of `loom-debug-bundle`, which collects everything about a stuck
# box into one directory an operator can copy off over the `--debug` sshd.
# nixos/debug.nix reads this file into the writeShellApplication of the same
# name, behind a prologue of `LOOM_*` assignments.
#
# A file rather than a string in that module, so `shellcheck -x -o all`
# covers it: writeShellApplication runs shellcheck at build time, but with
# nixpkgs' default options rather than the ones this repository holds its .sh
# files to.
#
# `set -euo pipefail` restates what writeShellApplication already applies, so
# the linter reads the program that actually runs.
set -euo pipefail

readonly NAMESPACE="${LOOM_NAMESPACE:?nixos/debug.nix must set this}"
readonly PLATFORM_INFO="${LOOM_PLATFORM_INFO:?nixos/debug.nix must set this}"

stamp="$(date +%Y%m%dT%H%M%S)"
out="/tmp/loom-debug-${stamp}.tar.gz"
dir="$(mktemp --directory)"
trap 'rm --recursive --force "$dir"' EXIT
root="${dir}/loom-debug-${stamp}"
mkdir --parents "${root}"

echo "[*] Collecting. Nothing here is fatal -- a section that could not be"
echo "[*] read is an empty file rather than a missing bundle."

# --no-pager everywhere: this runs unattended over ssh as often as not,
# and a pager waiting for a keypress on a closed stdout is a hang.
journalctl --no-pager --boot >"${root}/journal-this-boot.txt" 2>&1 || true
# The previous boot as well, which is the only copy of why a box that is
# now up went down. Absent on the first boot after an install; the
# redirection captures journalctl saying so.
journalctl --no-pager --boot=-1 >"${root}/journal-previous-boot.txt" 2>&1 || true
systemctl --no-pager list-units --all >"${root}/units.txt" 2>&1 || true
systemctl --no-pager list-units --failed >"${root}/units-failed.txt" 2>&1 || true
systemctl --no-pager status loom.service >"${root}/loom-service.txt" 2>&1 || true

# What the box is, as the box sees it -- against what platforms/<id>.nix
# claimed. See the option below for why this is reached by store path.
"${PLATFORM_INFO}" >"${root}/platform-info.txt" 2>&1 || true

# The login screen, verbatim. It carries the readiness line, the key
# guard state and the recovery passphrase, so it answers three questions
# at once -- and it is the one thing a remote session cannot look at.
cp --recursive /run/issue.d "${root}/issue.d" 2>/dev/null || true
cat /etc/loom/network.conf >"${root}/network.conf" 2>&1 || true
ip addr >"${root}/ip-addr.txt" 2>&1 || true

# Disk, and the store's share of it. This mode lets the box be used as a
# remote builder, which is the one thing that grows /nix/store without
# anybody deciding to -- and a full disk here is not recoverable from a
# console. `du` is deliberately not used: it would walk millions of files
# to answer a question `df` answers instantly.
{
  df --human-readable /nix /
  echo
  # `find -printf` rather than `ls`, which shellcheck refuses: one line
  # per entry whatever the name, and the top level only. `! -name '.*'`
  # drops /nix/store/.links, which is not a store path.
  echo "store paths: $(find /nix/store -mindepth 1 -maxdepth 1 ! -name '.*' -printf '\n' | wc --lines)"
  echo "(this mode enables nix.gc: daily, --delete-older-than 7d)"
} >"${root}/disk.txt" 2>&1 || true

# Where the console session lives, for anyone who wants to watch a long
# command on the box's own screen:
#   tmux -S /run/loom/tmux.sock split-window -v -l 40% '<command>'
# Its config unbinds the prefix (console.nix), so a new *window* would be
# unreachable from the box's keyboard -- split a pane instead.
ls -la /run/loom/tmux.sock >"${root}/tmux-socket.txt" 2>&1 || true

# The cluster. Every one of these is a timeout waiting to happen on a box
# where minikube never started, which is why they are last and why the
# deadline is short.
kube() { kubectl --request-timeout=20s "$@"; }
kube get nodes -o wide >"${root}/k8s-nodes.txt" 2>&1 || true
kube get all --namespace "${NAMESPACE}" \
  >"${root}/k8s-all.txt" 2>&1 || true
kube describe pods --namespace "${NAMESPACE}" \
  >"${root}/k8s-pods-describe.txt" 2>&1 || true
kube get events --namespace "${NAMESPACE}" \
  --sort-by=.lastTimestamp >"${root}/k8s-events.txt" 2>&1 || true

mkdir --parents "${root}/k8s-logs"
# `|| true` on the listing too: with no cluster this prints nothing and
# the loop body never runs, which is the correct outcome rather than an
# error. --all-containers so an init container that is the actual problem
# is not the one thing left out.
for pod in $(kube get pods --namespace "${NAMESPACE}" \
  --output=name 2>/dev/null || true); do
  name="${pod#pod/}"
  kube logs --namespace "${NAMESPACE}" \
    --tail=-1 --all-containers=true --prefix=true "${name}" \
    >"${root}/k8s-logs/${name}.txt" 2>&1 || true
done

tar --create --gzip --file "${out}" --directory "${dir}" "loom-debug-${stamp}"
chmod 0600 "${out}"

echo "[*] Wrote ${out}"
echo "[*] Pull it with: scp -F <the ssh_config the build printed> loom-appliance:${out} ."
