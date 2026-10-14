# Places the embedded Loom checkout on the appliance.
#
# The checkout cannot simply be used from /nix/store: up.sh:359 writes
# charts/values-up-flags.yaml *into* the repository, and the skaffold hooks
# (cicd/skaffold, cicd/tag_latest.sh) run from it. So the store copy is
# re-materialised into the operator's home, writable and owned by them.
#
# Two of the chart's values files are written here as part of that, and which
# one a value goes in is what decides whether it wins (skaffold.yaml lists them
# in this order, later last):
#
#   charts/values-user.yaml       `loom.userValues`      -- below every up.sh flag
#   charts/values-up-flags.yaml   up.sh, on the box
#   charts/values-appliance.yaml  `loom.applianceValues` -- above every up.sh flag
#   charts/values-overwrites.yaml nobody here, ever
#
# charts/values-overwrites.yaml is the operator's own file and is left exactly as
# the checkout carries it. It is `--skip-worktree` in a developer's clone
# (devenv.nix) precisely so that people keep real content in it, and these
# modules are also evaluated against a developer's tree by the VM tests, which
# pass `repoSrc ./.`.
{
  config,
  pkgs,
  lib,
  loomSrc,
  tag,
  loomUser,
  loomRepoDir,
  userValuesJson,
  userValuesSources,
  ...
}:
let
  yamlFormat = pkgs.formats.yaml { };

  applianceValues = config.loom.applianceValues;
  userValues = config.loom.userValues;

  # Every leaf of an attrset as a dot-joined path. A leaf is anything that is not
  # an attrset: a list counts, because a list is replaced whole rather than
  # merged -- by helm, by jq's `*` in build_appliance_image.sh, and by
  # lib.recursiveUpdate.
  leafPaths =
    prefix: set:
    lib.concatLists (
      lib.mapAttrsToList (
        name: value:
        let
          path = prefix ++ [ name ];
        in
        if lib.isAttrs value then leafPaths path value else [ (lib.concatStringsSep "." path) ]
      ) set
    );

  # What the box takes back off the operator.
  #
  # Nothing fails here: losing to the appliance layer is what that layer is for,
  # and an operator who asks for `ollama.hpa.enabled` on a one-GPU box is asking
  # for a pod that can never be scheduled. But a value that silently does nothing
  # is worth a line during the build, which is the one moment anybody is looking.
  #
  # A path is taken if the two name the same leaf, or if either one's leaf sits
  # inside the other's subtree -- `a.b` set here replaces all of `a.b.*` there.
  shadowedPaths =
    let
      appliance = leafPaths [ ] applianceValues;
      inside = a: b: a == b || lib.hasPrefix "${b}." a || lib.hasPrefix "${a}." b;
    in
    lib.filter (user: lib.any (app: inside user app) appliance) (leafPaths [ ] userValues);

  warnShadowed =
    value:
    lib.warnIf (shadowedPaths != [ ]) ''
      nixos: these values are set by this appliance and will be ignored:
        ${lib.concatStringsSep "\n  " shadowedPaths}
      charts/values-appliance.yaml is applied after charts/values-user.yaml, so
      the box's own value wins. See nixos/modes.nix and nixos/mtls.nix for what
      sets them and why.
    '' value;

  # Written into the staging copy rather than the finished one, so the `mv` in
  # the script below stays the single moment the repository appears.
  #
  # The committed file is comments and nothing else, so this replaces rather than
  # merges -- there is no second author to merge with, and appending would make a
  # second `ollama:` key the day somebody puts one there. Nothing is written at
  # all when the layer is empty, which is what leaves a developer's own copy
  # alone when these modules are evaluated against their checkout.
  seedLayer =
    tmp: name: values: header:
    lib.optionalString (values != { }) ''

      {
        cat <<'HEADER'
      # Written by the Loom appliance at first boot (nixos/repo.nix).
      #
      ${lib.removeSuffix "\n" header}
      #
      # Edits survive: this is written once, when the checkout is seeded.
      HEADER
        cat ${yamlFormat.generate "loom-${name}" values}
      } > ${lib.escapeShellArg tmp}/charts/${name}
      # Explicit, because the redirect inherits the unit's umask rather than the
      # mode of anything it copied.
      chmod 0644 ${lib.escapeShellArg tmp}/charts/${name}
    '';

  seedValues =
    tmp:
    warnShadowed (
      seedLayer tmp "values-appliance.yaml" applianceValues ''
        # These are values that are true of this box rather than of Loom, so they
        # are not in charts/ and not behind an up.sh flag. Skaffold applies this
        # file after the one up.sh writes, so they also win over every flag. See
        # `loom.applianceValues` in nixos/repo.nix for what may live here.
      ''
      + seedLayer tmp "values-user.yaml" userValues ''
        # Supplied at image build time with `build-appliance-image --values` or
        # `--set`, from:
        #   ${if userValuesSources == "" then "(no source recorded)" else userValuesSources}
        #
        # Skaffold applies this file before the one up.sh writes, so an up.sh flag
        # and the appliance's own values both win over anything here.
      ''
    );
in
{
  options.loom.applianceValues = lib.mkOption {
    type = yamlFormat.type;
    internal = true;
    default = { };
    description = ''
      Helm values the appliance forces on top of whatever up.sh assembles,
      written into `charts/values-appliance.yaml` of the seeded checkout.

      For the handful of facts that are true of *this box* rather than of a Loom
      deployment: a values file under `charts/` is shared with every cluster
      install, and an up.sh flag would have to be argued for on machines nobody
      here is building. Set from modes.nix, which is where the rest of the
      deployment shape for a platform is decided, and from mtls.nix.

      Left empty the committed placeholder is copied through untouched, so a
      platform that needs nothing pays nothing.
    '';
  };

  options.loom.userValues = lib.mkOption {
    type = yamlFormat.type;
    internal = true;
    default = { };
    description = ''
      Helm values the operator asked for, written into `charts/values-user.yaml`
      of the seeded checkout. Set by `build-appliance-image --values FILE` and
      `--set path=value`, which merge, validate and pass them as
      `userValuesJson`.

      The lowest of the override layers on purpose: skaffold applies it before
      `charts/values-up-flags.yaml`, so nothing put here can break a decision an
      up.sh flag or the platform made. What it is for is everything the chart
      exposes and the appliance has no opinion about -- OCR languages, the
      indexing pipeline's limits, resource sizing.
    '';
  };

  # Straight from the build argument, the way loomHostsJson reaches network.nix.
  # Validated before it ever gets here: build_appliance_image.sh checks every
  # path in it against the *embedded tag's* charts/values.yaml, so a typo is
  # refused while there is still a terminal to see it on.
  config.loom.userValues = builtins.fromJSON userValuesJson;

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
        ${seedValues tmp}
        chown -R ${loomUser}:users ${lib.escapeShellArg tmp}

        # Populated atomically, so a power cut mid-copy leaves no half-repo that
        # the ConditionPathExists guard would then skip.
        mv ${lib.escapeShellArg tmp} ${lib.escapeShellArg loomRepoDir}

        echo "[*] Seeded Loom ${tag} into ${loomRepoDir}"
      '';
  };
}
