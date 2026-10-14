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

  # A build carrying operator values, the way a stick built with
  # `build-appliance-image --values` does. The content is inert -- nothing is
  # realised from this closure -- and is a real chart path so that the file it
  # lands in is the only thing under test.
  userValuesSystem = boxSystem.extendModules {
    modules = [
      {
        loom.userValues.pipeline.tika_ocr_languages = [
          "deu"
          "fra"
        ];
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
        cfg.loom.applianceValues.certificate.requireClientCert or false
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

      # And the timer is also what *first* starts it. A target implicitly orders
      # itself `After=` everything in its own `.wants` (systemd.target(5)), so a
      # oneshot in there that waits out a cluster bring-up keeps the box from
      # reaching multi-user.target for however many hours the fetch takes. The
      # pair is asserted together: dropping the `wantedBy` without the
      # `OnBootSec` would leave the identity unissued until the next midnight.
      (check "mtls: the issuer does not hold multi-user.target up" (
        !(lib.elem "multi-user.target" identity.wantedBy)
      ))
      (check "mtls: the issuer still runs shortly after boot" (
        (cfg.systemd.timers.loom-mtls-identity.timerConfig.OnBootSec or null) != null
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

  # The captive portal page (nixos/portal.nix), and above all the one property of
  # it that nothing else in this repository can observe.
  #
  # A probe is answered because it matches no `server_name` and falls to the
  # default server, which redirects. Give the page vhost `default = true`, or let
  # the catch-all stop being the default, and every probe path starts answering
  # 200 -- at which point Android stops offering "Sign in to network", keeps using
  # mobile data, and resolves `frontend.loom` against a mobile network that has
  # never heard of `.loom`. That failure is invisible from a browser, from curl,
  # and from the VM tests; it happens on a phone, at a site.
  #
  # The rest is the privilege split and the two halves of the page's own name.
  portalChecks =
    let
      cfg = mtlsSystem.config;
      plain = boxSystem.config;
      portal = cfg.loom.portal;
      vhosts = cfg.services.nginx.virtualHosts;
      catchAll = vhosts.loom-portal;
      page = vhosts.loom-portal-page;
      server = cfg.systemd.services.loom-portal;
      sync = cfg.systemd.services.loom-portal-certificate;
      placeholder = cfg.systemd.services.loom-portal-tls-placeholder;
      issue = cfg.systemd.services.loom-portal-issue;
      password = cfg.systemd.services.loom-portal-password;

      # Which addresses in /etc/hosts claim the page's name. There should be
      # exactly one, and it should not be the minikube node: `portal` is in the
      # chart's `hostnames.extra` so the certificate names it, and box.nix pins
      # every other name in that list at the cluster.
      addressesNaming = lib.attrNames (
        lib.filterAttrs (_: names: lib.elem portal.host names) cfg.networking.hosts
      );

      portalListeners = lib.filterAttrs (name: _: lib.hasPrefix "loom-portal" name) vhosts;
    in
    [
      # ---- the probe contract ----
      (check "portal: the catch-all is still the default server" (
        catchAll.default && catchAll.serverName == null
      ))
      (check "portal: an unknown path is still a redirect, never a page" (
        lib.hasPrefix "302 " catchAll.locations."/".return
      ))
      (check "portal: the page is not the default server" (!(page.default or false)))
      (check "portal: the page answers for its own name and for the address" (
        lib.hasInfix portal.host (page.serverName or "")
        && lib.hasInfix cfg.loom.portalAddress (page.serverName or "")
      ))

      # Everything this module binds is on the portal address. loom-expose DNATs
      # 80 and 443 on the *appliance* address to the minikube node in nat
      # PREROUTING, ahead of the routing decision, so a listener that landed there
      # could never be reached and would only look as though it served the
      # frontend.
      (check "portal: every listener is on the portal address" (
        lib.all (vhost: lib.all (listen: listen.addr == cfg.loom.portalAddress) vhost.listen) (
          lib.attrValues portalListeners
        )
      ))

      # ---- the page's own name ----
      (check "portal: the resolver answers ${portal.host} with the portal address" (
        lib.elem "/${portal.host}/${cfg.loom.portalAddress}" (
          asList (cfg.services.dnsmasq.settings.address or [ ])
        )
      ))
      (check "portal: ${portal.host} resolves to the portal address and nowhere else" (
        addressesNaming == [ cfg.loom.portalAddress ]
      ))
      # The chart half. The image pairs these modules with a *tagged* Loom, so this
      # is read off the embedded checkout for the same reason `upShChecks` is: a
      # tag whose values.yaml predates the entry produces a certificate with no
      # `portal.loom` in its subjectAltName, and portal.nix drops the TLS listener
      # rather than serving the one page that exists to remove a warning with a
      # warning of its own.
      (check "portal: the embedded chart names the page in its certificate" (
        lib.hasInfix "\n    - portal\n" (builtins.readFile "${loomSrc}/charts/values.yaml")
      ))

      # ---- nginx's critical path ----
      # The same inversion `mtlsChecks` asserts, for the second pair of units that
      # can hold nginx up: the placeholder needs nothing and goes first, the sync
      # waits for a cluster and goes nowhere near it.
      (check "portal: the TLS placeholder is before nginx" (lib.elem "nginx.service" placeholder.before))
      (check "portal: nginx pulls the TLS placeholder in" (lib.elem "nginx.service" placeholder.wantedBy))
      (check "portal: the certificate sync does not hold nginx up" (
        !(lib.elem "nginx.service" sync.before) && !(lib.elem "nginx.service" sync.wantedBy)
      ))
      (check "portal: the certificate is refreshed on a timer" (
        lib.elem "timers.target" cfg.systemd.timers.loom-portal-certificate.wantedBy
      ))
      # And started by it, for the reason the mtls pair above gives: this one
      # waits out a bring-up too, and a target waits for everything in its
      # `.wants`.
      (check "portal: the certificate sync does not hold multi-user.target up" (
        !(lib.elem "multi-user.target" sync.wantedBy)
      ))
      (check "portal: the certificate sync still runs shortly after boot" (
        (cfg.systemd.timers.loom-portal-certificate.timerConfig.OnBootSec or null) != null
      ))

      # ---- the privilege split ----
      # The page server is the one process on this box a visitor talks to. Issuing
      # a certificate needs the mutual TLS CA's private key, so the work is split
      # across a spool and these three are what make the split mean anything.
      (check "portal: the page server does not run as root" (
        (server.serviceConfig.User or "root") != "root"
      ))
      (check "portal: the page server has no kubeconfig" (
        !(lib.any (entry: lib.hasPrefix "KUBECONFIG=" entry) (server.serviceConfig.Environment or [ ]))
      ))
      (check "portal: the page server can reach nothing but loopback" (
        (server.serviceConfig.IPAddressDeny or "") == "any"
      ))
      (check "portal: the issuer is triggered only by the spool" (
        (cfg.systemd.paths.loom-portal-issue.pathConfig.PathExistsGlob or null) != null
        && issue.wantedBy == [ ]
      ))
      (check "portal: the issuer can be triggered again" (
        !(issue.serviceConfig.RemainAfterExit or false)
      ))

      # ---- rate limiting ----
      # `limit_req_zone` is only legal in http{}, and a zone with no limit counts
      # nothing. Both halves, or the one route that costs an RSA key generation is
      # unthrottled.
      (check "portal: the rate-limit zones are declared at http level" (
        lib.hasInfix "limit_req_zone" cfg.services.nginx.appendHttpConfig
      ))
      (check "portal: issuance is rate limited" (
        lib.hasInfix "limit_req  zone=loom_portal_issue" page.locations."= /certificate".extraConfig
      ))

      # ---- the daily password ----
      (check "portal: the password is rotated on a timer" (
        lib.elem "timers.target" cfg.systemd.timers.loom-portal-password.wantedBy
      ))
      # Rotating a value nobody is shown is not rotating it. loom-banner-refresh
      # is what redraws tty1, and it declines on its own when somebody is logged
      # in rather than blanking the screen under them.
      (check "portal: rotating the password repaints the login screen" (
        lib.hasInfix "loom-banner-refresh" password.script
      ))
      (check "portal: the password lands in its own issue fragment" (
        lib.hasInfix "/run/issue.d/62-loom-portal.issue" password.script
      ))

      # ---- gating, in both directions ----
      (check "mtls: the page is served over TLS as well" (vhosts ? loom-portal-tls))
      (check "default: no TLS listener on a box with nothing secret to serve" (
        !(plain.services.nginx.virtualHosts ? loom-portal-tls)
      ))
      (check "default: no password is generated without mutual TLS" (
        !(plain.systemd.services ? loom-portal-password)
      ))
      (check "default: there is no issuance endpoint without mutual TLS" (
        !(plain.systemd.paths ? loom-portal-issue)
      ))
      # Every image still serves the page, and still publishes the anchor: the
      # certificate warning is not a mutual TLS problem.
      (check "default: the page is served anyway" (plain.services.nginx.virtualHosts ? loom-portal-page))
      (check "default: the anchor is published anyway" (plain.systemd.services ? loom-portal-certificate))

      # "Open Loom" follows the build, because the mutual TLS image is the one
      # that does not pass --enable-http: there, port 80 carries only a redirect
      # to a handshake the visitor is about to be refused at.
      (check "mtls: the page links to the frontend over https" (
        lib.hasPrefix "https://" portal.frontendUrl
      ))
      (check "default: the page links to the frontend over http" (
        lib.hasPrefix "http://" plain.loom.portal.frontendUrl
      ))
      (check "mtls: the page knows where its own TLS listener is" (
        portal.secureUrl == "https://${portal.host}/"
      ))
      (check "default: the page offers no secure link it cannot serve" (
        plain.loom.portal.secureUrl == ""
      ))

      # And the probe lands on the page rather than on Loom, which is what makes
      # the two sections above reachable at all.
      (check "portal: the probe redirect points at the page" (
        catchAll.locations."/".return == "302 http://${portal.host}/"
      ))
    ];

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

  # Which values file a value lands in is the whole of what decides whether it
  # takes effect, and the order is stated in the *tagged* skaffold.yaml rather
  # than here -- the same split the up.sh checks above are about.
  #
  # Read off the file instead of asserted as prose: three layers whose entire
  # contract is "later wins" are indistinguishable from each other until
  # something compares their positions.
  valuesChecks =
    let
      skaffoldText = builtins.readFile "${loomSrc}/skaffold.yaml";

      # `          - charts/values-user.yaml        # a comment` -> the path.
      # The dev profile's entry is added by a JSON patch rather than listed, so
      # it does not appear here and the order below is the production one.
      order = map (line: lib.head (lib.splitString " " (lib.last (lib.splitString "- " line)))) (
        lib.filter (line: lib.hasInfix "- charts/values" line) (lib.splitString "\n" skaffoldText)
      );

      position =
        name:
        let
          hits = lib.filter (entry: entry.value == name) (
            lib.imap0 (index: value: { inherit index value; }) order
          );
        in
        if hits == [ ] then null else (lib.head hits).index;

      # Null-safe, so a file the tag does not list fails as "not listed" rather
      # than throwing out of the comparison.
      below =
        a: b:
        let
          x = position a;
          y = position b;
        in
        x != null && y != null && x < y;

      seedScript = system: system.config.systemd.services.loom-seed-repo.script;
    in
    [
      (check "values: the user layer loses to every up.sh flag" (
        below "charts/values-user.yaml" "charts/values-up-flags.yaml"
      ))
      (check "values: the appliance layer beats every up.sh flag" (
        below "charts/values-up-flags.yaml" "charts/values-appliance.yaml"
      ))
      # The operator's own file stays the last word, which is why nothing here
      # may write it.
      (check "values: values-overwrites.yaml is still applied last" (
        below "charts/values-appliance.yaml" "charts/values-overwrites.yaml"
      ))
      (check "values: the defaults are applied first" (
        below "charts/values.yaml" "charts/values-user.yaml"
      ))

      # The regression guard. That file is `--skip-worktree` in a developer's
      # clone precisely so people keep real content in it, and these modules are
      # evaluated against a developer's tree whenever the VM tests run with
      # `repoSrc ./.`.
      (check "values: the seed never writes values-overwrites.yaml" (
        !(lib.hasInfix "values-overwrites.yaml" (seedScript boxSystem))
        && !(lib.hasInfix "values-overwrites.yaml" (seedScript userValuesSystem))
      ))

      # Empty layers are not written at all, so a box that asked for nothing
      # leaves both committed placeholders exactly as the checkout carries them.
      (check "values: a box with no user values writes no user layer" (
        !(lib.hasInfix "charts/values-user.yaml" (seedScript boxSystem))
      ))
      (check "values: --values reaches the seeded checkout" (
        lib.hasInfix "charts/values-user.yaml" (seedScript userValuesSystem)
      ))

      # The seed runs once, on whichever mode boots first, and first-time setup
      # is the mode an air-gapped box boots first. A value only one mode declares
      # is a value that depends on the order somebody used the boot menu in.
      (check "values: mutual TLS is pinned in run mode" (
        mtlsSystem.config.loom.applianceValues.certificate.requireClientCert
      ))
      (check "values: mutual TLS is pinned in setup mode too" (
        mtlsSystem.config.specialisation.first-time-setup.configuration.loom.applianceValues.certificate.requireClientCert
      ))
      # Stated in both directions: pinning it off is what makes the key inert in
      # an operator's own values file on a box that was not built for it.
      (check "values: a default box pins mutual TLS off" (
        boxSystem.config.loom.applianceValues.certificate.requireClientCert == false
      ))
    ];

  platform = boxSystem.config.loom.platform.id;

  checks =
    checksFor "default" boxSystem.config
    ++ checksFor "wifi" wifiSystem.config
    ++ bridgeChecks
    ++ mtlsChecks
    ++ portalChecks
    ++ valuesChecks
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

        A failure whose name starts with `portal:` is about nixos/portal.nix: the
        page the captive portal answers with, the certificates it hands out, and
        the privilege split behind them. The one worth reading twice is the
        probe contract -- a probe is answered with a 302 because it matches no
        `server_name` and falls to the default server. Make the page the default,
        or give it a name a probe sends, and every probe path starts answering
        200: Android stops offering "Sign in to network", keeps using mobile
        data, and resolves `frontend.loom` against a network that has never heard
        of `.loom`. Nothing else here can see that happen.

        A failure whose name starts with `values:` is about which Helm values
        file a value lands in, which is the whole of what decides whether it
        takes effect. The order is read off the embedded skaffold.yaml;
        charts/values-overwrites.yaml belongs to the operator and nothing in
        nixos/ may write it. See nixos/repo.nix.

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
