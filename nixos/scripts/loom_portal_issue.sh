# shellcheck shell=bash
#
# The body of `loom-portal-issue`, which turns a request the portal page left
# in the spool into a PKCS#12 bundle the visitor can download -- the one way
# into a `--require-client-cert` box that does not need an operator at a
# terminal. nixos/portal.nix reads this file into the writeShellApplication
# of the same name, behind a prologue of `LOOM_*` assignments.
#
# A file rather than a string in that module, so `shellcheck -x -o all`
# covers it: writeShellApplication runs shellcheck at build time, but with
# nixpkgs' default options rather than the ones this repository holds its .sh
# files to.
#
# `set -euo pipefail` restates what writeShellApplication already applies, so
# the linter reads the program that actually runs.
set -euo pipefail

readonly REQUESTS_DIR="${LOOM_REQUESTS_DIR:?nixos/portal.nix must set this}"
readonly BUNDLES_DIR="${LOOM_BUNDLES_DIR:?nixos/portal.nix must set this}"
readonly PORTAL_USER="${LOOM_PORTAL_USER:?nixos/portal.nix must set this}"
readonly NAMESPACE="${LOOM_NAMESPACE:?nixos/portal.nix must set this}"
readonly CA_SECRET="${LOOM_CA_SECRET:?nixos/portal.nix must set this}"
readonly VALIDITY_DAYS="${LOOM_VALIDITY_DAYS:?nixos/portal.nix must set this}"

requests="${REQUESTS_DIR}"
bundles="${BUNDLES_DIR}"
namespace="${NAMESPACE}"
ca_secret="${CA_SECRET}"
days="${VALIDITY_DAYS}"

current=""

# Written to a dot-prefixed temporary and renamed, exactly as the bundle
# directory below is, and for a sharper reason than tidiness.
#
# The page polls `bundles/<token>.error` every 100ms and unlinks it the
# instant it appears. Creating the file and *then* chgrp-ing it leaves a
# window of one fork-and-exec in which the page can take it away -- after
# which `chgrp` fails, `set -e` aborts the script, and the EXIT trap finds
# `current` still set and writes a second answer over a question already
# answered. The unit goes to `failed` on a perfectly ordinary
# "cluster not ready", a stale file is left for the next run's reap, and a
# visitor whose timing lands the other way is told the box cannot issue a
# certificate rather than that Loom is still starting.
#
# So the name the page watches for appears once, already owned and already
# readable, and nothing touches it afterwards.
refuse() {
  local temporary
  # `mktemp`, not a name derived from the token. `bundlesDir` is
  # 0730 root:loom-portal, so the portal user may create entries in it by
  # name -- and the portal generates the token itself, so it could plant
  # `bundles/.<token>.error.tmp` as a symlink before writing its request.
  # The redirect below opens O_CREAT|O_TRUNC through such a link, and the
  # chgrp and chmod follow it too: root truncating a file of the portal's
  # choosing, writing `cluster-not-ready` into it and handing it to the
  # portal group. `refuse` is reached on the ordinary cluster-not-ready
  # branch during every bring-up, so this is not an exotic path. The same
  # reasoning `put()` below already applies to the password file.
  temporary="$(mktemp --tmpdir="${bundles}" ".tmp.XXXXXXXX")"
  printf '%s\n' "$2" > "${temporary}"
  # --no-dereference for the same reason, belt to mktemp's braces.
  chgrp --no-dereference "${PORTAL_USER}" "${temporary}"
  chmod 640 "${temporary}"
  # Cleared before the rename rather than after it: once the answer is
  # visible the trap below must not write a second one, and a failure
  # between here and the rename is better served by the page's own deadline
  # than by an answer that contradicts this one.
  current=""
  mv "${temporary}" "${bundles}/$1.error"
}

# TERM as well as EXIT, because TimeoutStartSec kills with SIGTERM and the
# visitor whose request was in flight is watching a page that would
# otherwise spin until its own deadline.
cleanup() {
  if [[ -n "${current}" ]] && [[ ! -d "${bundles}/${current}" ]]; then
    refuse "${current}" issuer-failed
  fi
}
trap cleanup EXIT TERM

