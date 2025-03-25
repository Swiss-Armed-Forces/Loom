# CICD

The Gitlab pipeline is currently split into 3 stage:

1. lint: Checks the python and node.js code quality.
2. test: Runs unit tests for for white box testing.
3. build: Conducts an integration test and docker container build. See the integration test for more information.

## Gitlab Runner installation

1. Install `docker` and `docker-compose`
2. Ensure that the host can pull docker images (maybe via a mirror), especially `gitlab/gitlab-runner`
3. `sudo CI_REGISTRATION_TOKEN=XXXXXXXXXX ./install_runner.sh`
