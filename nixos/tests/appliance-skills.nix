# What the assistant pane was given to read, asserted at evaluation time.
#
# Like tests/appliance-hardware.nix and unlike everything else in this directory,
# this is not a VM test: the skills are a store path reachable off the evaluated
# configuration, so this is a `runCommand` that either exits 0 or prints what
# disagreed. Seconds and no KVM -- but, unlike appliance-hardware.nix, it *is*
# bound to the host architecture: the report below is built from `hostPkgs`, and
# the two store paths it inspects are not. Asking an x86_64 machine about the
# Spark is therefore a platform mismatch rather than a verdict, which is why
# `appliance-test skills` is run without `--platform all`.
#
# It exists because opencode fails quietly in three distinct ways here, none of
# which a running box reports in a place anybody looks:
#
#   * A `skills.paths` entry that does not resolve is a single `logWarning`.
#     The pane starts, draws normally, and simply has no skills.
#   * A SKILL.md whose frontmatter does not satisfy the registration guard is
#     skipped with no log line at all.
#   * Both of those produce the same symptom -- an assistant that has never heard
#     of Loom -- which reads as "the model is small" rather than as a broken
#     build.
#
# The division of labour with nixos/skills/tests is deliberate. That suite reads
# the sources against `Documentation/` and cannot see an evaluated configuration;
# this one reads the evaluated configuration and cannot see `Documentation/`. The
# question only this one can answer is the important one: does what shipped match
# *this* platform, with *these* build flags.
#
# `pkgs` is the platform's own nixpkgs -- aarch64 for the Spark -- and every value
# below is read off it at evaluation time. The report is built with `hostPkgs` for
# the same reason appliance-hardware.nix gives: nothing in it is
# architecture-specific, and a runCommand from `pkgs` could not be built on an
# x86_64 runner asking about the Spark.
#
# That is only half enough here, and knowingly so. `assistant.skillsDir` and
# `assistant.instructionsFile` are inputs to the report, and console.nix builds
# both from the platform's `pkgs` -- so realising the report still realises two
# aarch64 derivations. Unlike appliance-hardware.nix, which reads only values,
# this one cannot run for a platform the host cannot build for. See the note at
# the top.
{
  pkgs,
  hostPkgs,
  boxSystem,
}:
let
  inherit (pkgs) lib;

  box = boxSystem.config;
  platform = box.loom.platform.id;
  assistant = box.loom.assistant;

  # True exactly where console.nix builds an assistant pane and box.nix puts
  # opencode in the closure. On a platform without it the right answer is that
  # none of this ships at all, which is a check rather than a skip.
  aiEnabled = box.loom.platform.runsAiServices;

  check = what: ok: { inherit what ok; };

  # Every `loom-*` command this image actually has, read off the package list
  # rather than off a realised closure -- `meta.mainProgram` and `pname` are
  # known at evaluation time, and listing a package's bin/ would mean building
  # it, which would turn a seconds-long check into an image build.
  #
  # This is the half of the question that matters. Most of the `loom-*` commands
  # are conditional: loom-debug-bundle only exists on a `--debug` image,
  # loom-promote-boot-entry only in setup mode, loom-key-guard only where there
  # is a key to guard. A skill naming one of them on an image that has not got it
  # sends an operator to a command-not-found at the worst possible moment.
  commandNames = lib.unique (
    lib.concatMap (
      p:
      lib.optional (p ? meta && p.meta ? mainProgram) p.meta.mainProgram
      ++ lib.optional (p ? pname) p.pname
    ) box.environment.systemPackages
  );

  # Units are named alongside commands, and have to be: half of diagnosing this
  # box is `systemctl status loom-expose` or `journalctl --unit loom-fetch`, and
  # several `loom-*` names are a unit and nothing else.
  #
  # Unlike the commands these are checked against a union rather than against
  # this one image. The skills' unit reference is a table of what the appliance
  # has, and a table that silently lost its `--wifi` rows on a non-WiFi build
  # would be a worse document -- an operator reading it wants to know that
  # loom-wifi-check is the thing that would exist, and `facts.md` already says
  # whether this box has the radio.
  #
  # So the superset is built from the same evaluation, the way nixpkgs builds a
  # specialisation and tests/appliance-units.nix builds its own `--wifi` node.
  # The check that survives is still the one worth having: a unit name that is
  # not a unit on *any* appliance -- a typo, or one that was renamed out from
  # under the skill -- still fails.
  variantUnits =
    variant: lib.attrNames (boxSystem.extendModules { modules = [ variant ]; }).config.systemd.services;

  unitNames = lib.unique (
    lib.attrNames box.systemd.services
    # The credentials are inert -- nothing is realised from this closure -- but
    # they are spelled from the alphabet wifi.nix's assertions demand, so this
    # file is never the reason an assertion run fails.
    ++ variantUnits {
      loom.wifi = {
        enable = true;
        ssid = "loom-skills-eval";
        psk = "skills-eval-not-a-secret";
      };
    }
    ++ variantUnits { loom.mode = "setup"; }
    # And the mutual TLS build, for the same reason: the portal's issuance units
    # and the box's own identity exist only there, and the skills' unit tables
    # are about what this appliance has rather than about which flags this stick
    # was built with. `facts.md` is what says which box the pane is sitting on.
    ++ variantUnits { loom.mtls.enable = true; }
  );

  # The skills refer to each other by name, and their names start with `loom-`
  # too. Without this the tree fails its own check for mentioning itself.
  skillNames = lib.mapAttrsToList (name: _: name) (
    lib.filterAttrs (_: type: type == "directory") (builtins.readDir ../skills)
  );

  loomNames = lib.filter (n: lib.hasPrefix "loom-" n) (
    lib.unique (commandNames ++ unitNames ++ skillNames)
  );

  skillsPresent = assistant.skillsDir != null;
  instructionsPresent = assistant.instructionsFile != null;

  checks =
    if !aiEnabled then
      [
        # Dead weight is the mild failure; the sharp one is a test that silently
        # stops checking anything on the one platform that does not ship a pane.
        (check "no skills on a platform that deploys no Ollama" (!skillsPresent))
        (check "no assistant instructions either" (!instructionsPresent))
      ]
    else
      [
        (check "the assistant has a skill directory" skillsPresent)
        (check "the assistant has an instructions file" instructionsPresent)
      ];

  failures = builtins.filter (c: !c.ok) checks;
  report = lib.concatMapStringsSep "\n" (c: "  FAIL  ${c.what}") failures;
  passed = lib.concatMapStringsSep "\n" (c: "  ok    ${c.what}") checks;

  # The part that has to look at the files, which cannot be done in the Nix
  # expression -- so it is done in the build, against the assembled tree.
  #
  # `*Script` is not decoration: cicd/check_nix_inline_shell.py classifies a
  # `let` binding by its name, and a binding holding shell under any other
  # name is shell the cap cannot see.
  inspectSkillsScript = lib.optionalString aiEnabled ''
    LOOM_SKILLS_DIR=${lib.escapeShellArg "${assistant.skillsDir}"}
    LOOM_INSTRUCTIONS_FILE=${lib.escapeShellArg "${assistant.instructionsFile}"}
    LOOM_KNOWN_NAMES=${lib.escapeShellArg (lib.concatStringsSep "\n" loomNames)}
    LOOM_PLATFORM=${lib.escapeShellArg platform}

    ${builtins.readFile ./inspect_skills.sh}'';
in
hostPkgs.runCommand "loom-appliance-skills-${platform}"
  {
    inherit platform;
    aiEnabled = lib.boolToString aiEnabled;
    loomNames = lib.concatStringsSep " " loomNames;
  }
  (
    if failures != [ ] then
      ''
        echo "loom-appliance-skills (${platform}): ${toString (builtins.length failures)} of ${toString (builtins.length checks)} checks failed" >&2
        cat >&2 <<'EOF'
        ${report}
        EOF
        exit 1
      ''
    else
      ''
        ${inspectSkillsScript}
        echo "loom-appliance-skills (${platform}): ${toString (builtins.length checks)} checks passed"
        cat <<'EOF'
        ${passed}
        EOF
        touch "$out"
      ''
  )
