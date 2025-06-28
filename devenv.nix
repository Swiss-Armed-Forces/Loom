{
  pkgs,
  lib,
  config,
  inputs,
  ...
}:

let

  # local overlays: this can be removed
  # once we moved to devenv 1.4.2 which
  # adds support for local overlays
  overlay = final: prev: {

    # we have to disable the chromium
    # sandbox otherwise some (mostly electron)
    # apps won't run in containers and ubuntu (AppArmor)
    chromium = prev.chromium.override {
      commandLineArgs = "--no-sandbox";
    };
  };

  pkgs-stable = import inputs.nixpkgs-stable {
    system = pkgs.stdenv.system;
    config = pkgs.config;
    overlays = pkgs.overlays ++ [ overlay ];
  };
  pkgs-unstable = import inputs.nixpkgs-unstable {
    system = pkgs.stdenv.system;
    config = pkgs.config;
    overlays = pkgs.overlays ++ [ overlay ];
  };

  # fix locale
  use-locale = "C.UTF-8";
  custom-locales = pkgs.pkgs.glibcLocalesUtf8.override {
    allLocales = false;
    locales = [ "${use-locale}/UTF-8" ];
  };

  cicd-config = builtins.path { path = ./nix-dind/devenv.local.nix; };
in
{
  env = {
    # toggle CI/CD mode
    cicd = lib.mkDefault false;

    # set do not track
    # see:
    # - https://consoledonottrack.com/
    DO_NOT_TRACK = 1;

    # fix locale
    LOCALE_ARCHIVE = "${custom-locales}/lib/locale/locale-archive";
    LC_ALL = use-locale;
    LC_CTYPE = use-locale;
    LC_ADDRESS = use-locale;
    LC_IDENTIFICATION = use-locale;
    LC_MEASUREMENT = use-locale;
    LC_MESSAGES = use-locale;
    LC_MONETARY = use-locale;
    LC_NAME = use-locale;
    LC_NUMERIC = use-locale;
    LC_PAPER = use-locale;
    LC_TELEPHONE = use-locale;
    LC_TIME = use-locale;
    LC_COLLATE = use-locale;

    # poetry might fallback to query a keyring backend which might or might not exist.
    # this is bad. We don't want that. We don't need any keys.
    # https://www.reddit.com/r/learnpython/comments/zcb95y/comment/kdh0aka
    PYTHON_KEYRING_BACKEND = "keyring.backends.fail.Keyring";

    # Make minikube store all its metadata in the project root
    MINIKUBE_HOME = "${config.devenv.root}/.minikube";
  };

  # https://devenv.sh/packages/
  packages =
    with pkgs-stable;
    [
      # git
      git
      git-lfs

      # utils
      sysctl
      coreutils
      procps
      util-linux
      diffutils
      jq
      yq
      dos2unix
      curl
      pv
      openssl

      # k8s
      minikube
      kubectl
      skaffold
      kubernetes-helm

      # for frontend-api-generate
      jre

      # for software bill of materials (SBOM)
      syft

      # for unit testing
      libpst
      tshark
      binwalk
      cabextract
      imagemagick
      file
    ]
    #
    # The following dependencies are made available
    # for interactive devenv's only. Which means they
    # won't be available in the cicd pipeline
    #
    ++ (pkgs.lib.optionals (!config.env.cicd) [
      # for Frontend debugging
      chromium

      # utils
      vim

      # k8s
      k9s

      # minio
      minio-client

      # connect to CiCd runners
      tailscale
      dig

      # monitoring
      (btop.override { cudaSupport = true; })

      # for some reason, this is needed to make
      # the terminal in VScode work (or not ..)
      bashInteractive

      # ide
      # see: https://nixos.wiki/wiki/Visual_Studio_Code
      (vscode-with-extensions.override {
        vscodeExtensions =
          with vscode-extensions;
          [
            bbenoist.nix

            gitlab.gitlab-workflow

            ms-python.python
            ms-python.vscode-pylance
            ms-python.isort
            ms-python.black-formatter
            ms-python.debugpy
            vscode-extensions.ms-python.pylint
            vscode-extensions.ms-python.flake8

            ms-azuretools.vscode-docker
            ms-kubernetes-tools.vscode-kubernetes-tools
            redhat.vscode-yaml # required for vscode-kubernetes-tools
            tim-koehler.helm-intellisense

            dbaeumer.vscode-eslint
            esbenp.prettier-vscode

            timonwong.shellcheck

            davidanson.vscode-markdownlint

            mkhl.direnv
          ]
          ++ vscode-utils.extensionsFromVscodeMarketplace [
            {
              name = "mypy-type-checker";
              publisher = "ms-python";
              version = "2024.0.0";
              sha256 = "sha256-o2qmz8tAC4MG/4DTBdM1JS5slsUrlub4fbDulU42Bgg=";
            }
            {
              name = "autoflake-extension";
              publisher = "mikoz";
              version = "1.0.4";
              sha256 = "sha256-CtsJGlGsMmEePKTBQIu7vX15SkfdJo8zREJgVyztNTY=";
            }
            {
              name = "hadolint";
              publisher = "exiasr";
              version = "1.1.2";
              sha256 = "sha256-6GO1f8SP4CE8yYl87/tm60FdGHqHsJA4c2B6UKVdpgM=";
            }
          ];
      })
    ]);

  processes = {
    k8s-setup = {
      exec = "./up.sh --setup";
      process-compose = {
        is_elevated = true;
      };
    };

    k8s = {
      exec = "./up.sh --development";
      process-compose = {
        depends_on.k8s-setup.condition = "process_completed_successfully";
      };
    };

    ide = {
      exec = "code --wait $DEVENV_ROOT";
      process-compose = {
        availability = {
          restart = "always";
        };
      };
    };
  };

  # Disable cachix because cachix might cause
  # instabilities when fetching tarball for
  # nixpkgs-unstable
  cachix.enable = false;

  # https://devenv.sh/languages/
  languages.nix.enable = true;
  languages.python = {
    enable = true;
    # Note: we have to disable manylinux here,
    # because otherwise when using cli tools
    # from within python will segfault
    # more details:
    # https://github.com/cachix/devenv/issues/1469
    manylinux.enable = false;
    poetry = {
      enable = true;
      activate.enable = true;
    };
  };

  languages.javascript = {
    enable = true;
    directory = "Frontend";
    corepack.enable = true;
    pnpm = {
      enable = true;
      install.enable = true;
    };
  };
  languages.typescript.enable = true;

  # https://devenv.sh/pre-commit-hooks/
  pre-commit.hooks = {
    trim-trailing-whitespace.enable = true;

    #isort.enable = true;
    autoflake.enable = true;
    # missing: docformatter
    black.enable = true;
    flake8.enable = true;
    #pylint = {
    #  enable = true;
    #  entry = "pylint --rcfile .pylintrc";
    #};
    #mypy = {
    #  enable = true;
    #  entry = "mypy --exclude 'tests/*'";
    #};
    nixfmt-rfc-style.enable = true;

    shellcheck.enable = true;

    hadolint.enable = true;

    markdownlint.enable = true;
    markdownlint.settings.configuration = {
      MD013 = {
        line_length = 120;
        tables = false;
      };
    };

    eslint.enable = true;

    yamllint = {
      enable = true;
      settings.configuration = ''
        ignore: |
          pnpm-lock.yaml
          charts/templates/**
          charts/charts/**
      '';
    };
  };

  dotenv = {
    enable = true;
    disableHint = true;
  };

  enterShell = ''
    init(){
      (
        set -euo pipefail
        cd "${config.devenv.root}"

        # is interactive shell?
        if tty -s; then
          # - pull lfs artifacts
          # Note: we can not install lfs hooks because,
          # hooks are managed by devenv
          git lfs install --skip-repo
          git lfs pull
          # print help
          devenv-help
        fi

        echo "CI/CD mode: ${builtins.toJSON config.env.cicd}"
      )
    }
    if ! init; then
      echo "[!] Failed initializing shell!"
      exit 1
    fi

    # use dependency proxy
    CI_DEPENDENCY_PROXY_SERVER="''${CI_DEPENDENCY_PROXY_SERVER:-gitlab.com}"
    if docker-login-noninteractive "''${CI_DEPENDENCY_PROXY_SERVER}" &>/dev/null; then
      CI_DEPENDENCY_PROXY_GROUP_IMAGE_PREFIX="''${CI_DEPENDENCY_PROXY_SERVER}/swiss-armed-forces/cyber-command/cea/dependency_proxy/containers"
      export CI_DEPENDENCY_PROXY_GROUP_IMAGE_PREFIX
      echo "Using docker image dependency proxy: ''${CI_DEPENDENCY_PROXY_GROUP_IMAGE_PREFIX}"
    fi
  '';

  scripts.devenv-help = {
    description = "Print this help";
    exec = ''
      set -euo pipefail
      cd "${config.devenv.root}"

      echo
      echo "Helper scripts provided by the devenv:"
      echo
      sed -e 's| |XXXXXX|g' -e 's|=| |' <<EOF | column -t | sed -e 's|^|- |' -e 's|XXXXXX| |g'
      ${lib.generators.toKeyValue { } (lib.mapAttrs (name: value: value.description) config.scripts)}
      EOF
      echo
    '';
  };

  scripts.up = {
    description = "Start the application";
    exec = ''
      (
        set -euo pipefail
        cd "${config.devenv.root}"

        ./up.sh "''${@}"
      )
    '';
  };

  scripts.down = {
    description = "Stop the application";
    exec = ''
      (
        set -euo pipefail
        cd "${config.devenv.root}"

        echo "[*] Stopping loom"
        skaffold delete \
          "''${@}"

        (
          echo "[*] Stopping traefik"
          cd traefik
          ./skaffold delete \
            "''${@}"
        )
      )
    '';
  };

  scripts.build = {
    description = "Build the application";
    exec = ''
      (
        set -euo pipefail
        cd "${config.devenv.root}"

        ./cicd/build.sh "''${@}"
      )
    '';
  };

  scripts.build-helm = {
    description = "Build the helm chart and push it to package registry";
    exec = ''
      (
        set -euo pipefail
        cd "${config.devenv.root}"

        ./cicd/build_helm.sh "''${@}"
      )
    '';
  };

  scripts.lint = {
    description = "Lint the code";
    exec = ''
      (
        set -euo pipefail
        cd "${config.devenv.root}"

        echo "[*] Running lint.sh"
        ./cicd/lint.sh

        echo "[*] Running check-syntax.sh"
        ./cicd/check-syntax.sh

        echo "[*] Checking for whitspace errors"
        ./cicd/check_whitespace_errors.sh

        echo "[*] Checking for dos2unix errors"
        ./cicd/check_dos2unix_errors.sh

        echo "[*] Checking for leftover TODO's"
        ./cicd/check_todo.sh

        echo "[*] Checking deployment requests"
        ./cicd/check_requests.sh

        echo "[*] Linting successful!"
      )
    '';
  };

  scripts.lint-fix = {
    description = "Auto fix the code (if possible)";
    exec = ''
      (
        set -euo pipefail
        cd "${config.devenv.root}"

        ./cicd/check-syntax.sh \
          --fix \
          "''${@}"
      )
    '';
  };

  scripts.generate-openapi-schema = {
    description = "Print the openapi-schema.json";
    exec = ''
      (
        set -euo pipefail
        cd "${config.devenv.root}"

        ./cicd/generate_openapi_schema.py \
          "''${@}"
      )
    '';
  };

  scripts.frontend-test = {
    description = "Test the frontend";
    exec = ''
      (
        set -euo pipefail
        cd "''${DEVENV_ROOT}/Frontend"

        pnpm test run \
          "''${@}"
      )
    '';
  };

  scripts.frontend-build = {
    description = "Build the frontend";
    exec = ''
      (
        set -euo pipefail
        cd "''${DEVENV_ROOT}/Frontend"

        pnpm run build \
          "''${@}"
      )
    '';
  };

  scripts.frontend-audit = {
    description = "Audit the frontend";
    exec = ''
      (
        set -euo pipefail
        cd "''${DEVENV_ROOT}/Frontend"

        pnpm audit \
          "''${@}"
      )
    '';
  };

  scripts.backend-test = {
    description = "Test the backend";
    exec = ''
      (
        set -euo pipefail
        cd "''${DEVENV_ROOT}/backend"

        python -m pytest \
          --cov=. \
          --cov-config=.coveragerc \
          --cov-report=term \
          --cov-report=xml \
            "''${@}"
      )
    '';
  };

  scripts.poetry-lock = {
    description = "Regenrate all poetry lockfiles";
    exec = ''
      (
        set -euo pipefail
        cd "${config.devenv.root}"

        ./cicd/update-poetry-lock.sh \
          "''${@}"
      )
    '';
  };

  scripts.wipe-data = {
    description = "Wipe all data stored in loom";
    exec = ''
      (
        set -euo pipefail
        cd "${config.devenv.root}"

        poetry run \
          integrationtest/utils/wipe_data.py \
          "''${@}"
      )
    '';
  };

  scripts.kubernetes-image-backup-restore = {
    description = "Backup/Restore kubernetes images";
    exec = ''
      (
        set -euo pipefail
        cd "${config.devenv.root}"

        ./cicd/docker_image_backup_restore.py \
          --minikube \
          "''${@}"
      )
    '';
  };

  scripts.kubernetes-pause = {
    description = "Pause kubernetes cluster";
    exec = ''
      (
        set -euo pipefail
        cd "${config.devenv.root}"

        ./cicd/kubernetes_pause.sh \
          "''${@}"
      )
    '';
  };

  scripts.kubernetes-stop = {
    description = "Stop kubernetes cluster";
    exec = ''
      (
        set -euo pipefail
        cd "${config.devenv.root}"

        ./cicd/kubernetes_stop.sh \
          "''${@}"
      )
    '';
  };

  scripts.kubernetes-delete = {
    description = "Delete kubernetes cluster";
    exec = ''
      (
        set -euo pipefail
        cd "${config.devenv.root}"

        ./cicd/kubernetes_delete.sh \
          "''${@}"
      )
    '';
  };

  scripts.kubernetes-delete-namespace = {
    description = "Delete namespace in kubernetes";
    exec = ''
      (
        set -euo pipefail
        cd "${config.devenv.root}"

        ./cicd/kubernetes_delete_namespace.sh \
          "''${@}"
      )
    '';
  };

  scripts.kubernetes-prune = {
    description = "Remove unused data in kubernetes";
    exec = ''
      (
        set -euo pipefail
        cd "${config.devenv.root}"

        ./cicd/kubernetes_prune.sh \
          "''${@}"
      )
    '';
  };

  scripts.kubernetes-fetch-all-pod-logs = {
    description = "Fetch all logs from all pods and write them to logs/";
    exec = ''
      (
        set -euo pipefail
        cd "${config.devenv.root}"

        ./cicd/fetch_all_pod_logs.sh \
          "''${@}"
      )
    '';
  };

  scripts.docker-minikube = {
    description = "Docker cli wrapper communicating to the minikube docker daemon";
    exec = ''
      (
        set -euo pipefail
        cd "${config.devenv.root}"

        MINIKUBE_EVAL=$(minikube -p minikube docker-env)
        eval "''${MINIKUBE_EVAL}"

        docker \
          "''${@}"
      )
    '';
  };

  scripts.docker-login-noninteractive = {
    description = "Calling docker login without user interaction";
    exec = ''
      (
        set -euo pipefail
        cd "${config.devenv.root}"

        ./cicd/docker_login_noninteractive.sh \
          "''${@}"
      )
    '';
  };

  scripts.docker-image-backup-restore = {
    description = "Backup/Restore docker images";
    exec = ''
      (
        set -euo pipefail
        cd "${config.devenv.root}"

        ./cicd/docker_image_backup_restore.py \
          "''${@}"
      )
    '';
  };

  scripts.docker-container-stop = {
    description = "Stop all docker containers";
    exec = ''
      (
        set -euo pipefail
        cd "${config.devenv.root}"

        ./cicd/docker_container_stop.sh \
          "''${@}"
      )
    '';
  };

  scripts.docker-prune = {
    description = "Prune all docker resources";
    exec = ''
      (
        set -euo pipefail
        cd "${config.devenv.root}"

        ./cicd/docker_prune.sh \
          "''${@}"
      )
    '';
  };

  scripts.nix-dind = {
    description = "Build nix-dind image";
    exec = ''
      (
        set -euo pipefail
        cd "${config.devenv.root}"

        ./cicd/nix-dind.sh \
          "''${@}"
      )
    '';
  };

  scripts.frontend-api-generate = {
    description = "Generate frontent api typescript files";
    exec = ''
      (
        set -euo pipefail
        cd "${config.devenv.root}"

        ./cicd/generate_frontend_api.sh \
          "''${@}"
      )
    '';
  };

  scripts.generate-third-party = {
    description = "Generate THIRD-PARTY.md";
    exec = ''
      (
        set -euo pipefail
        cd "${config.devenv.root}"

        ./cicd/generate_third_party.sh \
          "''${@}"
      )
    '';
  };

  scripts.frontend-static-generate = {
    description = "Generate static assets for Frontend";
    exec = ''
      (
        set -euo pipefail
        cd "${config.devenv.root}"

        ./cicd/generate_frontend_static.sh \
          "''${@}"
      )
    '';
  };

  scripts.test-git-file-changed = {
    description = "Test if a git file was changed";
    exec = ''
      (
        set -euo pipefail
        cd "${config.devenv.root}"

        ./cicd/test_git_file_changed.sh \
          "''${@}"
      )
    '';
  };

  scripts.run-integrationtest = {
    description = "Run integrationtest";
    exec = ''
      (
        set -euo pipefail
        cd "${config.devenv.root}"

        ./cicd/run_integrationtest.sh
          "''${@}"
      )
    '';
  };

  scripts.cicd-mode-enter = {
    description = "Enter devenv CI/CD mode";
    exec = ''
      (
        set -euo pipefail
        cd "${config.devenv.root}"

        cp "${builtins.toString cicd-config}" devenv.local.nix
      )
    '';
  };

  scripts.cicd-mode-leave = {
    description = "Leave devenv CI/CD mode";
    exec = ''
      (
        set -euo pipefail
        cd "${config.devenv.root}"

        rm \
          --force \
          devenv.local.nix
      )
    '';
  };

  scripts.install-runner = {
    description = "Installing a new CI/CD runner on this system";
    exec = ''
      (
        set -euo pipefail
        cd "${config.devenv.root}"

        ./cicd/install_runner.sh
          "''${@}"
      )
    '';
  };

  scripts.chrome-loom-wrapped = {
    description = "Start a wrapped chrome version";
    exec = ''
      (
        set -euo pipefail
        cd "${config.devenv.root}"

        ./cicd/chrome_wrapped.sh \
          "''${@}"
      )
    '';
  };

  scripts.transfer-loom = {
    description = "Build a loom transer file";
    exec = ''
      (
        set -euo pipefail
        cd "${config.devenv.root}"

        ./helpers/transfer_loom.sh \
          "''${@}"
      )
    '';
  };

  scripts.update-traefik = {
    description = "Update the traefik helm charts in this repo";
    exec = ''
      (
        set -euo pipefail
        cd "${config.devenv.root}"

        ./traefik/update.sh \
          "''${@}"
      )
    '';
  };

  scripts.generate-client-certificate = {
    description = "Generate client certificates";
    exec = ''
      (
        set -euo pipefail
        cd "${config.devenv.root}"

        ./cicd/generate_client_certificate.sh \
          "''${@}"
      )
    '';
  };

  # See full reference at https://devenv.sh/reference/options/
}