# Anything abandoned. The page takes its own request back when it times out
# and removes its own bundle once it has handed it over, so this only ever
# catches what a crash or a closed tab left -- but a bundle holds an
# unencrypted private key, so it is swept rather than left.
find "${requests}" -mindepth 1 -mmin +5 -delete 2>/dev/null || true
find "${bundles}" -mindepth 1 -maxdepth 1 -mmin +5 -exec rm --recursive --force {} + 2>/dev/null || true

shopt -s nullglob
for request in "${requests}"/*.req; do
  token="$(basename "${request}" .req)"

  # Validated before the name is ever joined to a path again. The page
  # generates these, so anything else in here came from something that
  # should not have been writing to this directory at all.
  if [[ "${#token}" -ne 32 ]] || [[ -n "${token//[0-9a-f]/}" ]]; then
    rm --force "${request}"
    continue
  fi

  # The glob was expanded once, and a visitor whose page times out takes
  # their own request back -- so by the time this loop reaches an entry the
  # file may be gone. Under `set -euo pipefail` the sed below would then
  # exit 2 and abort the whole run mid-batch, with `current` still empty so
  # the trap writes no answer: a spurious `loom-portal-issue` failure in
  # `systemctl --failed`, which is a primary diagnostic on this box. The
  # batch itself recovers either way -- `PathExistsGlob` re-checks the
  # moment a triggered service exits -- but the noise is worth not making.
  [[ -f "${request}" ]] || continue

  # Re-validated rather than trusted: the page checked it too, and a
  # downstream check is not a substitute for the one that decides.
  label="$(sed --quiet 's/^label=\([a-z0-9][a-z0-9-]\{0,23\}\)$/\1/p' "${request}" 2>/dev/null | head --lines=1)" || label=""

  # Consumed before any work, so a retrigger of the path unit cannot hand
  # the same request to a second run.
  rm --force "${request}"
  current="${token}"

  # Deliberately no wait loop. mtls.nix's issuer waits out a bring-up
  # because nobody is watching it; here somebody is standing at a page, and
  # "Loom is still starting" is a better answer than a spinner.
  if ! kubectl --request-timeout=5s --namespace "${namespace}" \
    get secret "${ca_secret}" >/dev/null 2>&1; then
    refuse "${token}" cluster-not-ready
    continue
  fi

  work="${bundles}/.${token}.work"
  rm --recursive --force "${work}"
  mkdir --parents "${work}"
  chmod 750 "${work}"

  # The name is built here and never taken verbatim, so the worst a label
  # can do is choose 24 lowercase characters of a filename.
  if loom-client-certificate \
    --name "${label:-visitor}-${token:0:8}" \
    --days "${days}" \
    --namespace "${namespace}" \
    --out-dir "${work}"; then
    chgrp --recursive "${PORTAL_USER}" "${work}"
    chmod --recursive g+rX "${work}"
    # The directory itself also g+w, which is what lets the page shred the
    # bundle the moment it has handed it over: removing an entry needs
    # write on the containing directory, so with r-x alone every
    # `os.unlink` in `Spool._remove_tree` fails with EACCES and the rmdir
    # then fails ENOTEMPTY -- leaving an unencrypted private key on disk
    # until another request arrives to trigger the five-minute sweep, or
    # until reboot. It grants nothing new: `bundlesDir` is 0730
    # root:loom-portal, so the page can already unlink entries there by
    # name. The files stay g+r only.
    chmod g+w "${work}"
    # A rename within one directory, so the page can never see a partial
    # bundle: either the directory is there and complete, or it is not.
    mv "${work}" "${bundles}/${token}"
    current=""
    echo "Issued a visitor certificate for ${label:-visitor}."
  else
    rm --recursive --force "${work}"
    refuse "${token}" issuer-failed
  fi
done
