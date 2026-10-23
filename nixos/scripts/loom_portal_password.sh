# shellcheck shell=bash
#
# The body of `loom-portal-password`, which rotates the word password the
# captive portal asks for before it hands out a client identity, and keeps
# the previous one readable for a day so a visitor mid-handover is not
# locked out. nixos/portal.nix reads this file into the unit of the same
# name, behind a prologue of `LOOM_*` assignments.
#
# A file rather than a string in that module, because a unit `script` string
# is linted by nothing at all.
#
# `set -e` and nothing more, which is what nixpkgs' makeJobScript wraps a unit
# `script` in (nixos/lib/systemd-lib.nix). Restated so the linter reads the
# program that actually runs.
set -e

readonly STATE_DIR="${LOOM_STATE_DIR:?nixos/portal.nix must set this}"
readonly PASSWORD_FILE="${LOOM_PASSWORD_FILE:?nixos/portal.nix must set this}"
readonly PREVIOUS_PASSWORD_FILE="${LOOM_PREVIOUS_PASSWORD_FILE:?nixos/portal.nix must set this}"
readonly PORTAL_USER="${LOOM_PORTAL_USER:?nixos/portal.nix must set this}"
readonly PASSWORD_WORDS="${LOOM_PASSWORD_WORDS:?nixos/portal.nix must set this}"

state="${STATE_DIR}"

# Words rather than a random string, and drawn by `diceware` from its
# own EFF list rather than from a wordlist in this repository -- the
# same reasoning, and the same tool, as the --lock-key passphrase in
# cicd/build_appliance_image.sh.
#
# The y/z filter is kept even though the person typing this is on
# their own phone rather than on a keyboard somebody else chose. One
# box with two different rules for generating a passphrase is worse
# than one filter that is merely unnecessary here, and rejection
# sampling keeps the result uniform over what survives.
passphrase=""
for _ in $(seq 100); do
  candidate="$(diceware --no-caps --delimiter . --num "${PASSWORD_WORDS}")"
  if ! grep --quiet --extended-regexp '[yz]' <<< "${candidate}"; then
    passphrase="${candidate}"
    break
  fi
done
if [[ -z "${passphrase}" ]]; then
  echo "No passphrase without [yz] in 100 draws; diceware or its list has changed." >&2
  exit 1
fi

# Temp file, chmod, rename -- the shape key-guard.nix's `put` uses,
# so the page can never read a half-written password and refuse
# somebody who typed the right one.
put() {
  local temporary
  temporary="$(mktemp --tmpdir="${state}" .password.XXXXXX)"
  printf '%s\n' "$2" > "${temporary}"
  chgrp "${PORTAL_USER}" "${temporary}"
  chmod 640 "${temporary}"
  mv "${temporary}" "$1"
}

# Yesterday's is kept for one rotation. This runs at midnight and the
# password is read off a screen, so there is a minute every day when
# somebody is typing one the box has just replaced -- and that is the
# worst possible moment for it to refuse a correct answer.
if [[ -s "${PASSWORD_FILE}" ]]; then
  put "${PREVIOUS_PASSWORD_FILE}" \
    "$(cat "${PASSWORD_FILE}")"
fi
put "${PASSWORD_FILE}" "${passphrase}"

# And onto the login screen, which reads the file above at print time
# and puts the password in the same block as everything else somebody
# has to transcribe. Repaint, unless somebody is already logged in --
# which is what loom-banner-refresh decides, and it says so by
# exiting 1.
loom-banner-refresh || true
