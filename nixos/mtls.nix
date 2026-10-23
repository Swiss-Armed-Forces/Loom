# The appliance's way through its own mutual TLS.
#
# With `certificate.requireClientCert` set, Traefik refuses any connection that
# presents no client certificate -- including the two the box makes to itself:
#
#   loom-chat     opencode under Bun, which takes a CA through
#                 NODE_EXTRA_CA_CERTS and has nowhere to put an identity
#                 (console.nix)
#   usb-ingest    mc, whose certificate handling is a directory of CAs
#                 (usb-ingest/loom_usb_ingest/transfer.py, install_cluster_ca)
#
# Both are server-trust mechanisms with no client-identity counterpart, and
# neither program offers one. So the certificate is attached by something that
# can hold it: nginx, already on the box for the captive portal, reverse-proxying
# a loopback port per host and adding `proxy_ssl_certificate` on the way out.
# The clients are pointed at that port and otherwise left alone.
#
# The hop from client to proxy is plain http on 127.0.0.1. It never reaches a
# wire, and the identity it stands in front of is on the same encrypted disk.
#
# The identity itself is issued on the box, because the CA that signs it lives in
# the cluster: cicd/generate_client_certificate.sh, the same script an operator
# runs for a browser, packaged below so it does not depend on repo.nix having
# materialised the checkout yet.
{
  config,
  lib,
  pkgs,
  loomSrc,
  loomUser,
  loomNamespace,
  loomHostsJson,
  requireClientCert,
  ...
}:
let
  cfg = config.loom;

  hosts = builtins.fromJSON loomHostsJson;

  # Taken from the host list for the same reason console.nix and portal.nix take
  # theirs from it: a literal here would be a second copy of the domain, and a
  # box built with a different one would proxy to a name nothing resolves.
  hostNamed = prefix: fallback: lib.findFirst (h: lib.hasPrefix "${prefix}." h) fallback hosts;

  stateDir = "/var/lib/loom/mtls";

  clientCert = "${stateDir}/client.crt";
  clientKey = "${stateDir}/client.key";
  serverAnchor = "${stateDir}/loom-server-ca.pem";

  # The console's identity, and a directory of its own rather than a second pair
  # of files in `stateDir`.
  #
  # It has to be its own directory because `stateDir` is 0750 root:nginx -- see
  # `nginxGroup` -- and the operator is not in that group. That is the whole
  # reason there are two identities rather than one shared pair: nginx's key
  # must stay readable by nginx's group, since `nginx -t` opens it as the
  # service user while parsing, and the only way to share it would be to put
  # the operator into that group -- handing every process running as `loom`
  # nginx's private key. A key of its own costs one more certificate and
  # nothing else.
  #
  # It buys no revocation. Traefik's TLSOption takes a CA and a mode and has no
  # CRL, so the only way to withdraw either identity is to roll the CA, which
  # invalidates both of them and every operator certificate as well.
  consoleDir = "/var/lib/loom/console";

  # A group of its own, not the operator's. `loom` has no group named after it
  # -- `isNormalUser` leaves the primary group as `users` -- so naming the user
  # here would fail at `install -g`, and naming `users` would widen the identity
  # to every account that ever joins it.
  consoleGroup = "loom-console";

  consoleCert = "${consoleDir}/console.crt";
  consoleKey = "${consoleDir}/console.key";
  consoleAnchor = "${consoleDir}/loom-server-ca.pem";

  # The certificate traefik *serves*, which is a different secret from the CA
  # that signs clients. `loom-curl` needs it on every box, not only a mutual TLS
  # one: it is self-signed, so nothing in a stock trust store verifies it.
  #
  # Spelled the way cicd/generate_client_certificate.sh spells it, which is the
  # authority. The lookup here is the narrower of the two: that script also
  # falls back to whatever secret the frontend Ingress names, for a deployment
  # using values-external-tls-certificates.yaml. No appliance is one -- and on a
  # box whose user values swapped the serving certificate, this falls through to
  # the warning rather than to a wrong anchor.
  servingCertSecret = "self-signed-cert";

  # Who has to be able to read the identity, and the reason it is not root.
  #
  # The nixpkgs nginx unit sets `User = cfg.user; Group = cfg.group;`
  # unconditionally -- there is no privileged master process -- and its
  # `preStart` runs `nginx -t` as that user. A `proxy_ssl_certificate` with no
  # variables in it is loaded while the configuration is parsed, so the test
  # opens this key. Owned root:root at 0600 inside a 0700 directory, it cannot:
  # the test fails, `preStart` fails, and nginx never starts -- which on this box
  # takes the captive portal and both loopback proxies with it.
  #
  # Read through the option rather than written as `nginx`, so a box that ever
  # renames the service user keeps working.
  nginxGroup = config.services.nginx.group;

  # The issuer, out of the checkout rather than restated here. Installed as a
  # store binary rather than run from the seeded repository: this unit can start
  # before loom-seed-repo has finished, and one implementation is the point.
  #
  # The script sources ../vars.sh when it finds one, which is how it picks up the
  # namespace in a checkout. There is none beside $out/bin, so the unit passes
  # --namespace instead -- vars.sh needs yq and charts/values.yaml, neither of
  # which belongs in this closure.
  loom-client-certificate =
    pkgs.runCommandLocal "loom-client-certificate"
      {
        nativeBuildInputs = [ pkgs.makeWrapper ];
      }
      ''
        install -D -m 755 ${loomSrc}/cicd/generate_client_certificate.sh \
          $out/bin/loom-client-certificate
        patchShebangs $out/bin/loom-client-certificate
        wrapProgram $out/bin/loom-client-certificate \
          --prefix PATH : ${
            lib.makeBinPath (
              with pkgs;
              [
                coreutils
                kubectl
                openssl
              ]
            )
          }
      '';

  # What nginx presents while the cluster has not issued anything yet.
  #
  # It exists so nginx starts. `proxy_ssl_certificate` naming a file that is not
  # there fails the configuration test, and nginx on this box also serves the
  # captive portal -- so ordering it behind a unit that waits for a bring-up
  # would cost every visitor the portal for the length of one.
  #
  # It authenticates nothing: no CA signed it, so Traefik refuses it exactly as
  # it refuses no certificate at all. The proxy answers 502 until the real
  # identity lands and reloads nginx.
  loom-mtls-placeholder = pkgs.writeShellApplication {
    name = "loom-mtls-placeholder";
    runtimeInputs = with pkgs; [
      coreutils
      openssl
    ];
    text = ''
      LOOM_STATE_DIR=${lib.escapeShellArg stateDir}
      LOOM_CLIENT_CERT=${lib.escapeShellArg clientCert}
      LOOM_CLIENT_KEY=${lib.escapeShellArg clientKey}
      LOOM_SERVER_ANCHOR=${lib.escapeShellArg serverAnchor}
      LOOM_NGINX_GROUP=${lib.escapeShellArg nginxGroup}

      ${builtins.readFile ./scripts/loom_mtls_placeholder.sh}'';
  };

  # Issue, or reissue, the box's identity.
  #
  # Run at boot and once a day. Both calls are cheap when there is nothing to do:
  # a certificate with more than `renewBefore` days left returns immediately,
  # without asking the cluster anything.
  loom-mtls-identity = pkgs.writeShellApplication {
    name = "loom-mtls-identity";
    runtimeInputs = with pkgs; [
      coreutils
      kubectl
      openssl
      systemd
      loom-client-certificate
    ];
    text = ''
      LOOM_STATE_DIR=${lib.escapeShellArg stateDir}
      LOOM_NGINX_GROUP=${lib.escapeShellArg nginxGroup}
      LOOM_CONSOLE_DIR=${lib.escapeShellArg consoleDir}
      LOOM_CONSOLE_GROUP=${lib.escapeShellArg consoleGroup}
      LOOM_NAMESPACE=${lib.escapeShellArg loomNamespace}
      LOOM_CA_SECRET=${lib.escapeShellArg cfg.mtls.caSecret}
      LOOM_IDENTITY_NAME=${lib.escapeShellArg cfg.mtls.identityName}
      LOOM_CONSOLE_IDENTITY_NAME=${lib.escapeShellArg cfg.mtls.consoleIdentityName}
      LOOM_VALIDITY_DAYS=${toString cfg.mtls.validityDays}
      LOOM_RENEW_BEFORE=${toString cfg.mtls.renewBefore}

      ${builtins.readFile ./scripts/loom_mtls_identity.sh}'';
  };

  # curl, told the two things about this box that no stock trust store knows.
  #
  # This is the third client, after the two the proxies above exist for. It is
  # not proxied because it does not need to be: nginx holds an identity for
  # `opencode` and `mc` because neither program can be handed one, and curl can
  # -- so the identity is passed as flags and no port, listener or route is
  # involved.
  #
  # On every image, not only a mutual TLS one, and that is load-bearing rather
  # than tidy. tests/appliance-skills.nix reads the valid command names off
  # *this image's* `environment.systemPackages`, so a command that existed only
  # on an mTLS box could not be named by a skill at all -- and a skill that has
  # to say "on some boxes, prefix this" is a skill a model this size gets wrong
  # half the time. One spelling, every image.
  #
  # What it does on a box with no mutual TLS is still worth having: the serving
  # certificate is self-signed there too, so plain `curl https://api.loom/...`
  # fails to verify it. Every `https://*.loom` example in the skills was broken
  # that way, independently of this issue.
  loom-curl = pkgs.writeShellApplication {
    name = "loom-curl";
    runtimeInputs = with pkgs; [
      coreutils
      curl
      gnugrep
      kubectl
    ];
    text = ''
      LOOM_CONSOLE_DIR=${lib.escapeShellArg consoleDir}
      LOOM_CONSOLE_CERT=${lib.escapeShellArg consoleCert}
      LOOM_CONSOLE_KEY=${lib.escapeShellArg consoleKey}
      LOOM_CONSOLE_ANCHOR=${lib.escapeShellArg consoleAnchor}
      LOOM_NAMESPACE=${lib.escapeShellArg loomNamespace}
      LOOM_SERVING_CERT_SECRET=${lib.escapeShellArg servingCertSecret}

      ${builtins.readFile ./scripts/loom_curl.sh}'';
  };

  # One nginx server per route. The Host header is what Traefik routes on, so
  # this has to be an http proxy rather than a tunnel -- a connection forwarded
  # verbatim arrives asking for 127.0.0.1 and gets a 404 from a healthy cluster.
  routeVirtualHost = _name: route: {
    listen = [
      {
        addr = cfg.mtls.listenAddress;
        port = route.port;
      }
    ];
    # Nothing else answers on this address and port, and the Host header the
    # client sends is the loopback address rather than a name worth matching.
    default = true;
    serverName = null;

    locations."/" = {
      proxyPass = "https://${route.host}";
      extraConfig = ''
        proxy_set_header Host ${route.host};

        # The identity. Re-read on reload, which is what loom-mtls-identity
        # triggers after writing a new one.
        proxy_ssl_certificate     ${clientCert};
        proxy_ssl_certificate_key ${clientKey};

        # And the other direction: the appliance verifies what it is talking to.
        # Nothing issued that certificate, so the anchor is the leaf itself --
        # the same arrangement console.nix makes for Bun.
        proxy_ssl_trusted_certificate ${serverAnchor};
        proxy_ssl_verify       on;
        proxy_ssl_verify_depth 2;

        # Traefik picks the router by SNI before it looks at the Host header, so
        # without these the handshake lands on the default certificate and the
        # route the client asked for is never matched.
        proxy_ssl_name        ${route.host};
        proxy_ssl_server_name on;

        ${route.extraConfig}
      '';
    };
  };
