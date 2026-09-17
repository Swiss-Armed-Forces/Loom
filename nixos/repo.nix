# Places the embedded Loom checkout on the appliance.
#
# The checkout cannot simply be used from /nix/store: up.sh:359 writes
# charts/values-up-flags.yaml *into* the repository, and the skaffold hooks
# (cicd/skaffold, cicd/tag_latest.sh) run from it. So the store copy is
# re-materialised into the operator's home, writable and owned by them.
{
  pkgs,
  lib,
  loomSrc,
  tag,
  loomUser,
  loomRepoDir,
  ...
}:
{
  systemd.services.loom-seed-repo = {
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
        chown -R ${loomUser}:users ${lib.escapeShellArg tmp}

        # Populated atomically, so a power cut mid-copy leaves no half-repo that
        # the ConditionPathExists guard would then skip.
        mv ${lib.escapeShellArg tmp} ${lib.escapeShellArg loomRepoDir}

        echo "[*] Seeded Loom ${tag} into ${loomRepoDir}"
      '';
  };
}
