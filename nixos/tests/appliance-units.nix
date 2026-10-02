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
  loomSrc,
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

  # The mutual TLS build (nixos/mtls.nix), taken off the same evaluation for the
  # same reason the --wifi one above is.
  mtlsSystem = boxSystem.extendModules {
    modules = [
      {
        loom.mtls.enable = true;
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

  # The mutual TLS proxy, which is the other thing on this box that binds a
  # socket nothing else can supply.
  #
  # The edge under test is the one that keeps nginx off the cluster's critical
  # path. `proxy_ssl_certificate` naming a file that is not there fails nginx's
  # configuration test, and the certificate it names cannot exist until Loom has
  # come up far enough to issue one -- so the placeholder has to be ordered ahead
  # of nginx and the issuer has to be ordered nowhere near it. Get that backwards
  # and nginx waits for a bring-up, which costs every visitor the captive portal
  # for the length of one.
  #
  # The rest is the wiring: a box that requires client certificates and does not
  # move its own two clients onto the proxy has an assistant pane and a USB
  # ingest that its own cluster refuses.
  mtlsChecks =
    let
      cfg = mtlsSystem.config;
      mtls = cfg.loom.mtls;
      vhosts = cfg.services.nginx.virtualHosts;
      placeholder = cfg.systemd.services.loom-mtls-placeholder;
      identity = cfg.systemd.services.loom-mtls-identity;

      proxyUrl = route: "http://${mtls.listenAddress}:${toString route.port}";

      routeChecks =
        name: route:
        let
          vhost = vhosts."loom-mtls-${name}";
          listen = builtins.head vhost.listen;
          location = vhost.locations."/".extraConfig;
        in
        [
          (check "mtls: the ${name} route listens on ${mtls.listenAddress}" (
            listen.addr == mtls.listenAddress
          ))
          (check "mtls: the ${name} route listens on ${toString route.port}" (listen.port == route.port))
          (check "mtls: the ${name} route proxies to ${route.host}" (
            vhost.locations."/".proxyPass == "https://${route.host}"
          ))
          # Traefik routes on the Host header, so a route that forwards the
          # loopback address it was dialled on gets a 404 from a healthy cluster.
          (check "mtls: the ${name} route rewrites the Host header" (
            lib.hasInfix "proxy_set_header Host ${route.host};" location
          ))
          # The whole point of the module.
          (check "mtls: the ${name} route attaches the client certificate" (
            lib.hasInfix "proxy_ssl_certificate " location && lib.hasInfix "proxy_ssl_certificate_key " location
          ))
          (check "mtls: the ${name} route verifies what it is talking to" (
            lib.hasInfix "proxy_ssl_verify       on;" location
          ))
          # Without SNI the handshake lands on Traefik's default certificate and
          # the router the client asked for is never matched.
          (check "mtls: the ${name} route sends SNI" (
            lib.hasInfix "proxy_ssl_name        ${route.host};" location
            && lib.hasInfix "proxy_ssl_server_name on;" location
          ))
        ];
    in
    [
      (check "mtls: the chart is told to require a client certificate" (
        cfg.loom.chartOverrides.certificate.requireClientCert or false
      ))
      (check "mtls: the assistant pane dials the proxy" (
        cfg.loom.assistant.ollamaBaseUrl == proxyUrl mtls.routes.ollama
      ))
      (check "mtls: USB ingest dials the proxy" (cfg.loom.usbIngest.endpoint == proxyUrl mtls.routes.s3))

      # Both halves again, and for the reason the dnsmasq pair above states:
      # ordering alone constrains nothing unless something puts the unit in the
      # queue.
      (check "mtls: the placeholder is before nginx" (lib.elem "nginx.service" placeholder.before))
      (check "mtls: nginx pulls the placeholder in" (lib.elem "nginx.service" placeholder.wantedBy))

      # And the inverse, which is the mistake that reads like thoroughness: the
      # issuer waits for the cluster, so nginx must not wait for the issuer.
      (check "mtls: the issuer does not hold nginx up" (
        !(lib.elem "nginx.service" identity.before) && !(lib.elem "nginx.service" identity.wantedBy)
      ))

      # A plaintext entrypoint beside a client-certificate requirement is either
      # a way around it or a route that 404s, so the one build that requires a
      # certificate is the one build that does not pass --enable-http. Asserted
      # in both directions: dropping it from every box would cost the captive
      # portal its destination.
      (check "mtls: the box does not also serve plain http" (
        !(lib.hasInfix "--enable-http" cfg.systemd.services.loom.script)
      ))
      (check "default: the box serves plain http, for the captive portal" (
        lib.hasInfix "--enable-http" boxSystem.config.systemd.services.loom.script
      ))

      # Nothing else reissues it, and the certificate outlives neither the CA
      # nor the box.
      (check "mtls: the identity is renewed on a timer" (
        lib.elem "timers.target" cfg.systemd.timers.loom-mtls-identity.wantedBy
      ))

      # The flag is the whole gate: a box built without it must be the box it
      # always was.
      (check "default: no mutual TLS proxy" (
        !(boxSystem.config.services.nginx.virtualHosts ? loom-mtls-ollama)
      ))
      (check "default: the assistant pane dials the ingress directly" (
        lib.hasPrefix "https://" boxSystem.config.loom.assistant.ollamaBaseUrl
      ))
      (check "default: USB ingest dials the ingress directly" (
        lib.hasPrefix "https://" boxSystem.config.loom.usbIngest.endpoint
      ))
    ]
    ++ lib.concatLists (lib.mapAttrsToList routeChecks mtls.routes);

  # Every long option the boot units hand to up.sh, against the up.sh that will
  # actually be seeded.
  #
  # The image pairs these modules with a *tagged* Loom:
  # cicd/build_appliance_image.sh runs `nix-build "${CONTEXT_DIR}/nixos"` out of
  # the working checkout but passes `--arg repoSrc` a clone checked out at the
  # tag, so a flag added to up.sh and to a unit in the same commit still reaches
  # a box whose up.sh predates it by every release in between.
  #
  # up.sh does not reject an unknown long option: `*)` collects it into ARGS,
  # which the step runner forwards to every step, so run_skaffold passes it to
  # skaffold and the boot dies on `unknown flag` from skaffold -- naming neither
  # up.sh nor the unit that added it. That is the failure this catches, and it
  # costs one readFile.
  #
  # Matched as a substring, so `-g|--gpus)` answers for `--gpus`. A flag that
  # appears only in a comment would pass; the case worth catching is a flag the
  # file has never heard of.
  upShChecks =
    let
      upShText = builtins.readFile "${loomSrc}/up.sh";

      # `--gpus nvidia` splits into a flag and a value; the `--` filter drops the
      # value. loom-up adds --skip-* of its own (nixos/box.nix), which up.sh
      # matches with a glob rather than a literal, so they are not asserted here.
      #
      # The context is discarded because setup mode's script names store paths
      # (loom-promote-boot-entry and friends), and every substring taken off it
      # inherits that reference -- which a runCommand's name and build command
      # are not allowed to carry. Only the flag spellings are wanted here, and
      # nothing is realised from them.
      # Only the `loom-up` lines: setup mode's script also runs systemctl and
      # the boot-entry promoter, whose own options are nothing to do with up.sh.
      flagsOf =
        script:
        let
          lines = lib.filter (line: lib.hasInfix "loom-up" line) (
            lib.splitString "\n" (builtins.unsafeDiscardStringContext script)
          );
        in
        lib.filter (word: lib.hasPrefix "--" word) (lib.concatMap (line: lib.splitString " " line) lines);

      unitChecks =
        label: script:
        map (flag: check "${label}: the embedded up.sh knows ${flag}" (lib.hasInfix flag upShText)) (
          flagsOf script
        );
    in
    unitChecks "run mode" boxSystem.config.systemd.services.loom.script
    ++ unitChecks "setup mode" boxSystem.config.specialisation.first-time-setup.configuration.systemd.services.loom-fetch.script;

  platform = boxSystem.config.loom.platform.id;

  checks =
    checksFor "default" boxSystem.config
    ++ checksFor "wifi" wifiSystem.config
    ++ bridgeChecks
    ++ mtlsChecks
    ++ upShChecks;
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

        A failure whose name starts with `mtls:` is about nixos/mtls.nix instead:
        the loopback proxy that gets the box's own clients through its own mutual
        TLS, and the ordering that keeps nginx from waiting on a bring-up.

        A failure ending in `the embedded up.sh knows <flag>` means a boot unit
        passes a flag the tagged checkout does not have. The image takes its
        NixOS modules from this working tree and its Loom from a tag, so the two
        can be releases apart. Gate the flag on the embedded up.sh the way
        nixos/modes.nix does for --resume-if-deployed, rather than dropping it:
        the next release tag is what makes it work.
        EOF
        exit 1
      ''
  )
