# The captive portal.
#
# A phone that joins the appliance asks for a URL whose answer it already knows
# -- `connectivitycheck.gstatic.com/generate_204` and friends -- to decide
# whether the network reaches the internet. dnsmasq points those four names at
# the responder below (network.nix), which answers 302 to the Loom frontend, and
# the OS reacts by offering "Sign in to network" and opening that page. Without
# it the probe is REFUSED, the network is marked unusable, and a visitor is told
# only that there is no internet.
#
# The redirect target is plain http, and that is not a shortcut. A portal webview
# is not a browser: it refuses an untrusted certificate outright and offers no way
# to click through, and the appliance serves a self-signed `*.loom` that no public
# CA can ever replace -- `.loom` is not a real TLD. So the page has to be
# reachable without TLS, which is what `--enable-http` is for (modes.nix).
#
# RFC 8910's DHCP option 114 is deliberately not used. The API it points at is
# governed by RFC 8908, which requires an https endpoint presenting "a valid
# certificate on which the client can perform revocation checks" and says a client
# that cannot validate it "MUST NOT proceed". That is unreachable here for the
# same reason, so a conforming client would abort at the handshake. The probe
# redirect needs no certificate at all, which is why it is the mechanism that
# works.
#
# The box still says "no internet", and truthfully: it is an island with no
# upstream and advertises no default route. What changes is that the visitor is
# now offered a way in.
{
  config,
  lib,
  loomHostsJson,
  ...
}:
let
  cfg = config.loom;

  # Taken from the host list rather than written out again, exactly as
  # console.nix derives its Ollama host: spelling "frontend.loom" here would be a
  # second copy of the domain, and a box built with a different one would send
  # every visitor to a name it does not resolve.
  frontendHost = lib.findFirst (h: lib.hasPrefix "frontend." h) "frontend.loom" (
    builtins.fromJSON loomHostsJson
  );

  isRun = cfg.mode == "run";
in
{
  options.loom.portal = {
    enable = lib.mkOption {
      type = lib.types.bool;
      default = true;
      description = ''
        Whether the appliance answers captive-portal probes.

        An option rather than an unconditional import so the wiring is greppable
        from one place, and so a box whose network turns out to dislike it can be
        built without it. Off leaves the probes REFUSED, which is what every
        image did before this existed.
      '';
    };

    probeHosts = lib.mkOption {
      type = lib.types.listOf lib.types.str;
      default = [
        "connectivitycheck.gstatic.com"
        "captive.apple.com"
        "www.msftconnecttest.com"
        "detectportal.firefox.com"
      ];
      description = ''
        The hostnames dnsmasq answers with the portal address instead of
        REFUSED. network.nix reads this.

        One dedicated probe FQDN per vendor, and deliberately not the fallbacks
        `www.google.com` and `www.apple.com`: those are real sites people use,
        and claiming them would make this a blanket interception rather than an
        answer to a question only an OS asks. Losing a fallback costs nothing
        while the primary is answered.
      '';
    };

    target = lib.mkOption {
      type = lib.types.str;
      default = "http://${frontendHost}/";
      description = ''
        Where a probe is redirected. Plain http, because a portal webview will
        not accept the appliance's self-signed certificate -- see the header.
      '';
    };
  };

  config = lib.mkIf (cfg.portal.enable && isRun) {
    services.nginx = {
      enable = true;

      virtualHosts.loom-portal = {
        # Pinned to the portal address, because the default is every address the
        # box holds -- which would put nginx on port 80 of the appliance address
        # as well. Nothing would reach it there (loom-expose DNATs that port to
        # the minikube node before the routing decision), but a listener that
        # only looks like it serves the frontend is worth not having.
        listen = [
          {
            addr = cfg.portalAddress;
            port = 80;
          }
        ];

        # The Host header is whichever probe hostname the client was hijacked
        # on, so there is nothing to match against: `default` makes this the
        # server for anything arriving on that address, and `serverName = null`
        # drops the `server_name` directive that would otherwise assert a name.
        default = true;
        serverName = null;

        # Every path, every method, one answer. Probe URLs differ per vendor and
        # per OS release, and nothing else resolves to this address, so a path
        # this config has never heard of is likelier to be a probe than not.
        #
        # 302 rather than 301: the URLs being answered belong to Google and
        # Apple, and a permanent redirect is cached -- a phone that kept this one
        # would go on believing connectivitycheck.gstatic.com is Loom long after
        # it left the appliance. `no-store` says the same thing to anything that
        # caches by header instead.
        locations."/" = {
          return = "302 ${cfg.portal.target}";
          extraConfig = ''
            add_header Cache-Control "no-store" always;
          '';
        };
      };
    };

    # The address nginx binds is put there by the scripted network, and binding
    # one that does not exist yet fails the unit rather than waiting. Same
    # ordering dnsmasq needs next door, and for the same reason.
    systemd.services.nginx = {
      after = [ "network-addresses-${cfg.serviceInterface}.service" ];
      wants = [ "network-addresses-${cfg.serviceInterface}.service" ];
    };
  };
}
