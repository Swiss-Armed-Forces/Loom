# The appliance network.
#
# In run mode the box is an island: it owns its subnet, hands out addresses, and
# resolves every `*.loom` name to itself. A visitor plugs a laptop into the
# ethernet port and https://frontend.loom works with no configuration on their
# side -- which is the main way Loom is used on these boxes.
#
# In setup mode it is an ordinary DHCP client, because the box needs real
# internet exactly once: to populate minikube's image store.
{
  config,
  lib,
  pkgs,
  loomSubnet,
  loomInterface,
  minikubeIp,
  ...
}:
let
  boxAddress = "${loomSubnet}.1";
  poolStart = "${loomSubnet}.100";
  poolEnd = "${loomSubnet}.200";
  isRun = config.loom.mode == "run";

  # The appliance never refers to a kernel-assigned interface name. Predictable
  # naming gives `enp1s0f0np0` on the Spark and `enp*` on the EVO-X2, neither of
  # which a single image could hardcode -- and a wrong guess boots a box with a
  # static address on an interface that does not exist, no DHCP, no DNS, and no
  # sshd to fix it from. So udev renames the platform's NIC to a fixed name and
  # everything below pins to that.
  applianceInterface = "loom0";

  # `loomInterface` is the escape hatch: empty means "use the platform's match".
  #
  # It is kept as an OriginalName match, but that ONLY fires when the operator
  # passes the kernel's own name -- `eth0`. OriginalName matches the udev
  # INTERFACE property as it stands when the .link file is evaluated, and at that
  # moment the predictable name does not exist yet: `enp2s0` is the *output* of
  # NamePolicy in 99-default.link, which sorts after this file. So
  # `--interface enp2s0`, which is the name an operator actually reads off the
  # box and the one Documentation/appliance.md tells them to use, matched nothing
  # and produced a box with no loom0 -- the exact failure the flag exists to fix.
  #
  # Rather than demand a name nobody can discover, the override is applied at
  # runtime by loom-interface-fallback below, which renames whatever is called
  # `loomInterface` once udev has settled. This match stays as the fast path for
  # anyone who does pass a kernel name.
  netMatch =
    if loomInterface != "" then { OriginalName = loomInterface; } else config.loom.platform.netMatch;

  # With the access point enabled (wifi.nix), the wired NIC stops being the thing
  # the appliance addresses and becomes one port of a bridge. Everything that
  # used to pin to `loom0` -- the static address, dnsmasq's binding, the firewall
  # -- moves onto the bridge, so that a client is on the same segment, in the same
  # pool, behind the same resolver whether it arrived over the air or over copper.
  #
  # `loom0` keeps meaning "the physical NIC" in both builds. Only the name of the
  # interface holding the address changes.
  wifiEnabled = config.loom.wifi.enable;
  bridgeInterface = config.loom.wifi.bridge;

  # `isRun` as well as `wifiEnabled`, because the bridge is built by the run-mode
  # branch below and the radio by wifi.nix's, which is gated the same way. Every
  # use inside this file already sits under `mkIf isRun`, so that term changes
  # nothing here -- it is there for the option this is exported as, which is read
  # from modules that are not mode-gated. In setup mode the answer is the wired
  # NIC in both builds, `loombr0` being an interface that does not exist yet.
  serviceInterface = if isRun && wifiEnabled then bridgeInterface else applianceInterface;

  # Where the fallback below records what it claimed, for loom-network-check and
  # for anyone debugging the box afterwards.
  fallbackRecord = "/run/loom/interface-fallback";

  # Every wired NIC on the box, most-stable-device-path first.
  #
  # "Wired NIC" is four exclusions, and each one matters:
  #
  #   no `device` symlink   virtual interfaces -- bridges (loombr0), veth,
  #                         docker0, tun/tap. minikube and docker create these on
  #                         a running box, and claiming one would be absurd.
  #   a DEVTYPE in uevent   the kernel's own classification, and the reason this
  #                         is not a check for `wireless/` instead: an ordinary
  #                         wired NIC declares no DEVTYPE at all, while `wlan`,
  #                         `wwan`, `bridge`, `veth` and friends all declare one.
  #                         `wwan` is the case that motivated it -- a cellular
  #                         modem presents as ARPHRD_ETHER with a real device and
  #                         no `wireless/` directory, so the obvious radio checks
  #                         miss it and the box would have served DHCP down a
  #                         mobile connection.
  #   type != 1             not ARPHRD_ETHER: ppp, sit, ib and friends.
  #   lo                    obviously.
  #
  # Sorted by the PCI address behind the device rather than by interface name, so
  # a box with more than one port picks the same one on every boot instead of
  # whichever udev happened to finish first.
  loom-wired-nics = pkgs.writeShellApplication {
    name = "loom-wired-nics";
    runtimeInputs = with pkgs; [
      coreutils
      gawk
      gnugrep
    ];
    text = ''
      for path in /sys/class/net/*; do
          name="$(basename "''${path}")"

          if [ "''${name}" = lo ]; then
              continue
          fi
          if [ ! -e "''${path}/device" ]; then
              continue
          fi
          if grep --quiet '^DEVTYPE=' "''${path}/uevent" 2>/dev/null; then
              continue
          fi
          if [ "$(cat "''${path}/type" 2>/dev/null || echo 0)" != 1 ]; then
              continue
          fi

          printf '%s %s\n' \
              "$(basename "$(readlink --canonicalize "''${path}/device")")" \
              "''${name}"
      done | sort | awk '{ print $2 }'
    '';
  };

  # The ports a visitor may reach on the appliance address.
  #
  # Exactly the two the firewall opens, and deliberately not the rest of what
  # traefik's Service carries (imap 143, amqp 5672, redis 6379/6380, prometheus
  # 9090 -- traefik/values.yaml). `minikube tunnel` used to publish all seven on
  # this address as a side effect of how it works; only the firewall kept them
  # from being reachable. Here the list is the decision.
  exposedPorts = [
    80
    443
  ];

  # Reaching Loom from the appliance network, as two iptables chains.
  #
  # traefik binds :80 and :443 with a `hostPort` (traefik/values.yaml:26,31),
  # which puts them on the minikube node -- the docker container at
  # `minikubeIp`. That is already what `networking.hosts` in box.nix pins every
  # `*.loom` name to, and it is how the box itself reaches its own stack. So the
  # whole job here is to make a packet that a visitor sent to the appliance
  # address arrive there too.
  #
  # This replaces `up.sh --expose`, which did the same job with
  # `minikube tunnel`. That is not a route: with the docker driver minikube
  # shells out to the system `ssh` client and forwards each service port over a
  # connection into the node. The appliance never had `ssh` on `loom.service`'s
  # PATH -- `environment.systemPackages` does not reach a unit -- so every
  # forward failed with "executable file not found" and nothing ever listened on
  # the appliance address. DHCP and DNS worked, and the box served nothing.
  #
  # DNAT is the better mechanism here regardless of that bug: no ssh, no
  # long-lived root process that has to outlive a oneshot unit, and the client's
  # own address survives into traefik's access log instead of a tunnel endpoint.
  #
  # Both chains are ours, which is what makes install and teardown exact: the
  # rules can be flushed and the chains removed without touching anything docker
  # or the NixOS firewall put there.
  loom-expose = pkgs.writeShellApplication {
    name = "loom-expose";
    runtimeInputs = [ pkgs.iptables ];
    text = ''
      readonly INTERFACE=${lib.escapeShellArg serviceInterface}
      readonly BOX=${lib.escapeShellArg boxAddress}
      readonly NODE=${lib.escapeShellArg minikubeIp}
      readonly PORTS=${lib.escapeShellArg (lib.concatMapStringsSep " " toString exposedPorts)}
      readonly MULTIPORT=${lib.escapeShellArg (lib.concatMapStringsSep "," toString exposedPorts)}

      # Our own chains, jumped to from a hook each table guarantees us.
      readonly NAT_CHAIN=LOOM-EXPOSE
      readonly FORWARD_CHAIN=LOOM-FORWARD

      up() {
          # ---------------------------------------------------------------
          # nat PREROUTING: the appliance address becomes the minikube node.
          #
          # Created-or-flushed rather than created-if-absent, so a restart
          # rebuilds the rules instead of appending a second copy of them.
          # ---------------------------------------------------------------
          iptables --table nat --new-chain "''${NAT_CHAIN}" 2>/dev/null \
              || iptables --table nat --flush "''${NAT_CHAIN}"

          if ! iptables --table nat --check PREROUTING \
              --jump "''${NAT_CHAIN}" 2>/dev/null; then
              iptables --table nat --insert PREROUTING --jump "''${NAT_CHAIN}"
          fi

          local port
          for port in ''${PORTS}; do
              iptables --table nat --append "''${NAT_CHAIN}" \
                  --in-interface "''${INTERFACE}" \
                  --destination "''${BOX}" \
                  --protocol tcp --destination-port "''${port}" \
                  --jump DNAT --to-destination "''${NODE}:''${port}"
          done

          # ---------------------------------------------------------------
          # filter FORWARD: and then it has to be allowed across.
          #
          # This is the half that is easy to miss. dockerd sets the FORWARD
          # policy to DROP, so a DNAT'd packet crossing from the appliance
          # NIC to the minikube bridge is dropped by default and the symptom
          # is indistinguishable from the DNAT not being there at all.
          #
          # DOCKER-USER is docker's documented hook for this: it is jumped to
          # ahead of every docker-generated FORWARD rule and docker never
          # edits its contents. Created here only as a fallback -- `After`
          # and `Requires` on docker.service mean it normally exists already,
          # and creating it ourselves would otherwise leave a chain nothing
          # jumps to.
          # ---------------------------------------------------------------
          iptables --new-chain "''${FORWARD_CHAIN}" 2>/dev/null \
              || iptables --flush "''${FORWARD_CHAIN}"

          iptables --new-chain DOCKER-USER 2>/dev/null || true
          if ! iptables --check FORWARD --jump DOCKER-USER 2>/dev/null; then
              iptables --insert FORWARD --jump DOCKER-USER
          fi
          if ! iptables --check DOCKER-USER \
              --jump "''${FORWARD_CHAIN}" 2>/dev/null; then
              iptables --insert DOCKER-USER --jump "''${FORWARD_CHAIN}"
          fi

          # Matched on the node's address rather than on the bridge it is
          # behind: that bridge is `br-<docker network id>`, which changes
          # every time the cluster is deleted and recreated.
          iptables --append "''${FORWARD_CHAIN}" \
              --in-interface "''${INTERFACE}" \
              --destination "''${NODE}" \
              --protocol tcp --match multiport --dports "''${MULTIPORT}" \
              --jump ACCEPT

          # The replies. docker's own per-network rules happen to cover these
          # today, which is not something to depend on for the direction that
          # makes the whole thing work.
          iptables --append "''${FORWARD_CHAIN}" \
              --out-interface "''${INTERFACE}" \
              --match conntrack --ctstate RELATED,ESTABLISHED \
              --jump ACCEPT

          echo "[*] Loom is exposed on ''${BOX} ports ''${MULTIPORT} (via ''${NODE})."
      }

      # Never fails. This runs as ExecStop, including on the way to a
      # shutdown that is about to discard the whole ruleset anyway, and a
      # rule that somebody already removed by hand is not a failure worth
      # refusing to stop over.
      down() {
          if iptables --table nat --check PREROUTING \
              --jump "''${NAT_CHAIN}" 2>/dev/null; then
              iptables --table nat --delete PREROUTING --jump "''${NAT_CHAIN}" || true
          fi
          iptables --table nat --flush "''${NAT_CHAIN}" 2>/dev/null || true
          iptables --table nat --delete-chain "''${NAT_CHAIN}" 2>/dev/null || true

          if iptables --check DOCKER-USER \
              --jump "''${FORWARD_CHAIN}" 2>/dev/null; then
              iptables --delete DOCKER-USER --jump "''${FORWARD_CHAIN}" || true
          fi
          iptables --flush "''${FORWARD_CHAIN}" 2>/dev/null || true
          iptables --delete-chain "''${FORWARD_CHAIN}" 2>/dev/null || true
      }

      case "''${1:-}" in
          up)   up   ;;
          down) down ;;
          *)
              echo >&2 "usage: loom-expose up|down"
              exit 1
              ;;
      esac
    '';
  };
in
{
  # Exported rather than kept local because the name is not derivable from
  # outside: whether the address sits on `loom0` or on `loombr0` depends on
  # --wifi and on the boot mode, and console.nix -- which pins btop's net box to
  # this interface -- has no business recomputing that. /etc/loom/network.conf's
  # LOOM_INTERFACE is the same value written for humans; this is the one modules
  # read.
  options.loom.serviceInterface = lib.mkOption {
    type = lib.types.str;
    default = serviceInterface;
    readOnly = true;
    internal = true;
    description = ''
      The interface carrying the appliance address, serving DHCP and answering
      `*.loom`: the bridge when the access point is enabled, the wired NIC
      otherwise. `loom0` always means the physical port, in both builds.
    '';
  };

  options.loom.autoSelectInterface = lib.mkOption {
    type = lib.types.bool;
    default = true;
    internal = true;
    description = ''
      Claim a wired NIC as `loom0` when the platform's `netMatch` selected
      nothing.

      Without this, an image installed on a box the match does not cover comes up
      with no `loom0` at all -- and since the address, the dnsmasq binding, the
      firewall and the banner all pin to that name, the box cannot serve its
      network. With no sshd and no `nixos-rebuild`, recovering means building and
      flashing another stick. A box with exactly one wired port has no ambiguity
      to protect against and should simply work.

      Only ever runs when the match found nothing, so no supported platform
      changes behaviour. It also runs when `--interface` was given and did not
      match, deliberately: a pin that missed is the same failure as a match that
      missed, and the console says the NIC was claimed automatically either way.

      Off in tests/appliance.nix, which asserts the opposite -- that a VM whose
      only NIC is virtio comes up without `loom0`.
    '';
  };

  config = lib.mkMerge [
    # -------------------------------------------------------------------------
    # Run mode: static address, DHCP server, wildcard DNS.
    # -------------------------------------------------------------------------
    (lib.mkIf isRun {
      networking.useDHCP = false;
      networking.interfaces.${serviceInterface}.ipv4.addresses = [
        {
          address = boxAddress;
          prefixLength = 24;
        }
      ];

      # No upstream resolver: there is nothing upstream. Pointing at one would
      # only add a timeout to every lookup that is not ours.
      networking.nameservers = [ "127.0.0.1" ];

      services.dnsmasq = {
        enable = true;
        resolveLocalQueries = false;
        settings = {
          interface = serviceInterface;
          # Refuse to answer on anything but our own link, so the box can never
          # act as a rogue DHCP server if it is cabled into a real network.
          bind-interfaces = true;

          dhcp-range = "${poolStart},${poolEnd},255.255.255.0,12h";
          dhcp-option = [
            # No default gateway -- stated, because leaving option 3 out does
            # NOT leave it out.
            #
            # dnsmasq(8): "By default, dnsmasq sends some standard options to
            # DHCP clients, the netmask and broadcast address are set to the
            # same as the host running dnsmasq, and the DNS server and default
            # route are set to the address of the machine running dnsmasq." So
            # an omitted option:router is an advertised option:router, and the
            # only way to suppress one dnsmasq provides a default for is to
            # name it with no value, as here.
            #
            # What that cost: every lease told the visitor's laptop that the
            # appliance was its default gateway. A wired link outranks wifi on
            # metric almost everywhere, so the new route won, and from then on
            # *all* of that laptop's off-link traffic -- not just *.loom -- was
            # handed to a box that has no upstream. ip_forward is on for the
            # DNAT below, so the packets were accepted and then dropped rather
            # than refused. Plugging into Loom took the visitor off the
            # internet, on every interface they had.
            #
            # The box is an island: the client needs no route to reach it,
            # being on the same segment, and there is nothing behind it to
            # route to.
            "option:router"
            "option:dns-server,${boxAddress}"
          ];

          # Wildcard, so this covers every name under .loom rather than just
          # the 22 currently in vars.sh.
          address = "/loom/${boxAddress}";

          no-resolv = true;
          no-hosts = true;
          domain-needed = true;
          bogus-priv = true;
          log-dhcp = true;
        };
      };

      networking.firewall = {
        allowedTCPPorts = [ 53 ];
        allowedUDPPorts = [
          53
          67 # DHCP server
        ];
      };

      # DNAT'd traffic is routed, not delivered locally, so this is no longer
      # something to leave to dockerd -- which does enable it, as a side effect
      # of starting, on a box where nothing has declared it.
      boot.kernel.sysctl."net.ipv4.ip_forward" = true;

      # The rules above, with a lifecycle. See `loom-expose` for what they do
      # and why they replaced `up.sh --expose`.
      systemd.services.loom-expose = {
        description = "Publish Loom on the appliance address";
        wantedBy = [ "multi-user.target" ];
        # DOCKER-USER is created by dockerd, and half the rules go in it.
        after = [ "docker.service" ];
        requires = [ "docker.service" ];
        # Ahead of the stack it exposes. Nothing breaks in the other order --
        # bring-up takes hours and the rules can be installed at any point
        # during it -- but an operator reading the journal should not have to
        # wonder whether a box that is serving nothing yet is also unexposed.
        before = [ "loom.service" ];
        # A `systemctl restart docker` rebuilds the FORWARD chain. The
        # contents of DOCKER-USER survive that by docker's own contract, but
        # the box should not be relying on a contract for the one thing that
        # makes it reachable -- this reinstalls the rules afterwards, in the
        # right order, because of `after` above.
        partOf = [ "docker.service" ];
        serviceConfig = {
          Type = "oneshot";
          RemainAfterExit = true;
          ExecStart = "${lib.getExe loom-expose} up";
          ExecStop = "${lib.getExe loom-expose} down";
        };
      };

      # A record of the generated subnet, for whoever debugs the box later
      # without access to the machine that built the stick.
      # Deliberately carries no passphrase. This file is 0644 and the banner
      # reads it as the operator; the WPA key is interpolated into loom-info
      # from the closure instead (box.nix).
      environment.etc."loom/network.conf".text = ''
        # Generated by build-appliance-image. Informational only -- the live
        # values come from the NixOS configuration, not from this file.
        # LOOM_INTERFACE holds the address and serves DHCP; LOOM_WIRED_INTERFACE
        # is the port to plug a cable into. They differ only when the access
        # point is enabled and both are ports of a bridge.
        LOOM_INTERFACE=${serviceInterface}
        LOOM_WIRED_INTERFACE=${applianceInterface}
        LOOM_SUBNET=${loomSubnet}.0/24
        LOOM_BOX_ADDRESS=${boxAddress}
        LOOM_DHCP_POOL=${poolStart}-${poolEnd}
      ''
      + lib.optionalString wifiEnabled ''
        LOOM_WIFI_INTERFACE=${config.loom.wifi.interface}
        LOOM_WIFI_SSID=${config.loom.wifi.ssid}
      '';
    })

    # -------------------------------------------------------------------------
    # The bridge that makes wired and wireless the same network. Run mode with
    # --wifi only; wifi.nix owns the radio itself.
    # -------------------------------------------------------------------------
    (lib.mkIf (isRun && wifiEnabled) {
      # Declared with NO members, which looks wrong and is the whole point.
      #
      # The scripted bridge (nixpkgs network-interfaces-scripted.nix) sets
      # `bindsTo` on the .device unit of every interface it is told to enslave.
      # Naming loom0 here would therefore bind the bridge -- and so the address,
      # dnsmasq and every *.loom name -- to an ethernet port being present. A box
      # deployed for its access point, with nothing plugged into the wired port,
      # would come up with no address at all and no way in to find out why.
      #
      # So the bridge is created unconditionally and the ports attach to it:
      # loom0 below, and the radio by hostapd's own `bridge=` (wifi.nix).
      networking.bridges.${bridgeInterface}.interfaces = [ ];

      systemd.services.loom-bridge-attach = {
        description = "Attach the wired port to the appliance bridge";
        wantedBy = [ "network.target" ];
        after = [
          "${bridgeInterface}-netdev.service"
          "systemd-udev-settle.service"
        ];
        # Before the address, so a cabled client cannot get a DHCP lease over a
        # port that is not in the bridge yet.
        before = [ "network-addresses-${bridgeInterface}.service" ];
        serviceConfig = {
          Type = "oneshot";
          RemainAfterExit = true;
        };
        path = [ pkgs.iproute2 ];
        # Never fails. A missing loom0 is already reported by
        # loom-network-check, and taking the boot down here would cost the
        # access point too -- the one way left into a box in that state.
        script = ''
          if [ ! -e /sys/class/net/${applianceInterface} ]; then
            echo "${applianceInterface} is not present; bridge ${bridgeInterface} starts with the radio only"
            exit 0
          fi
          ip link set dev ${applianceInterface} master ${bridgeInterface}
          ip link set dev ${applianceInterface} up
        '';
      };

      # STP is off on a freshly created bridge, and with it off the kernel puts
      # ports straight into forwarding. Pinned anyway, and asserted by the test:
      # if a kernel ever did apply the default 15-second forward delay here, the
      # symptom would be a phone whose first DHCPDISCOVER is swallowed and which
      # then self-assigns a 169.254 address -- a failure that looks like a broken
      # AP rather than like a bridge timer.
      systemd.services.loom-bridge-tune = {
        description = "Pin forwarding behaviour on the appliance bridge";
        wantedBy = [ "network.target" ];
        after = [ "${bridgeInterface}-netdev.service" ];
        before = [ "network-addresses-${bridgeInterface}.service" ];
        serviceConfig = {
          Type = "oneshot";
          RemainAfterExit = true;
        };
        script = ''
          echo 0 >/sys/class/net/${bridgeInterface}/bridge/stp_state
          echo 0 >/sys/class/net/${bridgeInterface}/bridge/forward_delay
        '';
      };

      # dnsmasq binds an address rather than an interface name (bind-interfaces),
      # so it has to start after that address exists on the bridge.
      systemd.services.dnsmasq = {
        after = [ "network-addresses-${bridgeInterface}.service" ];
        wants = [ "network-addresses-${bridgeInterface}.service" ];
      };
    })

    # -------------------------------------------------------------------------
    # Setup mode: ordinary client, so skaffold can reach the registries.
    # -------------------------------------------------------------------------
    (lib.mkIf (!isRun) {
      networking.useDHCP = lib.mkForce true;
      services.dnsmasq.enable = false;
    })

    # -------------------------------------------------------------------------
    # A stable name for the appliance NIC, in both modes.
    #
    # .link files are applied by udev whether or not systemd-networkd is running
    # (nixpkgs says so in networkd.nix, right above the option), so this works
    # alongside the scripted/dhcpcd networking the appliance actually uses.
    # -------------------------------------------------------------------------
    {
      systemd.network.links."10-${applianceInterface}" = {
        matchConfig = netMatch;
        linkConfig.Name = applianceInterface;
      };

      environment.systemPackages = [ loom-wired-nics ];
    }

    # -------------------------------------------------------------------------
    # And a fallback, for the box the match does not cover.
    #
    # The .link file above is a driver match, so an image installed on hardware
    # nobody wrote a platform for renames nothing and comes up with no loom0 --
    # no address, no DHCP, no *.loom, and no way to fix it short of a new stick.
    # This claims a wired port instead.
    #
    # With more than one candidate it picks rather than refuses, which looks
    # reckless and is the opposite: platforms/evo-x2.nix already makes the
    # argument, because both its Realtek ports match the same driver and udev
    # decides between them. A box that came up on the wrong port is fixed by
    # moving the cable; a box with no loom0 at all is not fixable at the console
    # at all. Picking is strictly the better failure.
    # -------------------------------------------------------------------------
    (lib.mkIf (config.loom.autoSelectInterface || loomInterface != "") {
      systemd.services.loom-interface-fallback = {
        description = "Claim a wired NIC as ${applianceInterface} if none matched";
        wantedBy = [ "network-pre.target" ];
        # network-pre.target is the hook NixOS's own firewall unit uses, and it
        # is what puts this ahead of every address, bridge and dnsmasq unit
        # without having to name each of them -- including the ones that only
        # exist in the --wifi build.
        before = [ "network-pre.target" ];
        wants = [ "network-pre.target" ];
        # udev has to have finished renaming whatever it was going to rename,
        # otherwise this races the .link file it exists to back up.
        after = [ "systemd-udev-settle.service" ];
        serviceConfig = {
          Type = "oneshot";
          RemainAfterExit = true;
          # Journal only, for the reason given on loom-network-check below.
          StandardOutput = "journal";
          StandardError = "journal";
        };
        path = with pkgs; [
          coreutils
          iproute2
          loom-wired-nics
        ];
        script = ''
          readonly OVERRIDE=${lib.escapeShellArg loomInterface}
          readonly AUTO_SELECT=${if config.loom.autoSelectInterface then "1" else "0"}

          # Deliberately not brought up here: the scripted network configures and
          # raises it, and in setup mode dhcpcd does.
          #
          # Written through a temporary file, like key-guard.nix's state, so the
          # console check can never read half a record.
          claim() {
            local chosen="''${1}" reason="''${2}" alternatives="''${3:-}"

            # Never fail the boot over this. A device that refuses to be renamed
            # leaves the box where it would have been anyway, and
            # loom-network-check still reports it on the console.
            if ! ip link set dev "''${chosen}" down \
              || ! ip link set dev "''${chosen}" name ${applianceInterface}; then
              echo "[!] Could not rename ''${chosen} to ${applianceInterface}."
              return 1
            fi

            echo "[*] Claimed ''${chosen} as ${applianceInterface} (''${reason})."

            mkdir --parents /run/loom
            {
              printf 'LOOM_FALLBACK_INTERFACE=%s\n' "''${chosen}"
              printf 'LOOM_FALLBACK_REASON=%s\n' "''${reason}"
              printf 'LOOM_FALLBACK_ALTERNATIVES=%s\n' "''${alternatives}"
            } >${fallbackRecord}.tmp
            mv ${fallbackRecord}.tmp ${fallbackRecord}
          }

          if [ -e /sys/class/net/${applianceInterface} ]; then
            echo "[*] ${applianceInterface} already exists; udev claimed it."
            exit 0
          fi

          # An explicit --interface first, and regardless of AUTO_SELECT: the
          # operator named a port, which is an instruction rather than a guess.
          # This is the path that makes the flag work at all -- see the netMatch
          # comment above for why the .link file cannot do it by itself.
          if [ -n "''${OVERRIDE}" ]; then
            if [ -e "/sys/class/net/''${OVERRIDE}" ]; then
              claim "''${OVERRIDE}" override || true
              exit 0
            fi
            echo "[!] --interface named ''${OVERRIDE}, which does not exist on this box."
          fi

          if [ "''${AUTO_SELECT}" != 1 ]; then
            exit 0
          fi

          mapfile -t candidates < <(loom-wired-nics)

          if [ "''${#candidates[@]}" -eq 0 ]; then
            echo "[!] No wired interface to claim as ${applianceInterface}."
            exit 0
          fi

          claim "''${candidates[0]}" auto "''${candidates[*]:1}" || true
        '';
      };
    })

    {

      # If the match is wrong, everything above silently does nothing and the box
      # comes up unreachable -- with no sshd, the console is the only way to find
      # out why. Say so there, loudly, rather than leaving someone to guess.
      #
      # Three outcomes now, not one: no interface at all, an interface the
      # fallback above had to claim, or nothing to report.
      systemd.services.loom-network-check = {
        description = "Report how the appliance interface was selected";
        wantedBy = [ "multi-user.target" ];
        after = [
          "systemd-udev-settle.service"
          "loom-interface-fallback.service"
        ];
        # Same ordering trick as box.nix's loom-issue.service, and for the same
        # reason: the warning below is written as an issue fragment, so it has
        # to exist before any getty renders the issue. getty-pre.target is
        # passive -- nothing else pulls it into the transaction -- hence `wants`
        # as well as `before`, and the `before` has to name it: `wants` alone
        # orders nothing at all, which left the only diagnostic an operator can
        # see racing the login screen on the exact boot it exists to report.
        before = [
          "loom.service"
          "getty-pre.target"
        ];
        wants = [ "getty-pre.target" ];
        serviceConfig = {
          Type = "oneshot";
          RemainAfterExit = true;
          # Journal only. This used to be "journal+console", which -- with no
          # `console=` on the command line -- put it on the active VT. See
          # modes.nix for why that had to stop. The warning still reaches
          # somebody standing at the box, through the issue fragment below,
          # which is a better place for it: the login screen holds it until a
          # key is pressed instead of scrolling it past at boot.
          StandardOutput = "journal";
          StandardError = "journal";
        };
        # Never fails: this is a diagnostic, and blocking the boot of an
        # appliance whose only interface is missing helps nobody.
        path = with pkgs; [
          coreutils
          loom-wired-nics
        ];
        script = ''
          fragment=/run/issue.d/60-loom-network.issue

          # Sorts after box.nix's 50-loom.issue, so this lands under the banner
          # and above agetty's press-ENTER prompt. No backslashes anywhere in
          # the text: agetty reads them as issue escapes. Written through a
          # temporary file for the same reason loom-issue.service is -- a getty
          # respawning mid-write must never read half a message.
          report() {
            mkdir --parents /run/issue.d
            cat >"''${fragment}.tmp"
            mv "''${fragment}.tmp" "''${fragment}"
            # And to the journal, so `journalctl -u loom-network-check` has it.
            cat "''${fragment}"
          }

          if [ ! -e /sys/class/net/${applianceInterface} ]; then
            # With the fallback in place this no longer means "the match missed"
            # -- it means there was no wired port to claim either.
            {
              echo "[!] ${applianceInterface} does not exist -- no address, no DHCP, no *.loom."
              echo "[!] No wired interface was found to claim. Present instead:"
              for candidate in /sys/class/net/*; do
                name="$(basename "$candidate")"
                if [ "$name" = lo ]; then
                  continue
                fi
                echo "[!]   $name"
              done
              echo "[!] If one of those is in fact wired, rebuild with --interface <name>."
            } | report
            exit 0
          fi

          if [ -e ${fallbackRecord} ]; then
            # shellcheck source=/dev/null
            . ${fallbackRecord}

            # An explicit --interface did what it was told; that is not news for
            # the login screen, and the journal already has it.
            if [ "$LOOM_FALLBACK_REASON" = override ]; then
              rm --force "''${fragment}"
              exit 0
            fi

            {
              echo "[*] ${applianceInterface} is $LOOM_FALLBACK_INTERFACE, claimed automatically:"
              echo "[*] this image has no platform match for the NIC in this box."
              if [ -n "$LOOM_FALLBACK_ALTERNATIVES" ]; then
                echo "[*] Other wired ports: $LOOM_FALLBACK_ALTERNATIVES"
                echo "[*] If nothing reaches the box, move the cable to one of those."
              fi
              echo "[*] To pin it, rebuild with --interface $LOOM_FALLBACK_INTERFACE,"
              echo "[*] or add a platform for this machine."
            } | report
            exit 0
          fi

          # Matched properly. Clear anything an earlier boot left behind.
          rm --force "''${fragment}"
          exit 0
        '';
      };
    }

    # -------------------------------------------------------------------------
    # Radios off in both modes.
    #
    # Software disable, module blacklist and an rfkill block. Generic on purpose
    # -- this covers the Spark's radios and the EVO-X2's MediaTek Wi-Fi/BT alike.
    # A firmware-level disable in the box's own BIOS is the only true guarantee
    # and is a documented manual step -- see Documentation/appliance.md.
    #
    # Bluetooth is unconditional. --wifi opts a box into an access point, not
    # into a radio free-for-all, and nothing in Loom has ever wanted BT.
    # -------------------------------------------------------------------------
    {
      # wpa_supplicant, i.e. joining someone else's network. Never wanted, in
      # either build: the access point is hostapd, which is the other direction.
      networking.wireless.enable = false;
      networking.networkmanager.enable = false;
      hardware.bluetooth.enable = false;

      boot.blacklistedKernelModules = [
        "bluetooth"
        "btusb"
        "btintel"
        "btbcm"
        "btrtl"
      ]
      # The 802.11 stack itself, without which hostapd has nothing to drive.
      # Dropping these two from the blacklist is the whole of what --wifi
      # unblanks at the kernel level.
      ++ lib.optionals (!wifiEnabled) [
        "cfg80211"
        "mac80211"
      ];

      systemd.services.loom-rfkill-block = {
        description = if wifiEnabled then "Hard-block bluetooth" else "Hard-block all radios";
        wantedBy = [ "multi-user.target" ];
        serviceConfig = {
          Type = "oneshot";
          RemainAfterExit = true;
          # `rfkill block` exits non-zero when there is nothing to block, which
          # on a box with the modules blacklisted is the expected case.
          ExecStart = "${pkgs.util-linux}/bin/rfkill block ${if wifiEnabled then "bluetooth" else "all"}";
          SuccessExitStatus = [
            0
            1
          ];
        };
      };
    }
  ];
}
