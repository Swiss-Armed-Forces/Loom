# Places the embedded Loom checkout on the appliance.
#
# The checkout cannot simply be used from /nix/store: up.sh:359 writes
# charts/values-up-flags.yaml *into* the repository, and the skaffold hooks
# (cicd/skaffold, cicd/tag_latest.sh) run from it. So the store copy is
# re-materialised into the operator's home, writable and owned by them.
{
  config,
  pkgs,
  lib,
  loomSrc,
  tag,
  loomUser,
  loomRepoDir,
  ...
}:
let
  yamlFormat = pkgs.formats.yaml { };

  overrides = config.loom.chartOverrides;
  overridesFile = yamlFormat.generate "loom-values-overwrites.yaml" overrides;

  # charts/values-overwrites.yaml is the chart's documented last word: skaffold
  # lists it after values.yaml and after the values-up-flags.yaml up.sh writes
  # (skaffold.yaml:310-312), so it wins over both. The committed copy is empty,
  # which is what makes it usable from here -- nothing is being overwritten but
  # a placeholder.
  seedOverrides =
    tmp:
    lib.optionalString (overrides != { }) ''

      # The committed file is comments and nothing else, so this replaces rather
      # than merges -- there is no second author to merge with, and appending
      # would make a second `ollama:` key the day somebody puts one there.
      # Written into the staging copy rather than the finished one, so the `mv`
      # below stays the single moment the repository appears.
      {
        cat <<'HEADER'
      # Written by the Loom appliance at first boot (nixos/repo.nix).
      #
      # These are values that are true of this box rather than of Loom, so they
      # are not in charts/ and not behind an up.sh flag. See `loom.chartOverrides`
      # in nixos/repo.nix for what may live here and why this file is the hook.
      #
      # Edits survive: this is written once, when the checkout is seeded.
      HEADER
        cat ${overridesFile}
      } > ${lib.escapeShellArg tmp}/charts/values-overwrites.yaml
      # Explicit, because the redirect inherits the unit's umask rather than the
      # mode of anything it copied.
      chmod 0644 ${lib.escapeShellArg tmp}/charts/values-overwrites.yaml
    '';
in
{
  options.loom.chartOverrides = lib.mkOption {
    type = yamlFormat.type;
    internal = true;
    default = { };
    description = ''
      Helm values the appliance forces on top of whatever up.sh assembles,
      written into `charts/values-overwrites.yaml` of the seeded checkout.

      For the handful of facts that are true of *this box* rather than of a Loom
      deployment: a values file under `charts/` is shared with every cluster
      install, and an up.sh flag would have to be argued for on machines nobody
      here is building. Set from modes.nix, which is where the rest of the
      deployment shape for a platform is decided.

      Left empty the committed placeholder is copied through untouched, so a
      platform that needs nothing pays nothing.
    '';
  };

  config.systemd.services.loom-seed-repo = {
    description = "Seed the Loom working copy into the operator home directory";
    wantedBy = [ "multi-user.target" ];
    after = [ "local-fs.target" ];
    # Docker is what actually consumes the repo (via up.sh), and seeding a few
    # hundred megabytes should not race with it.
    before = [ "docker.service" ];

    # Runs once. A re-run would clobber an operator's in-place changes and any
    # state up.sh has written into the tree.
    unitConfig.ConditionPathExists = "!${loomRepoDir}/.git";

    serviceConfig = {
      Type = "oneshot";
      RemainAfterExit = true;
    };

    path = with pkgs; [
      coreutils
      git
      git-lfs
    ];

    script =
      let
        tmp = "${loomRepoDir}.tmp";
      in
      ''
        set -euo pipefail

        rm -rf ${lib.escapeShellArg tmp}
        cp -a ${loomSrc} ${lib.escapeShellArg tmp}

        # Nix store contents are r-xr-xr-x; git cannot even write .git/index
        # without this.
        chmod -R u+w ${lib.escapeShellArg tmp}
        ${seedOverrides tmp}
        chown -R ${loomUser}:users ${lib.escapeShellArg tmp}

        # Populated atomically, so a power cut mid-copy leaves no half-repo that
        # the ConditionPathExists guard would then skip.
        mv ${lib.escapeShellArg tmp} ${lib.escapeShellArg loomRepoDir}

        echo "[*] Seeded Loom ${tag} into ${loomRepoDir}"
      '';
  };
}
