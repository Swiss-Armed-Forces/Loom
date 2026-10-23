# The captive portal.
#
# A phone that joins the appliance asks for a URL whose answer it already knows
# -- `connectivitycheck.gstatic.com/generate_204` and friends -- to decide
# whether the network reaches the internet. dnsmasq answers every name with the
# responder below (network.nix), which redirects to the page this module serves,
# and the OS reacts by offering "Sign in to network" and opening it.
#
# Answering *every* name rather than a list of known probes is deliberate, and
# it is the correction to how this shipped: a client that cannot resolve its
# probe concludes "no internet" rather than "portal present", so a name nobody
# thought to list -- a Samsung or Xiaomi probe, an AOSP fallback, a Linux
# desktop -- took the prompt away rather than merely missing it.
#
# The page does four things, and the first is the only one most visitors want:
#
#   1. "Open Loom", as the one button above the fold.
#   2. The certificate this box serves `*.loom` with, to download and install.
#      `.loom` is not a real TLD, so no public CA can ever issue for it and
#      every visitor otherwise clicks through a warning. The anchor existed
#      before this module -- `generate-client-certificate` exports it -- but the
#      only way to get it was an operator at a console.
#   3. On a `--require-client-cert` box only: a client certificate, to anyone who
#      can type the password on the box's own login screen. That image admits
#      nobody without an identity, so before this there was no way in at all
#      except being handed files out of band.
#   4. A button that stops the visitor's own device nagging them. Until it is
#      pressed every probe gets the redirect; afterwards that client's probes
#      get the success answer its vendor is looking for, and the OS marks the
#      network validated. Without it the probes can never succeed, so Android
#      keeps warning and quietly prefers cellular -- which cannot reach Loom --
#      and Apple re-raises its sheet every sixty seconds. See
#      `portal/loom_portal/validated.py` for where the per-client answer lives.
#
# The probe redirect is plain http, and that is not a shortcut. A portal webview
# is not a browser: it refuses an untrusted certificate outright and offers no way
# to click through. So the page has to be reachable without TLS.
#
# What is NOT reachable without TLS is the third thing. A PKCS#12 bundle carries
# an unencrypted private key, and the appliance segment is a wire -- on a --wifi
# box, everybody in radio range. So an image that issues certificates also serves
# this page on 443 with the cluster's own certificate, which is the one the
# visitor has just been told to trust, and the form is only offered there.
#
# RFC 8910's DHCP option 114 is deliberately not used. The API it points at is
# governed by RFC 8908, which requires an https endpoint presenting "a valid
# certificate on which the client can perform revocation checks" and says a client
# that cannot validate it "MUST NOT proceed". That is unreachable here for the
# same reason, so a conforming client would abort at the handshake. The probe
# redirect needs no certificate at all, which is why it is the mechanism that
# works.
#
# The box has no internet, and until the visitor presses the button it says so.
# It is an island with no upstream, and it now advertises itself as the default
# route anyway -- because a client that cannot route to us never probes us, and
# because everything off this segment is rejected immediately rather than
# dropped (see `loom-expose` in network.nix). What changes is that the visitor
# is offered a way in, and then a way to stop being asked about it.
#
# Run mode only, like everything else here. In first-time setup the box is a DHCP
# client on somebody's real network, and a page that mints client certificates on
# an untrusted LAN is a hole rather than a convenience.
{
  config,
  lib,
  pkgs,
  loomNamespace,
  loomUser,
  loomHostsJson,
  tag,
  ...
}:
let
  cfg = config.loom;

  hosts = builtins.fromJSON loomHostsJson;

  # Taken from the host list rather than written out again, exactly as
  # console.nix derives its Ollama host: spelling "frontend.loom" here would be a
  # second copy of the domain, and a box built with a different one would send
  # every visitor to a name it does not resolve.
  frontendHost = lib.findFirst (h: lib.hasPrefix "frontend." h) "frontend.loom" hosts;
  domain = lib.removePrefix "frontend." frontendHost;

  isRun = cfg.mode == "run";

  # Who reads the TLS material. The nixpkgs nginx unit runs as its own user and
  # `nginx -t` opens every certificate while parsing -- see the same note in
  # mtls.nix, which is where that cost a box its whole nginx.
  nginxGroup = config.services.nginx.group;

  # The unprivileged account the page server runs as. Static rather than
  # DynamicUser, because the tmpfiles rules below name it.
  portalUser = "loom-portal";

  stateDir = "/run/loom-portal";
  requestsDir = "${stateDir}/requests";
  bundlesDir = "${stateDir}/bundles";
  validatedDir = "${stateDir}/validated";
  anchorFile = "${stateDir}/anchor.pem";
  fingerprintFile = "${stateDir}/anchor.sha256";
  # Declared as an option below, because the login screen prints it and box.nix
  # must be able to name the file without restating the path.
  passwordFile = cfg.portal.passwordFile;
  previousPasswordFile = "${passwordFile}.previous";

  # The TLS pair, on the encrypted root rather than in /run: nginx reads it at
  # parse time, so a box that rebooted before the cluster came back would
  # otherwise have no listener at all.
  tlsDir = "/var/lib/loom/portal/tls";
  tlsCert = "${tlsDir}/cert.pem";
  tlsKey = "${tlsDir}/key.pem";
  # Present exactly while the pair above is the one-day self-signed stand-in
  # `loom-portal-tls-placeholder` wrote. The page refuses to hand out a private
  # key over a connection authenticated by it -- see that unit, and
  # `page.py`'s identity section.
  tlsPlaceholderMarker = "${tlsDir}/placeholder";

  # Where "Open Loom" points, and the one detail in this module that cannot be a
  # constant.
  #
  # `--require-client-cert` is the one image that does not pass `up.sh
  # --enable-http` (modes.nix), so on that box port 80 carries only the global
  # redirect to https and `http://frontend.loom/` is a link to a redirect to a
  # handshake. Naming https directly is both honest and one round trip shorter,
  # and the page says in a sentence why the browser will be refused until the
  # certificate from its own second section is installed.
  frontendUrl = "http${lib.optionalString cfg.mtls.enable "s"}://${frontendHost}/";

  # Whether the box may serve this page over TLS as well. The listener needs a
  # certificate that names `portal.loom`, which the cluster issues because
  # `hostnames.extra` lists the portal -- checked by tests/appliance-units.nix,
  # so what is left to decide here is what this image was asked for.
  enableTls = cfg.mtls.enable && cfg.portal.tls.enable;

  loom-portal = pkgs.python3Packages.buildPythonApplication {
    pname = "loom-portal";
    version = "0.1.0";
    src = ./portal;
    pyproject = true;

    build-system = [ pkgs.python3Packages.poetry-core ];
    # Deliberately none. See the module header of portal/loom_portal/portal.py:
    # this is the one process on the box a visitor talks to, and it shells out to
    # nothing and imports nothing that is not in the standard library.
    nativeCheckInputs = [ pkgs.python3Packages.pytest ];

    checkPhase = ''
      runHook preCheck
      # Appended rather than assigned, and `tests` as well, because the suite
      # imports its doubles by module name the way pytest's rootdir insertion
      # would. Same line as ready/ and usb-ingest/.
      PYTHONPATH=$PWD:$PWD/tests''${PYTHONPATH:+:$PYTHONPATH} pytest tests -q
      runHook postCheck
    '';

    makeWrapperArgs = [
      "--set LOOM_PORTAL_FRONTEND_URL ${lib.escapeShellArg cfg.portal.frontendUrl}"
      "--set LOOM_PORTAL_URL ${lib.escapeShellArg "http://${cfg.portal.host}/"}"
      # Where an unvalidated probe is sent, which is the same value nginx's catch-all
      # returns statically. Status and `Location` match, which is all a probe reads;
      # the bodies differ, nginx's `return` carrying its own short HTML and this one
      # none.
      "--set LOOM_PORTAL_REDIRECT_URL ${lib.escapeShellArg cfg.portal.target}"
      "--set LOOM_PORTAL_SECURE_URL ${lib.escapeShellArg cfg.portal.secureUrl}"
      "--set LOOM_PORTAL_STATE_DIR ${lib.escapeShellArg stateDir}"
      "--set LOOM_PORTAL_TAG ${lib.escapeShellArg tag}"
      # branding.nix has already refused to build an image whose logo is an
      # unmaterialised git-lfs pointer, so this is the one Loom asset that can be
      # handed to a web page without a second guard.
      "--set LOOM_PORTAL_LOGO ${config.loom.branding.logoPng}"
      "--set LOOM_PORTAL_ACCENT ${lib.escapeShellArg "#${config.loom.branding.amberRgb}"}"
      # Derived from `enableTls`, not from `cfg.mtls.enable` alone. The two used
      # to differ: `cfg.portal.tls.enable = false` is a documented option and
      # leaves the listener off on an mTLS box. The page then advertised an
      # identity form on a box that could never answer it, and `page.py`'s own
      # "should not be reachable" branch was the thing being reached.
      "--set LOOM_PORTAL_MTLS ${if enableTls then "1" else "0"}"
      "--set LOOM_PORTAL_TLS_PLACEHOLDER ${lib.escapeShellArg tlsPlaceholderMarker}"
      "--set LOOM_PORTAL_PORT ${toString cfg.portal.listenPort}"
    ];

    meta.mainProgram = "loom-portal";
  };

  # The two headers every proxied location on every listener carries.
  #
  # `secure` is what the page is told about the connection it is answering, and
  # it decides whether the certificate form is offered at all. `X-Loom-Client`
  # is the only fact about a visitor this service is ever told, and it is what
  # decides whether their next connectivity probe is answered with a success or
  # with the redirect everybody else gets.
  #
  # Both are set on **every** location on **every** listener rather than only
  # where they are true, so a header a client invented is replaced rather than
  # passed through -- nothing outside this box can reach the loopback port, but
  # a value that is only ever written on the path where it is true is a value
  # somebody can forge on the path where it is not.
  #
  # `$remote_addr` and not `$proxy_add_x_forwarded_for`: nothing stands in front
  # of this nginx, and the second form appends whatever arrived in the request.
  clientHeaders = secure: ''
    proxy_set_header X-Loom-Secure "${if secure then "1" else "0"}";
    proxy_set_header X-Loom-Client $remote_addr;
  '';

  # The paths a connectivity probe uses, and the only ones proxied to the page
  # server from the catch-all.
  #
  # The same list `portal/loom_portal/routes.py` answers, and the third copy of
  # it is `portal/tests/test_routes.py`. `loom_tests/appliance/portal.py` counts
  # them in the rendered nginx configuration, so the two cannot drift silently.
  probePaths = [
    "/generate_204"
    "/gen_204"
    "/generate204"
    "/redirect"
    "/check_network_status.txt"
    "/hotspot-detect.html"
    "/library/test/success.html"
    "/connecttest.txt"
    "/ncsi.txt"
    "/success.txt"
    "/canonical.html"
  ];

  # What the catch-all answers a probe with when it cannot ask the page server.
  # A named location rather than a second copy of the `return`, so the two
  # cannot drift: a probe that found the page server down and a probe that never
  # reached it must be indistinguishable from the phone's side.
  probeFallback = "@probe_fallback";

  probeRedirect = {
    return = "302 ${cfg.portal.target}";
    extraConfig = ''
      add_header Cache-Control "no-store" always;
    '';
  };

  # One exact-match location per probe path on the catch-all vhost.
  #
  # Only these paths are proxied, and `location /` stays a static `return`: with
  # the resolver answering every name on the segment with this address, the
  # catch-all is the busiest thing on the box, and a static return has no
  # upstream, no connect, no timeout and no failure mode. That is worth more
  # than answering a path nobody has listed.
  probeLocationFor = target: {
    proxyPass = "http://127.0.0.1:${toString cfg.portal.listenPort}${target}";
    extraConfig = ''
      ${clientHeaders false}
      # A budget of its own. Apple re-probes every sixty seconds per client and
      # Android probes every few seconds while its sign-in notification is up,
      # so a probe charged against `loom_portal` would spend a visitor's page
      # budget on requests they never made.
      limit_req zone=loom_portal_probe burst=30 nodelay;

      # A probe is a question with a deadline. The defaults are sixty seconds,
      # which on a wedged page server would hold a phone's probe open for a
      # minute -- and a probe that times out is read as "no internet" by every
      # vendor here, which is the answer the fallback below gives in two.
      proxy_connect_timeout 2s;
      proxy_read_timeout 5s;

      # And when the page server is not there at all. `Restart=always` with
      # `RestartSec=5` is a real window, and this is what makes it cost a
      # redirect rather than an nginx error page inside a captive-portal sheet.
      # `proxy_intercept_errors` stays off, so this catches only what nginx
      # generated: the 502/504 of a dead upstream, and `limit_req`'s 503, which
      # belongs here for the same reason -- a throttled probe should be told
      # what every unvalidated probe is told rather than shown a refusal. An
      # answer the service itself produced is never touched.
      error_page 502 503 504 = ${probeFallback};

      # One line per client per minute, forever, about a request nobody made.
      access_log off;
    '';
  };

  # The probe paths keep their own URI, which is how the page server knows which
  # vendor is asking.
  probeLocation = probeLocationFor "";

  # The locations both page listeners carry.
  portalLocations = secure: {
    "/" = {
      proxyPass = "http://127.0.0.1:${toString cfg.portal.listenPort}";
      extraConfig = ''
        ${clientHeaders secure}
        # One visit is a page and a logo, so the budget is per visit rather than
        # per request.
        limit_req zone=loom_portal burst=20 nodelay;

        client_max_body_size 4k;
      '';
    };

    # An exact match, so it wins over the prefix above. This is the one route
    # that costs an RSA key generation on a box that is also running Loom, which
    # is what the separate and much smaller budget is for.
    "= /certificate" = {
      proxyPass = "http://127.0.0.1:${toString cfg.portal.listenPort}";
      extraConfig = ''
        ${clientHeaders secure}
        limit_req  zone=loom_portal_issue burst=3 nodelay;
        limit_conn loom_portal_conn 4;

        client_max_body_size 4k;

        # The page waits up to 45 seconds for the root issuer, so nginx has to
        # outlast it -- otherwise the visitor gets a 504 from the proxy instead
        # of the page's own explanation of what went wrong.
        proxy_read_timeout 60s;
      '';
    };
  };

  # What nginx presents on 443 until the cluster has published something real.
  #
  # The same idiom as mtls.nix's placeholder, and a unit of its own rather than a
  # second job for that one: mtls.nix gates everything on its own condition, and
  # `ssl_certificate` naming a file that is not there fails the configuration
  # test -- which on this box takes the whole of nginx down, the http page
  # included.
  loom-portal-tls-placeholder = pkgs.writeShellApplication {
    name = "loom-portal-tls-placeholder";
    runtimeInputs = with pkgs; [
      coreutils
      openssl
    ];
    text = ''
      LOOM_TLS_DIR=${lib.escapeShellArg tlsDir}
      LOOM_TLS_CERT=${lib.escapeShellArg tlsCert}
      LOOM_TLS_KEY=${lib.escapeShellArg tlsKey}
      LOOM_TLS_PLACEHOLDER_MARKER=${lib.escapeShellArg tlsPlaceholderMarker}
      LOOM_NGINX_GROUP=${lib.escapeShellArg nginxGroup}
      LOOM_PORTAL_USER=${lib.escapeShellArg portalUser}
      LOOM_PORTAL_HOST=${lib.escapeShellArg cfg.portal.host}

      ${builtins.readFile ./scripts/loom_portal_tls_placeholder.sh}'';
  };

  # Publish the certificate Loom serves: as a trust anchor for the page to hand
  # out, and -- on an image that issues identities -- as the pair nginx presents
  # on 443.
  loom-portal-certificate = pkgs.writeShellApplication {
    name = "loom-portal-certificate";
    runtimeInputs = with pkgs; [
      coreutils
      kubectl
      openssl
      systemd
    ];
    text = ''
      LOOM_TLS_CERT=${lib.escapeShellArg tlsCert}
      LOOM_TLS_KEY=${lib.escapeShellArg tlsKey}
      LOOM_TLS_PLACEHOLDER_MARKER=${lib.escapeShellArg tlsPlaceholderMarker}
      LOOM_ANCHOR_FILE=${lib.escapeShellArg anchorFile}
      LOOM_FINGERPRINT_FILE=${lib.escapeShellArg fingerprintFile}
      LOOM_NGINX_GROUP=${lib.escapeShellArg nginxGroup}
      LOOM_NAMESPACE=${lib.escapeShellArg loomNamespace}
      LOOM_SERVING_SECRET=${lib.escapeShellArg cfg.portal.servingSecret}
      LOOM_ENABLE_TLS=${if enableTls then "1" else "0"}

      ${builtins.readFile ./scripts/loom_portal_certificate.sh}'';
  };

  # The privileged half of issuing a visitor a certificate.
  #
  # Started by a path unit watching the spool, never wanted by anything else. It
  # has the operator's kubeconfig and the page server does not, which is the
  # whole point of the split: the process a visitor can reach cannot reach the
  # cluster.
  loom-portal-issue = pkgs.writeShellApplication {
    name = "loom-portal-issue";
    runtimeInputs = [
      pkgs.coreutils
      pkgs.findutils
      pkgs.kubectl
      cfg.mtls.issuer
    ];
    text = ''
      LOOM_REQUESTS_DIR=${lib.escapeShellArg requestsDir}
      LOOM_BUNDLES_DIR=${lib.escapeShellArg bundlesDir}
      LOOM_PORTAL_USER=${lib.escapeShellArg portalUser}
      LOOM_NAMESPACE=${lib.escapeShellArg loomNamespace}
      LOOM_CA_SECRET=${lib.escapeShellArg cfg.mtls.caSecret}
      LOOM_VALIDITY_DAYS=${toString cfg.portal.mtls.validityDays}

      ${builtins.readFile ./scripts/loom_portal_issue.sh}'';
  };
