# shellcheck shell=bash
#
# The build-time half of `nixos/tests/appliance-skills.nix`: the part that has
# to look at the assembled skills tree rather than at the Nix expression that
# produced it. nixos/tests/appliance-skills.nix reads this file into the
# `runCommand` that is the test, behind a prologue of `LOOM_*` assignments.
#
# Beside the test rather than in nixos/scripts/, because it is not something
# the appliance carries -- its only consumer is the derivation next to it.
#
# A file rather than a string in that module, so `shellcheck -x -o all` covers
# it. That matters more here than almost anywhere: this is a chain of `find`,
# `comm` and `grep` pipelines whose own comments record the ways it can fail
# open, in a test whose entire reason to exist is that opencode fails silently.
#
# `set -euo pipefail` restates what a stdenv builder applies (setup.sh runs
# `set -eu` and `set -o pipefail`), so the linter reads the program that runs.
set -euo pipefail

readonly skills="${LOOM_SKILLS_DIR:?appliance-skills.nix must set this}"
readonly instructions="${LOOM_INSTRUCTIONS_FILE:?appliance-skills.nix must set this}"
readonly platform="${LOOM_PLATFORM:?appliance-skills.nix must set this}"
# Newline-separated, and the one value that may legitimately be empty: a
# platform whose skills name no `loom-*` command at all.
readonly known_names="${LOOM_KNOWN_NAMES-}"


test -s "${instructions}" || {
  echo "the assistant instructions file is empty" >&2
  exit 1
}

# `**/SKILL.md` is what opencode globs a skills.paths entry with, and it is
# recursive -- so a SKILL.md anywhere below a skill's own directory would be
# registered as an extra skill nobody wrote.
found="$(cd "${skills}" && find . -name SKILL.md | sort)"
expected="$(cd "${skills}" && find . -mindepth 2 -maxdepth 2 -name SKILL.md | sort)"
if [[ "${found}" != "${expected}" ]]; then
  echo "SKILL.md files below a skill's own directory:" >&2
  comm -23 <(printf '%s\n' "${found}") <(printf '%s\n' "${expected}") >&2
  exit 1
fi
[[ -n "${found}" ]] || { echo "no skills in ${skills}" >&2; exit 1; }

# Re-checked on the assembled output rather than only on the sources, because
# the sources are a template until this image has been built: nixos/skills
# also lands in the seeded checkout, and only this copy is the one opencode
# reads.
for skill in "${skills}"/*/SKILL.md; do
  name="$(basename "$(dirname "${skill}")")"
  grep -q "^name: ${name}\$" "${skill}" \
    || { echo "${skill}: frontmatter name is not '${name}'" >&2; exit 1; }
  grep -q '^description: "' "${skill}" \
    || { echo "${skill}: description is not a quoted string" >&2; exit 1; }
done

# The generated facts, which are what the skills send the model to when the
# right answer depends on which flags this stick was built with. Two skills
# say "facts.md says whether this box requires a client certificate", and
# without that row the model cannot tell an mTLS box from a normal one and
# follows the advice for the wrong one. Checked by the row label rather than
# by the verdict, which differs per image.
facts="${skills}/loom-appliance/facts.md"
test -s "${facts}" || { echo "no facts.md in ${skills}" >&2; exit 1; }
grep -q 'require-client-cert' "${facts}" \
  || { echo "${facts}: says nothing about client certificates" >&2; exit 1; }

# Every loom-* command the skills name has to be one this image carries.
printf '%s\n' "${known_names}" > known

# No `|| true`, and the result is required to be non-empty. Any failure of
# the pipeline -- a wrong path, an empty tree, a pipefail surprise -- leaves
# `named` empty, which on its own makes `comm` find nothing missing and the
# check report success: a fail-open headline assertion, in a derivation whose
# header says its whole reason to exist is that opencode's failures are
# silent.
#
# Only where the name starts a token and is not the right-hand side of a
# `key=value`. Two things in the skills are spelled like a command and are
# not one: a workload, which is `production-loom-<component>` in full, and a
# pod label, as in `--selector app=loom-ollama`. A bare `loom-[a-z0-9-]+`
# reads `loom-crawler` out of the first and `loom-ollama` out of the second,
# then demands commands of those names, which no image has ever carried.
grep --recursive --only-matching --no-filename -E '(^|[^a-z0-9=-])loom-[a-z0-9-]+' "${skills}" \
  | sed -E 's/^[^l]+//; s/-$//' | sort --unique >named

if [[ ! -s named ]]; then
  echo "no loom-* name appears anywhere in the skills; the scan is broken" >&2
  exit 1
fi

# On its own line: `comm` exits non-zero on a --check-order violation, and
# folding that into the `if` would short-circuit to "pass" as well.
missing="$(comm -23 named <(sort --unique known))"
if [[ -n "${missing}" ]]; then
  echo "skills name loom-* things this image does not have:" >&2
  printf '  %s\n' "${missing}" >&2
  echo "" >&2
  echo "commands, units and skills ${platform} carries:" >&2
  sed 's/^/  /' known >&2
  exit 1
fi
