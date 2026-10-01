# The unit wiring the appliance network depends on, asserted at evaluation time.
#
# Not a VM test, for the same reason tests/appliance-hardware.nix is not: every
# value is readable straight off the evaluated configuration, so this is a
# `runCommand` that either exits 0 or prints what disagreed. It costs seconds and
# no KVM, and nothing in it is architecture-specific, so one workstation checks
# every platform.
#
# It exists because of one upstream change that broke a flashed box in silence.
# nixpkgs' scripted networking used to put `network-addresses-<iface>.service`
# ahead of a `network-setup.service` that was itself ahead of `network.target`,
# so a daemon ordered after `network.target` -- which is every daemon nixpkgs
# ships, dnsmasq included -- got the address for free. Under this pin
# `network-setup.service` does not exist, and the address unit is pulled in by
# the interface's .device unit alone, deliberately out of `network.target` so
# that a missing NIC cannot hang the boot. Nothing failed to evaluate, nothing in
# this repository changed, and the appliance stopped serving DHCP.
#
# So what is asserted is the edge itself, on both builds the image is ever
# flashed as: the default one, where the address sits on loom0, and the --wifi
# one, where it sits on the bridge. tests/appliance-dhcp.nix shows that a box
# comes up and hands out a lease; only this says why, and only this can say it
# for the --wifi build on a machine that cannot boot one.
#
# `pkgs` is the platform's own nixpkgs and every value below comes out of it at
# evaluation time. The report is built with `hostPkgs`, because nothing in it is
# architecture-specific and a runCommand from `pkgs` would carry the platform's
# system -- which would make Nix refuse to build the Spark's report on an x86_64
# runner, precisely the run this test is for.
{
  pkgs,
  hostPkgs,
  boxSystem,
}:
let
  inherit (pkgs) lib;

  # The --wifi build, taken off the same evaluation rather than written out as a
  # second one: `extendModules` is what nixpkgs uses for specialisations, and it
  # keeps the two configurations differing in exactly the option under test.
  #
  # The credentials are inert -- nothing is realised from this closure -- but
  # they are spelled from the alphabet wifi.nix's own assertions demand, so that
  # this file is never the reason an assertion run fails.
  wifiSystem = boxSystem.extendModules {
    modules = [
      {
        loom.wifi = {
          enable = true;
          ssid = "loom-units-eval";
          psk = "units-eval-not-a-secret";
        };
      }
    ];
  };

  check = what: ok: { inherit what ok; };

  # `services.dnsmasq.settings` is a freeform format whose values are normalised
  # to lists, so `interface` reads back as [ "loom0" ] rather than "loom0".
  # Normalised here rather than asserted in that shape, so that a nixpkgs change
  # to the format fails on the value being wrong instead of on its wrapper.
  asList = v: if builtins.isList v then v else [ v ];

  # One list per build rather than one list over both, so a failure names which
  # of the two it came from. The bug this file exists for was present in exactly
  # one of them, which is how it survived a suite that covers the other.
  checksFor =
    label: cfg:
    let
      iface = cfg.loom.serviceInterface;
      addresses = "network-addresses-${iface}.service";
      dnsmasq = cfg.systemd.services.dnsmasq;
      nginx = cfg.systemd.services.nginx;
      settings = cfg.services.dnsmasq.settings;
    in
    [
      # Both halves, because `after` on its own is a lie that evaluates: ordering
      # constrains jobs that are both in the queue, and the address unit is
      # pulled in by a .device that appears whenever udev gets to it. `wants` is
      # what puts it in the queue for `after` to bite on.
      (check "${label}: dnsmasq is ordered after ${addresses}" (lib.elem addresses dnsmasq.after))
      (check "${label}: dnsmasq wants ${addresses}, so that ordering is not vacuous" (
        lib.elem addresses dnsmasq.wants
      ))

      # The same pair for the captive portal responder, which binds the *second*
      # address out of that very unit. portal.nix has had this since it was
      # written and network.nix did not, which is the whole of the bug; asserting
      # both is what keeps them from drifting apart again.
      (check "${label}: nginx is ordered after ${addresses}" (lib.elem addresses nginx.after))
      (check "${label}: nginx wants ${addresses}" (lib.elem addresses nginx.wants))

      # The binding mode, which is the other half of the fix: bind-interfaces
      # resolves `interface=` once at startup and exits if the name is not there
      # yet, so an interface renamed, re-created or re-bridged after dnsmasq
      # started needs a restart nobody is at the box to give it.
      (check "${label}: dnsmasq binds dynamically" (asList (settings.bind-dynamic or false) == [ true ]))
      (check "${label}: dnsmasq does not bind its interfaces once, at startup" (
        !(settings ? bind-interfaces)
      ))

      # bind-dynamic without this would listen on every interface that ever
      # appears, which on a box cabled into a real network is a rogue DHCP
      # server. The access control is what makes the mode safe, so the two are
      # asserted together.
      (check "${label}: dnsmasq answers on ${iface} and nothing else" (
        asList (settings.interface or [ ]) == [ iface ]
      ))
      (check "${label}: the appliance address is declared on ${iface}" (
        cfg.networking.interfaces ? ${iface}
      ))
    ];

  # The three units that assemble the bridge, and the daemon that is handed it.
  # Upstream's own bridge, bond and vlan units are `wantedBy` network.target and
  # `before` it; these are their peers and have to say the same, or a consumer of
  # network.target runs while the wired port is still outside the bridge. They
  # had that edge transitively until `network-setup.service` was removed.
  bridgeChecks =
    let
      cfg = wifiSystem.config;
      bridge = cfg.loom.wifi.bridge;
      addresses = "network-addresses-${bridge}.service";
    in
    lib.concatMap
      (name: [
        (check "wifi: ${name} is pulled in by network.target" (
          lib.elem "network.target" cfg.systemd.services.${name}.wantedBy
        ))
        (check "wifi: ${name} is before network.target" (
          lib.elem "network.target" cfg.systemd.services.${name}.before
        ))
        (check "wifi: ${name} is before ${addresses}" (
          lib.elem addresses cfg.systemd.services.${name}.before
        ))
      ])
      [
        "loom-bridge-attach"
        "loom-bridge-tune"
        "loom-wifi-bridge-attach"
      ]
    ++ [
      # hostapd is handed `bridge=` in its own configuration and nixpkgs binds it
      # to the radio's .device unit and nothing else, so without this it can be
      # told to join a device that does not exist yet.
      (check "wifi: hostapd is ordered after ${bridge}-netdev.service" (
        lib.elem "${bridge}-netdev.service" cfg.systemd.services.hostapd.after
      ))
    ];

  platform = boxSystem.config.loom.platform.id;

  checks = checksFor "default" boxSystem.config ++ checksFor "wifi" wifiSystem.config ++ bridgeChecks;
  failures = builtins.filter (c: !c.ok) checks;

  report = lib.concatMapStringsSep "\n" (c: "  FAIL  ${c.what}") failures;
  passed = lib.concatMapStringsSep "\n" (c: "  ok    ${c.what}") checks;