in
{
  options.loom.portal = {
    enable = lib.mkOption {
      type = lib.types.bool;
      default = true;
      description = ''
        Whether the appliance answers captive-portal probes and serves the page
        behind them.

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
        The hostnames dnsmasq answers with the portal address by name.
        network.nix reads this.

        One dedicated probe FQDN per vendor. It is no longer the whole of the
        interception -- network.nix also answers every other name with the same
        address -- so this list is now the part that is written down rather than
        the part that works. It stays for two reasons: the tests are written
        against it, and a wildcard that is ever reverted must not silently take
        the probes with it.
      '';
    };

    host = lib.mkOption {
      type = lib.types.str;
      default = "portal.${domain}";
      description = ''
        The name the page answers to, beside the portal address itself.

        It exists so the TLS listener can present a certificate that matches
        something. `charts/values.yaml` has to carry it in `hostnames.extra` for
        the chart's pre-install Job to put it in the subjectAltName; a tag that
        does not is what `loom.portal.tls.enable` is silently gated on.

        network.nix answers it from dnsmasq with the portal address, and box.nix
        takes it back out of the `/etc/hosts` block that pins every other Loom
        name at the minikube node -- this one is not served by the cluster.
      '';
    };

    frontendUrl = lib.mkOption {
      type = lib.types.str;
      internal = true;
      readOnly = true;
      description = ''
        Where the page's "Open Loom" button points.

        https on a `--require-client-cert` box and http on every other one, because
        that is the one image modes.nix does not give `up.sh --enable-http` -- so
        there, port 80 carries only a redirect to a handshake the visitor will be
        refused at. An option because `nixos/tests/appliance-units.nix` asserts the
        two directions against each other, and a value only the wrapper carries is
        a value only a built image can be asked about.
      '';
    };

    secureUrl = lib.mkOption {
      type = lib.types.str;
      internal = true;
      readOnly = true;
      description = ''
        Where the page sends a visitor to collect a certificate, or empty on an
        image with no TLS listener -- which is every image but the mutual TLS one.
        See `loom.portal.tls.enable`.
      '';
    };

    package = lib.mkOption {
      type = lib.types.package;
      internal = true;
      readOnly = true;
      description = ''
        `loom-portal`: the page server, built from `nixos/portal/`.

        An option, and set in both modes, so that
        `nix-build ./nixos -A boxSystem.config.loom.portal.package` reaches it. Building
        it on its own runs the package's pytest suite under the interpreter the image
        ships, which is a check worth having without building a whole appliance.
      '';
    };

    listenPort = lib.mkOption {
      type = lib.types.port;
      default = 18082;
      internal = true;
      description = ''
        The loopback port the page server binds, and nginx proxies to. Beside
        mtls.nix's 18080 and 18081, which is the whole of the box's private
        http.
      '';
    };

    servingSecret = lib.mkOption {
      type = lib.types.str;
      default = "self-signed-cert";
      internal = true;
      description = ''
        The secret the chart's pre-install hook puts the certificate Traefik
        serves in. The page hands out its anchor, and the TLS listener presents
        its pair.
      '';
    };

    target = lib.mkOption {
      type = lib.types.str;
      default = "http://${config.loom.portalAddress}/";
      description = ''
        Where a probe is redirected. Plain http, because a portal webview will
        not accept the appliance's self-signed certificate -- see the header.

        The page rather than the frontend, which is what it used to be: the
        certificate a visitor needs, and on a mutual TLS box the identity they
        cannot get in without, are both on it, and "Open Loom" is the first thing
        on it.

        The literal address rather than `portal.loom`, which is also what it
        used to be. A redirect to a name makes the portal webview do a second
        lookup, in a TLD that does not exist, from a context that is not a
        browser -- and on a phone with Android's Private DNS in strict mode that
        lookup cannot succeed at all. Such a phone still detects the portal and
        still follows this redirect, because Android's connectivity check
        deliberately bypasses private DNS; it simply cannot resolve anything the
        redirect names. An address needs no resolver.

        The name is still served and the page's footer still prints it: it is
        what somebody types when they come back later, and on a mutual TLS box
        it is what the certificate on 443 is for.
      '';
    };

    tls = {
      enable = lib.mkOption {
        type = lib.types.bool;
        default = true;
        description = ''
          Whether to serve the page on 443 as well, with the cluster's own
          certificate.

          Only has an effect on a `--require-client-cert` image, and that is the
          point rather than an accident: the listener exists so a PKCS#12 bundle
          is not handed over in the clear, and standing it up anywhere else would
          mean copying the certificate Traefik serves `*.loom` with -- private
          key included -- out of the cluster and onto the box, in front of an
          unauthenticated listener, to protect a file that is public.
        '';
      };
    };

    passwordFile = lib.mkOption {
      type = lib.types.str;
      default = "${stateDir}/password";
      internal = true;
      readOnly = true;
      description = ''
        Where the day's portal password is published.

        Declared rather than written out twice: the rotation unit below owns the
        file, and the login screen reads it at print time -- the same arrangement
        `loom.ready.stateDir` and `loom.keyGuard.stateDir` have with the banner.
        On tmpfs, so a box that has been off since midnight has no stale password
        to offer.
      '';
    };

    mtls = {
      validityDays = lib.mkOption {
        type = lib.types.int;
        default = 7;
        internal = true;
        description = ''
          How long a certificate issued through the page is good for.

          Much shorter than the 60 days `generate-client-certificate` defaults
          to, because that default is for an operator issuing by hand to somebody
          they chose. This one is issued to whoever read a password off a screen,
          and the page is always there to issue another.
        '';
      };

      passwordWords = lib.mkOption {
        type = lib.types.int;
        default = 4;
        internal = true;
        description = ''
          How many EFF words in the daily password.

          Four is about 51 bits after the layout filter, against an endpoint that
          is rate limited, reachable only from the appliance segment, and rotates
          every day. More would cost rows on a login screen that is already full
          on a `--wifi` box.
        '';
      };
    };
  };

  config = lib.mkMerge [
    # Outside the gate below, and the only part of this module that is: the option is
    # `readOnly`, so reading it on a box that answers no probes has to be possible.
    # Nothing is realised by declaring it.
    {
      loom.portal.package = loom-portal;
      loom.portal.frontendUrl = frontendUrl;
      loom.portal.secureUrl = lib.optionalString enableTls "https://${cfg.portal.host}/";
    }

    (lib.mkIf (cfg.portal.enable && isRun) (
      lib.mkMerge [
        {
          # --------------------------------------------------------------------
          # The page, on plain http, on every image.
          # --------------------------------------------------------------------

          # The name, so the page has an address bar entry somebody can type and
          # the TLS listener has something to be a certificate for. Pointed at the
          # responder rather than at the box: port 80 on the box address is DNAT'd
          # to Traefik before the routing decision (network.nix, loom-expose).
          networking.hosts."${cfg.portalAddress}" = [ cfg.portal.host ];

          users.users.${portalUser} = {
            isSystemUser = true;
            group = portalUser;
            description = "The appliance's captive portal page";
          };
          users.groups.${portalUser} = { };

          systemd.tmpfiles.rules = [
            # `/run/loom-portal`, beside `/run/loom` rather than inside it, and the
            # reason is a permission rather than a preference: console.nix declares
            # `/run/loom` as `0700 loom:users` for the tmux socket, and
            # systemd-tmpfiles takes the first rule it has for a path and ignores
            # every later one. A second declaration of it here would silently win or
            # silently lose, and the losing case is a console with no session --
            # `loom-console` could no longer create its socket. This is the first
            # thing on the box that runs as neither root nor `loom`, so it gets a
            # directory of its own instead.
            "d ${stateDir} 0755 root root -"
            # 0730, which is -wx for the group and nothing for anyone else. The
            # page server may create, stat and unlink **by name** and may not
            # enumerate, so a compromise of the one process a visitor can reach
            # cannot list other visitors' tokens.
            "d ${requestsDir} 0730 root ${portalUser} -"
            "d ${bundlesDir} 0730 root ${portalUser} -"
            # The same -wx as the two spool directories, and for the same reason:
            # the page creates and stats markers by name and nothing enumerates
            # them, so a compromise of the one process a visitor can reach cannot
            # read back the list of who was on this network. Nothing sweeps it and
            # nothing needs to -- it is on tmpfs, and a /24 pool caps it at a
            # hundred empty files. See portal/loom_portal/validated.py.
            "d ${validatedDir} 0730 root ${portalUser} -"
          ];

          systemd.services.loom-portal = {
            description = "The appliance's captive portal page";
            wantedBy = [ "multi-user.target" ];
            after = [ "systemd-tmpfiles-setup.service" ];

            serviceConfig = {
              Type = "simple";
              ExecStart = "${lib.getExe loom-portal} --listen 127.0.0.1 --port ${toString cfg.portal.listenPort}";

              User = portalUser;
              Group = portalUser;

              # A page that has stopped is worse than one that never existed: the
              # probe still redirects to it. Same argument ready.nix makes.
              Restart = "always";
              RestartSec = 5;

              # Everything below is the other half of the privilege split. This
              # process has no kubeconfig, no kubectl, nothing on PATH it shells
              # out to, and now no way to reach anything but the socket nginx
              # dials. A full compromise of it buys a certificate request, which is
              # what it is for.
              IPAddressAllow = [ "localhost" ];
              IPAddressDeny = "any";
              RestrictAddressFamilies = [
                "AF_INET"
                "AF_UNIX"
              ];
              CapabilityBoundingSet = [ ];
              NoNewPrivileges = true;
              ProtectSystem = "strict";
              ProtectHome = true;
              PrivateTmp = true;
              PrivateDevices = true;
              ProtectKernelTunables = true;
              ProtectKernelModules = true;
              ProtectControlGroups = true;
              LockPersonality = true;
              MemoryDenyWriteExecute = true;
              SystemCallFilter = [ "@system-service" ];
              SystemCallArchitectures = "native";
              ReadWritePaths = [
                requestsDir
                bundlesDir
                validatedDir
              ];

              StandardOutput = "journal";
              StandardError = "journal";
            };
          };

          systemd.services.loom-portal-certificate = {
            description = "Publish the cluster's serving certificate for the portal";
            # Deliberately not `wantedBy = [ "multi-user.target" ]`. A target
            # implicitly orders itself `After=` everything in its `.wants`
            # (systemd.target(5)), and this unit waits out a cluster bring-up --
            # so the box would not reach multi-user.target for as long as that
            # took. The timer below starts it instead, thirty seconds in.
            after = [ "loom-portal-tls-placeholder.service" ];
            # Deliberately NOT before or wantedBy nginx. This unit waits for a
            # cluster bring-up; nginx must not. The placeholder is what nginx
            # waits for, and it needs nothing.
            serviceConfig = {
              Type = "oneshot";
              # No RemainAfterExit: the timer restarts this unit, and a unit still
              # "active (exited)" is not restarted by one.
              ExecStart = lib.getExe loom-portal-certificate;
              # What makes "waiting forever is safe here" true. The script loops
              # `until kubectl ...; sleep 10`, so without this systemd's 90 s
              # DefaultTimeoutStartSec kills it and logs a failed unit on every boot
              # where the cluster is not already up -- and the hourly timer then
              # spends the page's first hour handing out no anchor and no
              # fingerprint, which is the hour the page exists for.
              TimeoutStartSec = "infinity";
              # kubectl runs as root here and borrows the operator's credentials,
              # the same arrangement mtls.nix, ready.nix and usb-ingest.nix use.
              Environment = [ "KUBECONFIG=/home/${loomUser}/.kube/config" ];
              StandardOutput = "journal";
              StandardError = "journal";
            };
          };

          systemd.timers.loom-portal-certificate = {
            description = "Keep the portal's copy of the serving certificate current";
            wantedBy = [ "timers.target" ];
            timerConfig = {
              # Hourly, and expiry is not why. The chart's pre-install Job replaces
              # the certificate the moment a declared host is missing from its
              # subjectAltName -- which is exactly what happens the first time a
              # box meets a chart that names this page. A daily sync would spend up
              # to a day handing out an anchor that no longer matches what Traefik
              # serves, so a visitor would install it and the warning would stay:
              # the one failure this whole page exists to remove.
              # Thirty seconds in, which is what replaced the unit's own
              # `wantedBy` -- see the note on it.
              OnBootSec = "30s";
              OnCalendar = "hourly";
              Persistent = true;
              RandomizedDelaySec = 300;
            };
          };

          services.nginx = {
            # Set here as well as in mtls.nix: each module is independently able to
            # need nginx, and the option merges.
            enable = true;

            # `limit_req_zone` is only legal in http{}, so the zones are declared
            # here and the limits applied per location below. Both are needed: a
            # zone with no limit counts nothing, and a limit in the page's own
            # location would charge a page load against the issuance budget.
            appendHttpConfig = ''
              limit_req_zone  $binary_remote_addr zone=loom_portal:1m       rate=60r/m;
              limit_req_zone  $binary_remote_addr zone=loom_portal_issue:1m rate=6r/m;
              limit_req_zone  $binary_remote_addr zone=loom_portal_probe:1m rate=120r/m;
              limit_conn_zone $binary_remote_addr zone=loom_portal_conn:1m;
            '';

            virtualHosts.loom-portal = {
              # Pinned to the portal address, because the default is every address
              # the box holds -- which would put nginx on port 80 of the appliance
              # address as well. Nothing would reach it there (loom-expose DNATs
              # that port to the minikube node before the routing decision), but a
              # listener that only looks like it serves the frontend is worth not
              # having.
              listen = [
                {
                  addr = cfg.portalAddress;
                  port = 80;
                }
              ];

              # The catch-all, and the reason captive-portal detection still works.
              # A probe arrives with `Host: connectivitycheck.gstatic.com`, matches
              # no server_name, falls to the default server, and is redirected --
              # never answered with a page. `serverName = null` drops the
              # `server_name` directive that would otherwise assert a name.
              default = true;
              serverName = null;

              # Every path, every method, one answer -- except the listed probe
              # paths, which go to the page server so a client that has finished
              # with the page can be told what it wants to hear. Probe URLs differ
              # per vendor and per OS release, and with the resolver answering every
              # name on the segment with this address, a path this config has never
              # heard of is likelier to be a probe than not.
              #
              # 302 rather than 301: the URLs being answered belong to Google and
              # Apple, and a permanent redirect is cached -- a phone that kept this
              # one would go on believing connectivitycheck.gstatic.com is Loom long
              # after it left the appliance. `no-store` says the same thing to
              # anything that caches by header instead.
              locations = {
                "/" = probeRedirect;
                # Byte-for-byte what `/` answers, so a probe that found the page
                # server down and a probe that never reached it are
                # indistinguishable from the phone's side.
                ${probeFallback} = probeRedirect;
              }
              // lib.genAttrs (map (path: "= ${path}") probePaths) (_: probeLocation);
            };

            virtualHosts.loom-portal-page = {
              listen = [
                {
                  addr = cfg.portalAddress;
                  port = 80;
                }
              ];
              # Emphatically not the default server -- see above. Both the name and
              # the address, so a visitor who typed the address rather than
              # following the redirect still gets the page.
              serverName = "${cfg.portal.host} ${cfg.portalAddress}";
              locations = portalLocations false;
            };

            # The two probes that cannot be told apart by path.
            #
            # Ubuntu's NetworkManager fetches `http://connectivity-check.ubuntu.com/`
            # and KDE fetches `http://networkcheck.kde.org/` -- both at `/`, so the
            # only thing distinguishing them from any other request to the catch-all
            # is the Host header. A server block is the clean way to read one; the
            # alternatives are proxying the catch-all's `/` wholesale, which is the
            # property the design is built around not doing, or an `if`.
            virtualHosts.loom-portal-probe = {
              listen = [
                {
                  addr = cfg.portalAddress;
                  port = 80;
                }
              ];
              serverName = "connectivity-check.ubuntu.com networkcheck.kde.org";
              locations = {
                # Rewritten to a probe path rather than proxied as it arrived.
                # `/` is the page, in `routes.py` and on every other listener, so
                # passing this through unchanged would serve a NetworkManager
                # probe the whole portal page with status 200 -- which is the one
                # answer a probe must never get, and the failure this module's
                # header spends a paragraph on. Both vendors read a 204 as
                # success, so `/generate_204` is the right thing to ask the page
                # server on their behalf.
                "= /" = probeLocationFor "/generate_204";
                "/" = probeRedirect;
                ${probeFallback} = probeRedirect;
              };
            };
          };

          systemd.services.nginx = {
            # The address nginx binds is put there by the scripted network, and
            # binding one that does not exist yet fails the unit rather than
            # waiting. Same ordering dnsmasq needs next door, and for the same
            # reason.
            after = [ "network-addresses-${cfg.serviceInterface}.service" ];
            wants = [ "network-addresses-${cfg.serviceInterface}.service" ];
          };
        }

        # ----------------------------------------------------------------------
        # The TLS listener, on the one image that has something secret to serve.
        # ----------------------------------------------------------------------
        (lib.mkIf enableTls {
          services.nginx.virtualHosts.loom-portal-tls = {
            listen = [
              {
                addr = cfg.portalAddress;
                port = 443;
                ssl = true;
              }
            ];
            # Name-based, and emphatically not the default server -- which it
            # used to be, on the grounds that nothing else was on this socket.
            # The resolver now answers every name on the segment with this
            # address, so everything a client's phone does over https in the
            # background lands here: certificate warnings instead of clean
            # connection failures, and -- the sharp half -- every one of those
            # requests charged against `loom_portal`, a budget sized for one
            # visit being a page and a logo. The visitor's own page load then
            # gets a 503 from a rate limiter they never touched.
            serverName = "${cfg.portal.host}";
            onlySSL = true;
            sslCertificate = tlsCert;
            sslCertificateKey = tlsKey;
            locations = portalLocations true;
          };

          # And what unknown SNI gets instead: an immediate TLS alert.
          #
          # Faster for the client than a handshake it will reject anyway, and it
          # keeps the budget above the visitor's. `https://<portal address>`
          # stops working with it, which costs nothing -- `secureUrl` is the
          # name, and nothing links to the address over TLS.
          services.nginx.virtualHosts.loom-portal-tls-reject = {
            listen = [
              {
                addr = cfg.portalAddress;
                port = 443;
                ssl = true;
              }
            ];
            default = true;
            onlySSL = true;
            serverName = null;
            # nginx requires a certificate on an ssl listener even where it will
            # never present one, and `ssl_reject_handshake` is evaluated first.
            sslCertificate = tlsCert;
            sslCertificateKey = tlsKey;
            extraConfig = ''
              ssl_reject_handshake on;
            '';
          };

          systemd.services.loom-portal-tls-placeholder = {
            description = "Give the portal's TLS listener something to start with";
            before = [ "nginx.service" ];
            wantedBy = [ "nginx.service" ];
            serviceConfig = {
              Type = "oneshot";
              RemainAfterExit = true;
              ExecStart = lib.getExe loom-portal-tls-placeholder;
            };
          };
        })

        # ----------------------------------------------------------------------
        # Issuing identities, on the image that requires one.
        # ----------------------------------------------------------------------
        (lib.mkIf cfg.mtls.enable {
          systemd.paths.loom-portal-issue = {
            description = "Watch for portal certificate requests";
            wantedBy = [ "multi-user.target" ];
            # The spool is made by tmpfiles. A path unit on a directory that does
            # not exist yet watches the nearest ancestor and recovers on its own,
            # but ordering it makes the first request after a boot deterministic
            # rather than merely likely.
            after = [ "systemd-tmpfiles-setup.service" ];
            pathConfig.PathExistsGlob = "${requestsDir}/*.req";
          };

          systemd.services.loom-portal-issue = {
            description = "Issue a visitor's mutual TLS client identity";
            # Deliberately no wantedBy: the path unit above is the only trigger.
            serviceConfig = {
              Type = "oneshot";
              # And deliberately no RemainAfterExit, for the reason mtls.nix gives
              # for its own issuer: a unit still "active (exited)" is never started
              # again, and this one has to be.
              ExecStart = lib.getExe loom-portal-issue;
              Environment = [ "KUBECONFIG=/home/${loomUser}/.kube/config" ];
              # Shorter than nginx's read timeout on the route and longer than the
              # page's own wait, so the page is always the thing that gives up
              # first and has a sentence to show for it.
              TimeoutStartSec = 60;
              # A visitor can ask for a 4096-bit key, which is the only real CPU
              # this feature spends. Capped so a room full of people cannot make it
              # compete with a bring-up.
              CPUQuota = "50%";
              Nice = 10;
              StandardOutput = "journal";
              StandardError = "journal";
            };
          };

          # ------------------------------------------------------------------
          # The daily password, and the two lines of login screen it occupies.
          # ------------------------------------------------------------------
          systemd.services.loom-portal-password = {
            description = "Rotate the portal's certificate password";
            # Started by its timer alone -- `OnBootSec` for the first one and
            # `OnCalendar` for every day after. It used to be `wantedBy
            # multi-user.target` *as well*, so a box that had been powered off
            # across midnight ran it twice within seconds: once from the target
            # and once from the timer's missed elapse. Nothing was lost (stateDir
            # is tmpfs, so there is no yesterday's password at boot) but the
            # password an operator was reading off the login screen changed under
            # them, and `loom-banner-refresh` restarted the getty twice inside the
            # window publish.py goes out of its way to keep clear of the
            # operator's first keypress.
            after = [ "systemd-tmpfiles-setup.service" ];
            serviceConfig = {
              Type = "oneshot";
              # No RemainAfterExit: the timer restarts this unit.
              StandardOutput = "journal";
              StandardError = "journal";
            };
            path = with pkgs; [
              coreutils
              diceware
              gnugrep
              config.loom.bannerRefresh
            ];
            script = ''
              LOOM_STATE_DIR=${lib.escapeShellArg stateDir}
              LOOM_PASSWORD_FILE=${lib.escapeShellArg passwordFile}
              LOOM_PREVIOUS_PASSWORD_FILE=${lib.escapeShellArg previousPasswordFile}
              LOOM_PORTAL_USER=${lib.escapeShellArg portalUser}
              LOOM_PASSWORD_WORDS=${toString cfg.portal.mtls.passwordWords}

              ${builtins.readFile ./scripts/loom_portal_password.sh}'';
          };

          systemd.timers.loom-portal-password = {
            description = "Rotate the portal's certificate password daily";
            wantedBy = [ "timers.target" ];
            timerConfig = {
              # The boot trigger as well as the daily one, since the service is no
              # longer wanted by multi-user.target: /run is empty at boot, so the
              # first password of a boot has to be written by something.
              OnBootSec = "10s";
              OnCalendar = "daily";
              Persistent = true;
            };
          };
        })
      ]
    ))
  ];
}
