#!/usr/bin/env bash
set -euo pipefail

GITLAB_INSTANCE="${GITLAB_INSTANCE:-https://gitlab.com/}"
CI_REGISTRATION_TOKEN="${CI_REGISTRATION_TOKEN?Missing CI_REGISTRATION_TOKEN}"
DEFAULT_IMAGE="${DEFAULT_IMAGE:-docker}"
# shellcheck disable=SC1091
OS_ID="$(source "/etc/os-release"; echo "${ID}")"
USER="$(id -un)"

if [[ "${EUID}" -ne 0 ]]
	then echo "[-] Please run as root"
	exit 1
fi

DIR=$( cd -- "$( dirname -- "${BASH_SOURCE[0]}" )" &> /dev/null && pwd )

install_debian_pkg(){
	curl -L "https://packages.gitlab.com/install/repositories/runner/gitlab-runner/script.deb.sh" \
	| bash
	apt install -y gitlab-runner
}

install_fedora_pkg(){
	curl -L "https://packages.gitlab.com/install/repositories/runner/gitlab-runner/script.rpm.sh" \
	| bash
	yum install -y gitlab-runner
}

(
	cd "${DIR}"

	case "${OS_ID}" in
		fedora)
			install_fedora_pkg
		;;
		debian)
			install_debian_pkg
		;;
		*)
			echo >&2 "[!] OS_ID not supported: '${OS_ID}'"
			exit 1
		;;
	esac

	echo "[*] Register runner"
	# Note we need ulimit nofile= because of
	# https://github.com/NixOS/nix/issues/11258#issuecomment-2323063903
	gitlab-runner register \
		--non-interactive \
		--executor docker \
		--url "${GITLAB_INSTANCE}" \
		--registration-token "${CI_REGISTRATION_TOKEN}" \
		--ulimit "nofile=1024:1024" \
		--docker-volumes /certs/client \
		--docker-image "${DEFAULT_IMAGE}" \
		--docker-privileged \
		--docker-security-opt "label=disable" \
		--docker-security-opt "seccomp=unconfined" \
		--docker-devices "/dev/fuse"

	echo "[*] Starting runner"
	gitlab-runner start

	echo "[*] Installing daily cleanup cronjob"
	cat << EOF > /etc/cron.hourly/gitlab_runner_clear_cache
#!/usr/bin/env sh
docker system prune --volumes --force
EOF
	chmod +x /etc/cron.hourly/gitlab_runner_clear_cache

	echo "[*] Installing weekly cleanup cronjob"
	cat << EOF > /etc/cron.weekly/gitlab_runner_clear_cache
#!/usr/bin/env sh
docker system prune --volumes --all --force
docker volume prune --all --force
EOF
	chmod +x /etc/cron.weekly/gitlab_runner_clear_cache
)
