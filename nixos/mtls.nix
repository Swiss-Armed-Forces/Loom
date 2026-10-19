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
      state=${lib.escapeShellArg stateDir}
      mkdir -p "$state"
      # Restated here as well as in tmpfiles, because this unit is ordered
      # before nginx and a directory nginx cannot traverse is the failure it
      # exists to prevent.
      chgrp ${lib.escapeShellArg nginxGroup} "$state"
      chmod 750 "$state"

      # Only when there is nothing there. A placeholder written over a real
      # identity would take the box off its own cluster until the next renewal.
      if [ -s ${lib.escapeShellArg clientCert} ] && [ -s ${lib.escapeShellArg clientKey} ]; then
        exit 0
      fi

      umask 077
      openssl req -x509 -nodes -days 1 \
        -newkey rsa:2048 \
        -subj "/CN=loom-mtls-placeholder" \
        -keyout ${lib.escapeShellArg clientKey} \
        -out ${lib.escapeShellArg clientCert} 2>/dev/null

      # Group-readable, for the reason `nginxGroup` is declared at all: the
      # configuration test reads both halves as the service user.
      chgrp ${lib.escapeShellArg nginxGroup} \
        ${lib.escapeShellArg clientKey} ${lib.escapeShellArg clientCert}
      chmod 640 ${lib.escapeShellArg clientKey}
      chmod 644 ${lib.escapeShellArg clientCert}

      # `proxy_ssl_trusted_certificate` needs a file too, and the placeholder
      # identity is as good a stand-in as any: nothing verifies against it while
      # the upstream is being refused anyway.
      if [ ! -s ${lib.escapeShellArg serverAnchor} ]; then
        cp ${lib.escapeShellArg clientCert} ${lib.escapeShellArg serverAnchor}
        chmod 644 ${lib.escapeShellArg serverAnchor}
      fi
    '';
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
      state=${lib.escapeShellArg stateDir}
      namespace=${lib.escapeShellArg loomNamespace}
      secret=${lib.escapeShellArg cfg.mtls.caSecret}
      name=${lib.escapeShellArg cfg.mtls.identityName}
      days=${toString cfg.mtls.validityDays}
      renew_before=${toString cfg.mtls.renewBefore}

      # The placeholder is a certificate too, so "is there a file" is not the
      # question -- `-checkend` against a one-day placeholder is false on the
      # day it was written, which is what gets it replaced.
      if openssl x509 -noout -checkend "$((renew_before * 86400))" \
        -in "$state/client.crt" >/dev/null 2>&1; then
        echo "Client certificate has more than $renew_before days left; nothing to do."
        exit 0
      fi

      # Said once per change rather than once per attempt, the way console.nix's
      # waits do: a box that waits an hour for a bring-up should not fill the
      # journal with one line every ten seconds.
      said=""
      note() {
        if [ "$1" != "$said" ]; then
          said="$1"
          echo "$1"
        fi
      }

      until kubectl --request-timeout=5s --namespace "$namespace" \
        get secret "$secret" >/dev/null 2>&1; do
        note "Waiting for '$secret'; Loom has not got that far yet."
        sleep 10
      done

      work="$(mktemp --directory)"
      # shellcheck disable=SC2064
      trap "rm --recursive --force '$work'" EXIT

      loom-client-certificate \
        --name "$name" \
        --days "$days" \
        --namespace "$namespace" \
        --out-dir "$work"

      # Moved into place together, and only once all three exist: nginx reloads
      # on its own schedule as well as on the one below, and a reload that lands
      # between a new certificate and its key gets a pair that does not match.
      #
      # The key is group-readable and the group is nginx's, because nginx runs
      # as its own user and reads this while parsing -- see `nginxGroup`.
      install -m 644 "$work/$name.crt" "$state/client.crt"
      install -m 640 -g ${lib.escapeShellArg nginxGroup} "$work/$name.key" "$state/client.key"
      install -m 644 "$work/loom-server-ca.pem" "$state/loom-server-ca.pem"

      echo "Issued a client identity for $name."

      # reload-or-restart rather than reload: on a box where nginx failed to
      # start at all, a reload is a no-op and the proxy stays down.
      systemctl reload-or-restart nginx.service
    '';
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
