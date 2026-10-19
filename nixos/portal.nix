# The captive portal.
#
# A phone that joins the appliance asks for a URL whose answer it already knows
# -- `connectivitycheck.gstatic.com/generate_204` and friends -- to decide
# whether the network reaches the internet. dnsmasq points those four names at
# the responder below (network.nix), which answers 302 to the page this module
# serves, and the OS reacts by offering "Sign in to network" and opening it.
# Without it the probe is REFUSED, the network is marked unusable, and a visitor
# is told only that there is no internet.
#
# The page does three things, and the first is the only one most visitors want:
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
# The box still says "no internet", and truthfully: it is an island with no
# upstream and advertises no default route. What changes is that the visitor is
# now offered a way in.
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

  # The two locations both page listeners carry.
  #
  # `secure` is what the page is told about the connection it is answering, and
  # it decides whether the certificate form is offered at all. Set on **both**
  # listeners rather than only on the TLS one, so a header a client invented is
  # replaced rather than passed through -- nothing outside this box can reach
  # the loopback port, but a value that is only ever written on the path where
  # it is true is a value somebody can forge on the path where it is not.
  portalLocations = secure: {
    "/" = {
      proxyPass = "http://127.0.0.1:${toString cfg.portal.listenPort}";
      extraConfig = ''
        proxy_set_header X-Loom-Secure "${if secure then "1" else "0"}";

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
        proxy_set_header X-Loom-Secure "${if secure then "1" else "0"}";

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
      mkdir --parents ${lib.escapeShellArg tlsDir}
      chgrp ${lib.escapeShellArg nginxGroup} ${lib.escapeShellArg tlsDir}
      chmod 750 ${lib.escapeShellArg tlsDir}

      # Only when there is nothing usable there. Writing a placeholder over the
      # real certificate would put the warning back for a day, on the one page
      # that exists to take it away -- but `-s` alone also kept an *expired*
      # pair: `tlsDir` is on the encrypted root and survives reboots, this
      # certificate is `-days 1`, and `loom-portal-certificate` loops until the
      # cluster answers without ever consulting expiry. On a box whose cluster
      # never comes up, every boot after the first short-circuited past replacing
      # it and nginx served an expired certificate indefinitely. `-checkend 0` is
      # the one-line version of what `loom-mtls-identity` does daily.
      if [ -s ${lib.escapeShellArg tlsCert} ] && [ -s ${lib.escapeShellArg tlsKey} ] \
        && openssl x509 -noout -checkend 0 -in ${lib.escapeShellArg tlsCert} \
          >/dev/null 2>&1; then
        exit 0
      fi

      umask 077
      openssl req -x509 -nodes -days 1 \
        -newkey rsa:2048 \
        -subj "/CN=${cfg.portal.host}" \
        -keyout ${lib.escapeShellArg tlsKey} \
        -out ${lib.escapeShellArg tlsCert} 2>/dev/null

      chgrp ${lib.escapeShellArg nginxGroup} ${lib.escapeShellArg tlsKey} ${lib.escapeShellArg tlsCert}
      chmod 640 ${lib.escapeShellArg tlsKey}
      chmod 644 ${lib.escapeShellArg tlsCert}

      # The marker the page reads. While it exists, 443 is answered by a
      # certificate nothing can verify -- `-days 1`, rsa:2048, self-signed
      # `CN=portal.loom` -- and the page must not offer a PKCS#12 over it: the
      # bundle carries an unencrypted private key, and "the connection was
      # encrypted" is not the property that matters when the key exchange is
      # authenticated by nothing. `loom-portal-certificate` removes it once the
      # cluster's own pair is in place, which on a first boot is hours away.
      : > ${lib.escapeShellArg tlsPlaceholderMarker}
      chgrp ${lib.escapeShellArg portalUser} ${lib.escapeShellArg tlsPlaceholderMarker}
      chmod 644 ${lib.escapeShellArg tlsPlaceholderMarker}
    '';
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
      namespace=${lib.escapeShellArg loomNamespace}
      secret=${lib.escapeShellArg cfg.portal.servingSecret}
      want_tls=${if enableTls then "1" else "0"}

      # Said once per change rather than once per attempt, the way mtls.nix's
      # issuer does it: a box waiting an hour for a bring-up should not fill the
      # journal with one line every ten seconds.
      said=""
      note() {
        if [ "$1" != "$said" ]; then
          said="$1"
          echo "$1"
        fi
      }

      read_secret_key() {
        local value
        value="$(kubectl --request-timeout=5s --namespace "$namespace" \
          get secret "$1" --output "jsonpath={.data.$2}" 2>/dev/null)" || return 1
        [ -n "$value" ] || return 1
        base64 --decode <<< "$value"
      }

      # Whatever the frontend's Ingress names, for a deployment that brought its
      # own certificate. Same fallback as cicd/generate_client_certificate.sh's
      # fetch_serving_anchor.
      ingress_secret() {
        kubectl --request-timeout=5s --namespace "$namespace" \
          get ingress --selector app.kubernetes.io/component=frontend \
          --output "jsonpath={.items[0].spec.tls[0].secretName}" 2>/dev/null || true
      }

      # Waiting forever is safe here, unlike in the issuer next door: nothing is
      # ordered behind this unit, the page works without it and says so, and a
      # visitor is not standing in front of it.
      until kubectl --request-timeout=5s --namespace "$namespace" \
        get secret "$secret" >/dev/null 2>&1; do
        alternative="$(ingress_secret)"
        if [ -n "$alternative" ] && [ "$alternative" != "$secret" ]; then
          note "Using '$alternative' from the frontend Ingress instead of '$secret'."
          secret="$alternative"
          continue
        fi
        note "Waiting for '$secret'; Loom has not got that far yet."
        sleep 10
      done

      work="$(mktemp --directory)"
      # shellcheck disable=SC2064
      trap "rm --recursive --force '$work'" EXIT

      # The anchor and the serving pair are not necessarily the same certificate.
      #
      # On the default path the chart makes `self-signed-cert` with `kubectl
      # create secret tls`, so it carries no `ca.crt` and the anchor is the leaf
      # itself -- nothing issued it, and a client that trusts this deployment
      # trusts that certificate as its own root. On the cert-manager path
      # (`certificate.enabled`) the secret carries both, and the anchor is the
      # issuer. Taking `tls.crt` in that case would hand the visitor a leaf to
      # trust on the one deployment where the leaf rotates underneath them.
      found=""
      for key in 'ca\.crt' 'tls\.crt'; do
        if read_secret_key "$secret" "$key" > "$work/anchor.pem" \
          && grep --quiet "BEGIN CERTIFICATE" "$work/anchor.pem"; then
          found="$key"
          break
        fi
      done
      if [ -z "$found" ]; then
        echo "Secret '$secret' carries no certificate this page could publish." >&2
        exit 1
      fi

      openssl x509 -noout -fingerprint -sha256 -in "$work/anchor.pem" \
        | cut --delimiter== --fields=2 > "$work/anchor.sha256"

      changed=0

      # Compared before it is written, and that is not tidiness. The reload below
      # is `reload-or-restart`, which on a box where nginx is down becomes a
      # restart -- and a restart drops the in-flight connections on
      # loom-mtls-ollama, which carry the assistant pane's token stream at a
      # 3600-second read timeout. Doing that every hour for no reason would be a
      # chat pane that goes blank on the hour.
      publish() {
        if cmp --silent "$1" "$2" 2>/dev/null; then
          return 0
        fi
        install --mode="$3" "$1" "$2"
        changed=1
      }

      publish "$work/anchor.pem" ${lib.escapeShellArg anchorFile} 644
      publish "$work/anchor.sha256" ${lib.escapeShellArg fingerprintFile} 644

      if [ "$want_tls" = 1 ]; then
        if ! read_secret_key "$secret" 'tls\.crt' > "$work/cert.pem" \
          || ! read_secret_key "$secret" 'tls\.key' > "$work/key.pem"; then
          echo "Secret '$secret' carries no serving pair; leaving the TLS listener as it is." >&2
          exit 0
        fi
        publish "$work/cert.pem" ${lib.escapeShellArg tlsCert} 644
        if ! cmp --silent "$work/key.pem" ${lib.escapeShellArg tlsKey} 2>/dev/null; then
          install --mode=640 --group=${lib.escapeShellArg nginxGroup} \
            "$work/key.pem" ${lib.escapeShellArg tlsKey}
          changed=1
        fi
        # The listener is now the cluster's own certificate -- the one the page
        # has been telling the visitor to trust -- so the page may offer a
        # private key over it. Until this point `_is_secure` was true of a
        # connection carrying the one-day placeholder, which is authenticated by
        # nothing and is in force for the hours a first boot takes.
        rm --force ${lib.escapeShellArg tlsPlaceholderMarker}
      fi

      if [ "$changed" = 1 ]; then
        echo "Published the serving certificate from '$secret' (anchor key: $found)."
        systemctl reload-or-restart nginx.service
      fi
    '';
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
      requests=${lib.escapeShellArg requestsDir}
      bundles=${lib.escapeShellArg bundlesDir}
      namespace=${lib.escapeShellArg loomNamespace}
      ca_secret=${lib.escapeShellArg cfg.mtls.caSecret}
      days=${toString cfg.portal.mtls.validityDays}

      current=""

      # Written to a dot-prefixed temporary and renamed, exactly as the bundle
      # directory below is, and for a sharper reason than tidiness.
      #
      # The page polls `bundles/<token>.error` every 100ms and unlinks it the
      # instant it appears. Creating the file and *then* chgrp-ing it left a
      # window of one fork-and-exec in which the page could take it away -- after
      # which `chgrp` failed, `set -e` aborted the script, and the EXIT trap found
      # `current` still set and wrote a second answer over a question already
      # answered. The unit went to `failed` on a perfectly ordinary
      # "cluster not ready", a stale file was left for the next run's reap, and a
      # visitor whose timing landed the other way was told the box could not issue
      # a certificate rather than that Loom was still starting.
      #
      # So the name the page watches for appears once, already owned and already
      # readable, and nothing touches it afterwards.
      refuse() {
        local temporary
        # `mktemp`, not a name derived from the token. `bundlesDir` is
        # 0730 root:loom-portal, so the portal user may create entries in it by
        # name -- and the portal generates the token itself, so it could plant
        # `bundles/.<token>.error.tmp` as a symlink before writing its request.
        # The redirect below opens O_CREAT|O_TRUNC through such a link, and the
        # chgrp and chmod follow it too: root truncating a file of the portal's
        # choosing, writing `cluster-not-ready` into it and handing it to the
        # portal group. `refuse` is reached on the ordinary cluster-not-ready
        # branch during every bring-up, so this was not an exotic path. The same
        # reasoning `put()` below already applies to the password file.
        temporary="$(mktemp --tmpdir="$bundles" ".tmp.XXXXXXXX")"
        printf '%s\n' "$2" > "$temporary"
        # --no-dereference for the same reason, belt to mktemp's braces.
        chgrp --no-dereference ${lib.escapeShellArg portalUser} "$temporary"
        chmod 640 "$temporary"
        # Cleared before the rename rather than after it: once the answer is
        # visible the trap below must not write a second one, and a failure
        # between here and the rename is better served by the page's own deadline
        # than by an answer that contradicts this one.
        current=""
        mv "$temporary" "$bundles/$1.error"
      }

      # TERM as well as EXIT, because TimeoutStartSec kills with SIGTERM and the
      # visitor whose request was in flight is watching a page that would
      # otherwise spin until its own deadline.
      cleanup() {
        if [ -n "$current" ] && [ ! -d "$bundles/$current" ]; then
          refuse "$current" issuer-failed
        fi
      }
      trap cleanup EXIT TERM

      # Anything abandoned. The page takes its own request back when it times out
      # and removes its own bundle once it has handed it over, so this only ever
      # catches what a crash or a closed tab left -- but a bundle holds an
      # unencrypted private key, so it is swept rather than left.
      find "$requests" -mindepth 1 -mmin +5 -delete 2>/dev/null || true
      find "$bundles" -mindepth 1 -maxdepth 1 -mmin +5 -exec rm --recursive --force {} + 2>/dev/null || true

      shopt -s nullglob
      for request in "$requests"/*.req; do
        token="$(basename "$request" .req)"

        # Validated before the name is ever joined to a path again. The page
        # generates these, so anything else in here came from something that
        # should not have been writing to this directory at all.
        if [ "''${#token}" -ne 32 ] || [ -n "''${token//[0-9a-f]/}" ]; then
          rm --force "$request"
          continue
        fi

        # The glob was expanded once, and a visitor whose page times out takes
        # their own request back -- so by the time this loop reaches an entry the
        # file may be gone. Under `set -euo pipefail` the sed below would then
        # exit 2 and abort the whole run mid-batch, with `current` still empty so
        # the trap writes no answer: a spurious `loom-portal-issue` failure in
        # `systemctl --failed`, which is a primary diagnostic on this box. The
        # batch itself recovers either way -- `PathExistsGlob` re-checks the
        # moment a triggered service exits -- but the noise is worth not making.
        [ -f "$request" ] || continue

        # Re-validated rather than trusted: the page checked it too, and a
        # downstream check is not a substitute for the one that decides.
        label="$(sed --quiet 's/^label=\([a-z0-9][a-z0-9-]\{0,23\}\)$/\1/p' "$request" 2>/dev/null | head --lines=1)" || label=""

        # Consumed before any work, so a retrigger of the path unit cannot hand
        # the same request to a second run.
        rm --force "$request"
        current="$token"

        # Deliberately no wait loop. mtls.nix's issuer waits out a bring-up
        # because nobody is watching it; here somebody is standing at a page, and
        # "Loom is still starting" is a better answer than a spinner.
        if ! kubectl --request-timeout=5s --namespace "$namespace" \
          get secret "$ca_secret" >/dev/null 2>&1; then
          refuse "$token" cluster-not-ready
          continue
        fi

        work="$bundles/.$token.work"
        rm --recursive --force "$work"
        mkdir --parents "$work"
        chmod 750 "$work"

        # The name is built here and never taken verbatim, so the worst a label
        # can do is choose 24 lowercase characters of a filename.
        if loom-client-certificate \
          --name "''${label:-visitor}-''${token:0:8}" \
          --days "$days" \
          --namespace "$namespace" \
          --out-dir "$work"; then
          chgrp --recursive ${lib.escapeShellArg portalUser} "$work"
          chmod --recursive g+rX "$work"
          # The directory itself also g+w, which is what lets the page shred the
          # bundle the moment it has handed it over: removing an entry needs
          # write on the containing directory, so with r-x alone every
          # `os.unlink` in `Spool._remove_tree` failed with EACCES and the rmdir
          # then failed ENOTEMPTY -- leaving an unencrypted private key on disk
          # until another request arrived to trigger the five-minute sweep, or
          # until reboot. It grants nothing new: `bundlesDir` is 0730
          # root:loom-portal, so the page can already unlink entries there by
          # name. The files stay g+r only.
          chmod g+w "$work"
          # A rename within one directory, so the page can never see a partial
          # bundle: either the directory is there and complete, or it is not.
          mv "$work" "$bundles/$token"
          current=""
          echo "Issued a visitor certificate for ''${label:-visitor}."
        else
          rm --recursive --force "$work"
          refuse "$token" issuer-failed
        fi
      done
    '';
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
        The hostnames dnsmasq answers with the portal address instead of
        REFUSED. network.nix reads this.

        One dedicated probe FQDN per vendor, and deliberately not the fallbacks
        `www.google.com` and `www.apple.com`: those are real sites people use,
        and claiming them would make this a blanket interception rather than an
        answer to a question only an OS asks. Losing a fallback costs nothing
        while the primary is answered.
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
      default = "http://${config.loom.portal.host}/";
      description = ''
        Where a probe is redirected. Plain http, because a portal webview will
        not accept the appliance's self-signed certificate -- see the header.

        The page rather than the frontend, which is what it used to be: the
        certificate a visitor needs, and on a mutual TLS box the identity they
        cannot get in without, are both on it, and "Open Loom" is the first thing
        on it.
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

              # Every path, every method, one answer. Probe URLs differ per vendor
              # and per OS release, and nothing else resolves to this address, so a
              # path this config has never heard of is likelier to be a probe than
              # not.
              #
              # 302 rather than 301: the URLs being answered belong to Google and
              # Apple, and a permanent redirect is cached -- a phone that kept this
              # one would go on believing connectivitycheck.gstatic.com is Loom long
              # after it left the appliance. `no-store` says the same thing to
              # anything that caches by header instead.
              locations."/" = {
                return = "302 ${cfg.portal.target}";
                extraConfig = ''
                  add_header Cache-Control "no-store" always;
                '';
              };
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
            # Nothing else is on this socket, so nginx would pick this server
            # anyway; said out loud so a connection with no SNI, or with the
            # address in it, is answered rather than left to whatever a later
            # change makes the default.
            default = true;
            serverName = "${cfg.portal.host} ${cfg.portalAddress}";
            onlySSL = true;
            sslCertificate = tlsCert;
            sslCertificateKey = tlsKey;
            locations = portalLocations true;
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
              state=${lib.escapeShellArg stateDir}

              # Words rather than a random string, and drawn by `diceware` from its
              # own EFF list rather than from a wordlist in this repository -- the
              # same reasoning, and the same tool, as the --lock-key passphrase in
              # cicd/build_appliance_image.sh.
              #
              # The y/z filter is kept even though the person typing this is on
              # their own phone rather than on a keyboard somebody else chose. One
              # box with two different rules for generating a passphrase is worse
              # than one filter that is merely unnecessary here, and rejection
              # sampling keeps the result uniform over what survives.
              passphrase=""
              for _ in $(seq 100); do
                candidate="$(diceware --no-caps --delimiter . --num ${toString cfg.portal.mtls.passwordWords})"
                if ! grep --quiet --extended-regexp '[yz]' <<< "$candidate"; then
                  passphrase="$candidate"
                  break
                fi
              done
              if [ -z "$passphrase" ]; then
                echo "No passphrase without [yz] in 100 draws; diceware or its list has changed." >&2
                exit 1
              fi

              # Temp file, chmod, rename -- the shape key-guard.nix's `put` uses,
              # so the page can never read a half-written password and refuse
              # somebody who typed the right one.
              put() {
                local temporary
                temporary="$(mktemp --tmpdir="$state" .password.XXXXXX)"
                printf '%s\n' "$2" > "$temporary"
                chgrp ${lib.escapeShellArg portalUser} "$temporary"
                chmod 640 "$temporary"
                mv "$temporary" "$1"
              }

              # Yesterday's is kept for one rotation. This runs at midnight and the
              # password is read off a screen, so there is a minute every day when
              # somebody is typing one the box has just replaced -- and that is the
              # worst possible moment for it to refuse a correct answer.
              if [ -s ${lib.escapeShellArg passwordFile} ]; then
                put ${lib.escapeShellArg previousPasswordFile} \
                  "$(cat ${lib.escapeShellArg passwordFile})"
              fi
              put ${lib.escapeShellArg passwordFile} "$passphrase"

              # And onto the login screen, which reads the file above at print time
              # and puts the password in the same block as everything else somebody
              # has to transcribe. Repaint, unless somebody is already logged in --
              # which is what loom-banner-refresh decides, and it says so by
              # exiting 1.
              loom-banner-refresh || true
            '';
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