in
hostPkgs.runCommand "loom-appliance-units-${platform}"
  {
    # Handy when a failure needs context -- `nix-build` prints the derivation
    # path, and these are readable straight out of it with `nix derivation show`.
    inherit platform;
    serviceInterface = boxSystem.config.loom.serviceInterface;
    dnsmasqAfter = lib.concatStringsSep " " boxSystem.config.systemd.services.dnsmasq.after;
    dnsmasqWants = lib.concatStringsSep " " boxSystem.config.systemd.services.dnsmasq.wants;
  }
  (
    if failures == [ ] then
      ''
        echo "loom-appliance-units (${platform}): ${toString (builtins.length checks)} checks passed"
        cat <<'EOF'
        ${passed}
        EOF
        touch "$out"
      ''
    else
      ''
        echo "loom-appliance-units (${platform}): ${toString (builtins.length failures)} of ${toString (builtins.length checks)} checks failed" >&2
        cat >&2 <<'EOF'
        ${report}

        dnsmasq After=  ${lib.concatStringsSep " " boxSystem.config.systemd.services.dnsmasq.after}
        dnsmasq Wants=  ${lib.concatStringsSep " " boxSystem.config.systemd.services.dnsmasq.wants}

        These are the edges that put the appliance address on the interface
        before anything binds it. Read the dnsmasq block in nixos/network.nix,
        then nixpkgs' nixos/modules/tasks/network-interfaces-scripted.nix, before
        changing anything here. `after` without `wants` is the mistake that looks
        like a fix.
        EOF
        exit 1
      ''
  )
