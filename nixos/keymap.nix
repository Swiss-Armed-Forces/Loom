# Which keyboard the box thinks is in front of it.
#
# Unset by default, which means US QWERTY -- the kernel's built-in map, and what
# every Linux console falls back to. That is fine until somebody has to *type*
# something they cannot see, and this appliance has three such prompts:
#
#   * the `--lock-key` passphrase, in stage 1, on every boot (key-store.nix)
#   * the LUKS recovery passphrase, in stage 1, when the stick is absent
#   * INSTALL and WIPE, the installer's typed interlocks (interlock.py)
#
# On a Swiss or German keyboard under a US map, `-` produces `/` and `y`/`z` are
# swapped. A generated seven-word passphrase contains a `y` or a `z` 71% of the
# time and six hyphens always, so on QWERTZ hardware *every* passphrase is
# mistyped -- and a masked prompt gives no clue why. The word passphrase avoids
# `y` and `z` for that reason (build_appliance_image.sh `generate_luks_key`) and
# the prompts echo what they are given, but neither is a substitute for telling
# the box what keyboard it has.
#
# Set once at build time rather than chosen at the prompt: stage 1 has no UI to
# choose with, and an appliance is built for a known place.
#
# ---------------------------------------------------------------------------
# Why this reaches the initrd, where it matters most
# ---------------------------------------------------------------------------
#
# `console.keyMap` looks like it only configures the booted system, and with the
# scripted initrd it nearly does. With systemd stage 1 -- which box-hardware.nix
# enables -- nixpkgs' console.nix also:
#
#   * writes `KEYMAP=` into the initrd's /etc/vconsole.conf,
#   * copies `/etc/kbd/keymaps` into the initrd, and
#   * pulls `systemd-vconsole-setup.service` and `loadkeys` in with it.
#
# The font half of that is gated on `console.earlySetup`, which branding.nix
# deliberately leaves off -- so the keymap arrives in stage 1 and the Cozette
# font does not, which is exactly the split wanted here.
#
# key-store.nix orders its prompt after `systemd-vconsole-setup.service`, or the
# passphrase could be asked for before the map it is typed under is loaded.
{
  config,
  lib,
  pkgs,
  keymap,
  ...
}:
let
  cfg = config.loom.keymap;

  # A bad name is otherwise silent. systemd-vconsole-setup resolves `KEYMAP=` at
  # boot and falls back to the built-in US map when it cannot find one -- which
  # is the precise failure this option exists to remove, arriving with no message
  # anywhere. `loadkeys -b` resolves the same name at build time instead, so
  # `--keymap de_CH-latn1` fails the build rather than the box.
  #
  # Modelled on nixpkgs' own `optimizedKeymap` (console.nix), which is built only
  # on the scripted-initrd path and so never runs for this appliance.
  keymapCheck =
    pkgs.runCommand "loom-keymap-check-${cfg}"
      {
        nativeBuildInputs = [ pkgs.buildPackages.kbd ];
        LOADKEYS_KEYMAP_PATH = "${pkgs.kbd}/share/keymaps/**";
        preferLocalBuild = true;
      }
      ''
        if ! loadkeys --bkeymap ${lib.escapeShellArg cfg} > /dev/null 2> loadkeys.log; then
            echo "nixos: '${cfg}' is not a console keymap this kbd knows." >&2
            echo "Pick one of these names (without the .map.gz):" >&2
            find ${pkgs.kbd}/share/keymaps -name '*.map.gz' -printf '  %f\n' \
                | sed 's/\.map\.gz//' | sort | head -40 >&2
            cat loadkeys.log >&2
            exit 1
        fi
        touch "$out"
      '';
in
{
  options.loom.keymap = lib.mkOption {
    type = lib.types.str;
    default = keymap;
    internal = true;
    description = ''
      The console keymap for the box, the installer and stage 1, as
      `loadkeys` names it -- `de_CH-latin1`, `fr`, `uk`. Empty means the
      kernel's built-in US QWERTY, which is what every image was before this
      option existed.

      Set by `build-appliance-image --keymap`.
    '';
  };

  config = lib.mkIf (cfg != "") {
    console.keyMap = cfg;

    # Nothing consumes this; it exists to be built, so that a name nothing can
    # resolve stops the image rather than the box. The output is an empty file.
    system.extraDependencies = [ keymapCheck ];
  };
}
