# The platform dimension: which physical box this closure is for.
#
# Deliberately separate from `system`. Architecture and machine are different
# questions -- two platforms could share an architecture, and everything that
# actually differs between the DGX Spark and the GMKtec EVO-X2 (which NIC to
# claim, which initrd modules are needed) is a property of the machine rather
# than of aarch64 vs x86_64.
#
# This file declares the options only. The values live in platforms/<id>.nix,
# and nixos/default.nix picks one from its `platform` argument.
{ config, lib, ... }:
{
  options.loom.platform = {
    id = lib.mkOption {
      type = lib.types.enum [
        "spark"
        "evo-x2"
        "nuc12"
      ];
      description = "Identifier of the appliance platform this closure targets.";
    };

    description = lib.mkOption {
      type = lib.types.str;
      description = ''
        Human-readable name of the box. Shown on the console banner, which on an
        appliance with no remote access is the only place it can reach anyone.
      '';
    };

    nixSystem = lib.mkOption {
      type = lib.types.str;
      description = ''
        The nix system this platform must be built for. nixos/default.nix
        asserts that it matches the `system` argument, so a
        `--platform evo-x2 --system aarch64-linux` mismatch fails during
        evaluation rather than at boot.
      '';
    };

    netMatch = lib.mkOption {
      type = lib.types.attrsOf lib.types.str;
      description = ''
        systemd `[Match]` section identifying the wired interface that serves the
        appliance network. network.nix renames whatever matches to `loom0`, so
        that the static address, the dnsmasq binding and the banner never have to
        guess a kernel-assigned name.

        Keep this specific. A broad match (`Type = "ether"`) would also claim the
        interface of any VM this configuration is evaluated in, including the
        NixOS test driver's.
      '';
      example = {
        Driver = "mlx5_core";
      };
    };

    wifiMatch = lib.mkOption {
      type = lib.types.nullOr (lib.types.attrsOf lib.types.str);
      default = null;
      description = ''
        systemd `[Match]` section identifying the radio the access point runs on,
        or `null` if this platform has no AP-capable one. wifi.nix renames
        whatever matches to `loomwl0`, for the same reason network.nix renames the
        wired NIC: nothing may depend on a kernel-assigned name.

        `null` is what makes `--wifi` fail during evaluation rather than on a box
        that boots without the access point it was built for.

        `Type = "wlan"` is the right default. Unlike the wired `netMatch`, a broad
        match is safe here -- it cannot claim an ethernet NIC or the NixOS test
        driver's virtio device -- and no one has yet confirmed which driver each
        box's radio binds to. Pin it once someone has run this on the hardware:
          iw list | grep -A15 'Supported interface modes'   # needs a '* AP' line
          udevadm info /sys/class/net/<iface> | grep ID_NET_DRIVER=
      '';
      example = {
        Driver = "mt7921e";
      };
    };

    gpuVendor = lib.mkOption {
      type = lib.types.nullOr (
        lib.types.enum [
          "amd"
          "nvidia"
        ]
      );
      default = null;
      description = ''
        The GPU vendor Ollama can be offloaded to on this box, or `null` for a
        box that runs the whole stack on its CPU.

        Non-null makes the appliance pass `--gpus <vendor>` to up.sh, which
        selects `charts/values-{amd,nvidia}-gpu.yaml`, enables minikube's
        matching device-plugin addon, and asks `minikube start` for the GPU. It
        also puts the vendor's SMI tool in `loom.toolchain`, because up.sh's
        `validate_environment` requires it whenever `--gpus` is set.

        This is a claim about the box, not a preference: it means somebody has
        confirmed that the kernel driver binds here *and* that the vendor's
        compute stack enumerates the device. The driver alone is not enough --
        every platform in this directory loads one, since that is what puts the
        installer menu on the monitor.

        Get it wrong and the box does not merely fall back to CPU. up.sh's
        `check_host_resources` counts GPUs through the SMI tool and hard-exits
        below `LOOM_MIN_GPU`, so a box that cannot see its own GPU serves
        nothing at all -- on an appliance with no remote access. That failure is
        what `build-appliance-image --no-gpu` exists to get out of, and it needs
        a new stick.
      '';
    };

    runsAiServices = lib.mkOption {
      type = lib.types.bool;
      default = config.loom.platform.gpuVendor != null;
      defaultText = lib.literalExpression "config.loom.platform.gpuVendor != null";
      description = ''
        Whether this box deploys Ollama.

        Defaults to "only where there is a GPU to run it on", which is the
        rule rather than a coincidence: every model in the image is sized for
        offload, and the embedding step runs over *every* indexed file. On a CPU
        that does not degrade the pipeline, it defines it -- an indexing run that
        would take an afternoon takes days, and the queue never drains. Shipping
        the service and letting the operator discover that is worse than not
        shipping it, because the box looks like it is working.

        Set it explicitly to say something the GPU does not already say. The
        NUC 12 does, for memory; a CPU-only box that somebody has measured and
        is happy with would set it true.

        False makes the appliance pass `--disable-ai` to up.sh, which stops the
        service being deployed *and* stops the indexing pipeline calling it --
        without the second half every indexed file would retry an embedding task
        fifteen times against a service that is not there
        (charts/values-disable-ai-services.yaml).

        What the box loses: summaries, translation, image descriptions,
        auto-tagging, embeddings, and therefore semantic search and RAG. What it
        keeps: full-text search, OCR, metadata extraction and archive import.

        console.nix also drops its assistant pane, because that pane is an
        opencode pointed at the cluster's own Ollama and would have nothing to
        talk to.
      '';
    };

    meetsResourceMinimum = lib.mkOption {
      type = lib.types.bool;
      default = true;
      description = ''
        Whether this box clears `LOOM_MIN_MEMORY` in vars.sh.

        False makes the appliance pass `--no-resources`, not merely
        `--skip-check_host_resources`. The host check is the first obstacle but
        not the real one: even with the AI services disabled the chart asks for
        about 19.4 GiB of memory *requests*, so a box with ~12 GiB allocatable
        would get past up.sh and then leave most of its pods Pending forever.
        `--no-resources` strips requests and limits, and skips the host check on
        the way past, so one flag covers both.

        The cost is real: with no limits, nothing stops one container starving
        the others, and a heavy indexing run on a box this size ends in OOM kills
        rather than orderly eviction. Set this only for a machine somebody has
        actually run Loom on, and expect it to be usable rather than comfortable.
      '';
    };

    runsAutoscaling = lib.mkOption {
      type = lib.types.bool;
      default = config.loom.platform.meetsResourceMinimum;
      defaultText = lib.literalExpression "config.loom.platform.meetsResourceMinimum";
      description = ''
        Whether this box scales its compute-intensive services with load.

        True makes the appliance pass `--scaling` to up.sh, which installs KEDA
        (`keda/`, a vendored chart -- nothing is fetched at run time) and applies
        `charts/values-scaling.yaml`: worker and reaper scale on RabbitMQ queue
        depth, tika and gotenberg on CPU. Without it every service stays at the
        one replica the chart declares, so an indexing run uses a fraction of a
        box that has cores to spare.

        The flag reaches both boot modes, and it has to. `--scaling` is the only
        thing that installs KEDA, so a stick whose first-time setup ran without
        it has no KEDA images in minikube's store -- and run mode, being
        air-gapped, cannot go and get them.

        Defaults to `meetsResourceMinimum`, which is not a convenience: up.sh
        rejects `--scaling` alongside `--no-resources` outright
        (`validate_environment`), because the scaling values file turns on a
        resource quota that requires requests on every pod and `--no-resources`
        is what strips them. On an appliance that pairing is not a usage error
        printed to a terminal -- it is a box that never comes up, with no remote
        access to find out why. modes.nix asserts the two agree at evaluation
        time so the stick cannot be built.
      '';
    };

    extraInitrdModules = lib.mkOption {
      type = lib.types.listOf lib.types.str;
      default = [ ];
      description = ''
        Platform-specific additions to `boot.initrd.availableKernelModules`, for
        both the appliance and the installer. The shared list covers USB and
        NVMe; anything a particular box needs to reach its disk or its keyboard
        belongs here.
      '';
    };
  };
}
