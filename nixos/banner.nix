# The pre-login screen, as a package and as the two commands that draw it.
#
# `loom-info` prints what this box is; `loom-issue-fragment` writes the blocks that
# land under it from units that run later than the banner does. Both come out of
# nixos/banner/, where the geometry, the colour roles and the rule agetty imposes --
# no backslash, ever -- live in one tested place rather than in a printf per module.
#
# The facts the image was built with are passed on the command line rather than baked
# into the Python, the same route loom-platform-info takes for the platform's own
# claims: one generator, told what box it is running on.
{
  config,
  lib,
  pkgs,
  recoveryPassphraseFile,
  tag,
  ...
}:
let
  cfg = config.loom;

  # Only run mode ever has an access point -- see wifi.nix -- so first-time setup
  # must not advertise one, and a box with no radio must not print a card for it.
  showWifi = cfg.wifi.enable && cfg.mode == "run";

  # The same condition portal.nix issues certificates under. With mutual TLS off, or
  # the portal's own listener off, the page refuses every plaintext POST -- so the
  # screen sends the reader to the console rather than to a URL that cannot help.
  portalIssuesCertificates = cfg.mtls.enable && cfg.portal.tls.enable;

  # How long the box survives the key being pulled, in the same two numbers
  # key-guard.nix multiplies. Restating "10 seconds" here would drift the moment
  # either is tuned.
  keyGuardGrace = cfg.keyGuard.intervalSec * cfg.keyGuard.graceTicks;

  wifiUri = "WIFI:T:WPA;S:${cfg.wifi.ssid};P:${cfg.wifi.psk};;";

  loom-banner = pkgs.python3Packages.buildPythonApplication {
    pname = "loom-banner";
    version = "0.1.0";
    src = ./banner;
    pyproject = true;

    build-system = [ pkgs.python3Packages.poetry-core ];
    # The console, the style spans and the colour system (loom_banner/render.py).
    dependencies = [ pkgs.python3Packages.rich ];
    nativeCheckInputs = [ pkgs.python3Packages.pytest ];

    # What this screen may not do -- eat a backslash, run past the margin, break the
    # danger block into stripes -- is checked here rather than on a monitor at a site.
    # The suite needs nothing built and fails the image in seconds.
    checkPhase = ''
      runHook preCheck
      # Appended rather than assigned, so the paths the python setup hook exported for
      # this package's dependencies survive; `tests` as well, because the suite imports
      # its helpers by module name the way pytest's rootdir insertion would.
      PYTHONPATH=$PWD:$PWD/tests''${PYTHONPATH:+:$PYTHONPATH} pytest tests -q
      runHook postCheck
    '';
  };

  # The flags that say which box this is. A list so that the optional ones are
  # dropped rather than passed empty: `--wifi-uri ""` would ask for a QR code of
  # nothing, and argparse cannot tell that from a box with a radio.
  facts = [
    "--tag ${lib.escapeShellArg tag}"
    "--platform ${lib.escapeShellArg cfg.platform.description}"
    "--amber ${lib.escapeShellArg cfg.branding.amberRgb}"
    "--key-guard-action ${lib.escapeShellArg cfg.keyGuard.action}"
    "--key-guard-grace ${toString keyGuardGrace}"
    "--key-guard-arm-deadline ${toString cfg.keyGuard.armDeadlineSec}"
    "--portal-host ${lib.escapeShellArg cfg.portal.host}"
    # Read at print time, every one of them: a box booted on the recovery
    # passphrase has no key and its guard never arms, a cluster takes minutes, and
    # the portal password is replaced at midnight. The row appears when the file
    # does.
    "--network-conf /etc/loom/network.conf"
    "--ready-summary ${cfg.ready.stateDir}/summary"
    "--key-guard-state ${cfg.keyGuard.stateDir}/state"
    "--key-guard-deadline ${cfg.keyGuard.stateDir}/deadline"
    "--recovery-passphrase ${recoveryPassphraseFile}"
    "--portal-password ${cfg.portal.passwordFile}"
    # The mark the boot splash just showed, drawn by the command the installer menu
    # draws it with, so the two screens cannot disagree.
    "--eyes ${lib.getExe cfg.branding.eyes}"
  ]
  ++ lib.optional (!cfg.platform.runsAiServices) "--no-ai"
  ++ lib.optional (!cfg.platform.meetsResourceMinimum) "--below-resource-minimum"
  ++ lib.optional portalIssuesCertificates "--portal-issues-certificates"
  ++ lib.optionals showWifi [
    "--wifi-ssid ${lib.escapeShellArg cfg.wifi.ssid}"
    "--wifi-psk ${lib.escapeShellArg cfg.wifi.psk}"
    "--wifi-uri ${lib.escapeShellArg wifiUri}"
    "--qrencode ${pkgs.qrencode}/bin/qrencode"
  ]
  ++ map (line: "--warning ${lib.escapeShellArg line}") cfg.debug.warningLines;

  # A wrapper rather than the package itself on PATH, so that `loom-issue-fragment`
  # is not handed this box's facts as well -- it takes none of them.
  loom-info = pkgs.writeShellApplication {
    name = "loom-info";
    text = ''
      exec ${loom-banner}/bin/loom-info ${lib.concatStringsSep " " facts} "$@"
    '';
  };
in
{
  options.loom.banner = {
    info = lib.mkOption {
      type = lib.types.package;
      internal = true;
      description = ''
        `loom-info`: the pre-login screen, told which box it is drawing.

        Three units render it into /run/issue.d and an operator runs it in a pane, so
        it carries this box's facts itself rather than taking them from a caller.
      '';
    };

    fragment = lib.mkOption {
      type = lib.types.package;
      internal = true;
      description = ''
        `loom-issue-fragment`: one numbered block of the login screen, written
        atomically and echoed to the journal.

        The number in the name is the position on screen, because agetty reads
        /run/issue.d in filename order. Used by network.nix and wifi.nix for the
        problems they find, and by box.nix for a --debug image's danger block.
      '';
    };
  };

  config = {
    loom.banner.info = loom-info;
    loom.banner.fragment = loom-banner;
  };
}
