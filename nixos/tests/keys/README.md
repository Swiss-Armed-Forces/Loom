# `nixos/tests/keys/` — throwaway key material for the VM tests

**Nothing in here is a secret, and nothing in here may ever become one.**

`loom-debug-test_ed25519` is a real private key, committed on purpose. It exists
because `tests/appliance-debug.nix` has to put an *authorized* key into the
appliance's closure at build time, and a closure is built before the test runs —
so the pair cannot be generated while the VM boots. nixpkgs' own
`initrd-network-ssh` test carries a committed pair for the same reason.

What it opens: a VM that exists for the length of one `nix-build`, on a host
network, with no data on it. It is never written to a stick. The real
`build-appliance-image --debug` generates a fresh pair per image and keeps the
private half out of the Nix store entirely — see `nixos/debug.nix`.

This directory is listed in `/.secretsignore` so `ripsecrets` does not stop a
commit over it. That is the whole reason it is a directory rather than a string
inside the test: the suppression is scoped to these two files, so a real secret
that lands anywhere else — `tests/appliance-debug.nix` included — is still
caught. **Do not put anything else here**, and do not widen the ignore.
