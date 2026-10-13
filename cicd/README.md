# CICD

The Gitlab pipeline is currently split into 3 stage:

1. lint: Checks the python and node.js code quality.
2. test: Runs unit tests for for white box testing.
3. build: Conducts an integration test and docker container build. See the integration test for more information.

## Gitlab Runner installation

1. Install `docker` and `docker-compose`
2. Ensure that the host can pull docker images (maybe via a mirror), especially `gitlab/gitlab-runner`
3. `sudo CI_REGISTRATION_TOKEN=XXXXXXXXXX ./install_runner.sh`

The script also writes the two cleanup cronjobs the host needs to keep its disk
in check. The hourly one skips its run while the host has a job in flight, so it
cannot collect a layer an image pull is still writing - a host registered before
that was added keeps the old cronjob until `install_runner.sh` is run again.