in
{
  options.loom.mtls = {
    enable = lib.mkOption {
      type = lib.types.bool;
      default = requireClientCert;
      description = ''
        Deploy Loom with mutual TLS, and give the box's own clients a way
        through it. Set by `build-appliance-image --require-client-cert`.

        This turns on `certificate.requireClientCert` in the chart as well, via
        `loom.applianceValues`. The two are one switch on purpose: a box with the
        proxy and no mutual TLS proxies for nothing, and a box with mutual TLS
        and no proxy loses its assistant pane and its USB ingest.
      '';
    };

    listenAddress = lib.mkOption {
      type = lib.types.str;
      default = "127.0.0.1";
      internal = true;
      description = ''
        Where the proxy listens. Loopback, because the plaintext side of it is
        the one thing on this box that would be worth intercepting.
      '';
    };

    routes = lib.mkOption {
      type = lib.types.attrsOf (
        lib.types.submodule {
          options = {
            host = lib.mkOption {
              type = lib.types.str;
              description = "The `*.loom` host this route fronts.";
            };
            port = lib.mkOption {
              type = lib.types.port;
              description = "The loopback port it is reached on.";
            };
            extraConfig = lib.mkOption {
              type = lib.types.lines;
              default = "";
              description = "Anything this particular upstream needs.";
            };
          };
        }
      );
      internal = true;
      default = {
        ollama = {
          host = hostNamed "ollama" "ollama.loom";
          port = 18080;
          extraConfig = ''
            # The chat pane streams tokens. Buffered, they arrive in blocks and
            # the pane looks frozen between them.
            proxy_buffering off;

            # A question can take minutes to answer on a box this size, and
            # nginx's own default would close the connection at 60 seconds.
            proxy_read_timeout 3600s;
            proxy_send_timeout 3600s;
          '';
        };
        s3 = {
          host = hostNamed "s3" "s3.loom";
          port = 18081;
          extraConfig = ''
            # `mc mirror` moves whole files, and the default is a megabyte.
            client_max_body_size 0;

            # Streamed rather than spooled to disk first: the appliance's root
            # is sized for Loom, not for a second copy of what is being ingested.
            proxy_request_buffering off;

            proxy_read_timeout 3600s;
            proxy_send_timeout 3600s;
          '';
        };
      };
      description = ''
        The hosts the box reaches through the proxy, one loopback port each.

        Only the two the appliance dials itself. Everything else on the box
        talks to the API server rather than through an ingress, and an operator
        with a browser gets an identity of their own.
      '';
    };

    caSecret = lib.mkOption {
      type = lib.types.str;
      default = "self-signed-mtls-cert";
      internal = true;
      description = ''
        The secret the chart's pre-install hook puts the client CA in. Waiting
        for it is how this module knows Loom has got far enough to issue
        against.
      '';
    };

    identityName = lib.mkOption {
      type = lib.types.str;
      default = "loom-appliance";
      internal = true;
      description = ''
        The CN on the box's own certificate, and the basename the issuer writes.
      '';
    };

    consoleIdentityName = lib.mkOption {
      type = lib.types.str;
      default = "loom-console";
      internal = true;
      description = ''
        The CN on the identity `loom-curl` presents, which is deliberately not
        the one nginx presents. Two keys rather than one shared pair because
        nginx's has to be readable by nginx's group; see `consoleDir` for why
        sharing it is the thing being avoided.
      '';
    };

    validityDays = lib.mkOption {
      type = lib.types.int;
      default = 60;
      internal = true;
      description = ''
        How long the box's certificate is issued for. The issuer refuses a value
        that would outlive the CA behind it.
      '';
    };

    renewBefore = lib.mkOption {
      type = lib.types.int;
      default = 14;
      internal = true;
      description = ''
        Reissue once the certificate has fewer than this many days left. The
        daily timer is what notices.
      '';
    };

    issuer = lib.mkOption {
      type = lib.types.package;
      internal = true;
      readOnly = true;
      description = ''
        `loom-client-certificate`: the checkout's own issuing script, packaged.

        An option because portal.nix issues visitors' certificates with the same
        binary, and a second `runCommandLocal` over the same file would be a
        second thing to keep in step. Set outside the `mkIf` below, beside
        `applianceValues`, so reading it does not depend on this box being a
        mutual TLS one -- portal.nix does its own gating, and an unreferenced
        package is not in any closure.
      '';
    };
  };

  config = lib.mkMerge [
    # The other half of the switch, and the only part of this module that is not
    # conditional. repo.nix writes it into charts/values-appliance.yaml, which
    # Skaffold applies after everything up.sh assembles.
    #
    # Stated in both directions and in both modes rather than only when it is on:
    #
    #   - The seed runs once, on whichever mode boots first, and first-time setup
    #     is the mode an air-gapped box boots first. A value that only one mode
    #     declares is a value that depends on the order somebody used the boot
    #     menu in.
    #   - Pinning it either way is what makes `certificate.requireClientCert` in
    #     an operator's own values file inert. The key has a box-side half -- the
    #     loopback proxies and the identity units below -- that a values file
    #     cannot bring with it, and a box with one half of it serves nothing to
    #     anybody, including itself.
    {
      loom.applianceValues.certificate.requireClientCert = cfg.mtls.enable;
      loom.mtls.issuer = loom-client-certificate;

      # Unconditional, unlike everything below it. See `loom-curl`: a skill can
      # only name a command the image it is read on actually carries, so this
      # one ships whether or not the box requires a client certificate.
      environment.systemPackages = [ loom-curl ];
    }

    (lib.mkIf (cfg.mtls.enable && cfg.mode == "run") {
      # mc reaches S3 through the proxy rather than through the ingress. The CA
      # directory install_cluster_ca maintains stays as it is and goes unused on
      # this path: the hop is http, and taking the code out would leave the
      # non-mutual-TLS box with nothing.
      loom.usbIngest.endpoint = "http://${cfg.mtls.listenAddress}:${toString cfg.mtls.routes.s3.port}";

      # And the chat pane likewise.
      loom.assistant.ollamaBaseUrl = "http://${cfg.mtls.listenAddress}:${toString cfg.mtls.routes.ollama.port}";

      environment.systemPackages = [ loom-client-certificate ];

      # The group that reads the console's key, and the operator in it. Both
      # only on a box that has such a key -- see `consoleGroup`.
      users.groups.${consoleGroup} = { };
      users.users.${loomUser}.extraGroups = [ consoleGroup ];

      systemd.tmpfiles.rules = [
        # /var/lib/loom itself is box.nix's, declared once for the whole box --
        # see the comment there. Declaring it again with another mode produced a
        # duplicate systemd-tmpfiles refuses, keeping whichever module happened to
        # be evaluated first.
        #
        # 0750 root:nginx, not 0700 root:root. See `nginxGroup`: the
        # configuration test opens the key in here as the service user, and a
        # directory it cannot traverse stops nginx from starting at all.
        "d ${stateDir} 0750 root ${nginxGroup} -"

        # And the console's, which the operator has to be able to traverse
        # rather than nginx. Separate for the reason `consoleDir` gives.
        "d ${consoleDir} 0750 root ${consoleGroup} -"
      ];

      systemd.services.loom-mtls-placeholder = {
        description = "Give the mutual TLS proxy something to start with";
        before = [ "nginx.service" ];
        wantedBy = [ "nginx.service" ];
        serviceConfig = {
          Type = "oneshot";
          RemainAfterExit = true;
          ExecStart = lib.getExe loom-mtls-placeholder;
        };
      };

      systemd.services.loom-mtls-identity = {
        description = "Issue the appliance's mutual TLS client identity";
        # Deliberately NOT `wantedBy = [ "multi-user.target" ]`, which is what it
        # used to be. A target implicitly orders itself `After=` everything in
        # its `.wants` (systemd.target(5)), and this unit waits for a cluster
        # bring-up -- so a box that requires client certificates never reached
        # multi-user.target at all, for however many hours the fetch took. The
        # timer below starts it instead, thirty seconds in, which is the same
        # moment for every purpose except the one that was broken.
        after = [ "loom-mtls-placeholder.service" ];

        serviceConfig = {
          Type = "oneshot";
          # Deliberately not RemainAfterExit: the timer below restarts this unit,
          # and a unit that is still "active (exited)" is not restarted by one.
          ExecStart = lib.getExe loom-mtls-identity;

          # The script waits for the CA secret with `until kubectl get secret; sleep
          # 10`, and a first bring-up takes hours. Without this, systemd's
          # DefaultTimeoutStartSec of 90 s SIGTERMs the OnBootSec run every time --
          # and the only other trigger is the daily timer, so the box would hold a
          # certificate no CA signed until the next midnight. For that whole window
          # the assistant pane and USB ingest, both pointed at the loopback proxy,
          # are refused by the box's own cluster.
          TimeoutStartSec = "infinity";

          # kubectl runs as root here and borrows the operator's credentials, the
          # same arrangement ready.nix and usb-ingest.nix use.
          Environment = [ "KUBECONFIG=/home/${loomUser}/.kube/config" ];

          StandardOutput = "journal";
          StandardError = "journal";
        };
      };

      systemd.timers.loom-mtls-identity = {
        description = "Renew the appliance's mutual TLS client identity";
        wantedBy = [ "timers.target" ];
        timerConfig = {
          # Both, and the first is what replaced the unit's own `wantedBy` --
          # see the note on it.
          OnBootSec = "30s";
          OnCalendar = "daily";
          Persistent = true;
        };
      };

      services.nginx = {
        # Set here as well as in portal.nix: the proxy is needed whether or not
        # the box answers captive-portal probes.
        enable = true;
        virtualHosts = lib.mapAttrs' (
          name: route: lib.nameValuePair "loom-mtls-${name}" (routeVirtualHost name route)
        ) cfg.mtls.routes;
      };
    })
  ];
}
