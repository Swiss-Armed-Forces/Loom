# Integration tests

The integration tests ensure the functionality of the existing code by simulating interactions on the entire multi-container Docker application.

The Pytest integration tests are located in the `integrationtest/tests` folder.

## CI job `integrationtest_docker`

The integration tests are executed during the last stage of the GitLab CI/CD pipeline.

## Local debugging

It is recommended to debug and create new Pytest integration tests in a local environment where the tests run directly on the machine and communicate with the multi-container application over host mapped ports.

### Prepare the local environment

The integration tests can be executed locally in the development environment. Use `run-integrationtest` to execute them.

#### Explanation

Local testing and debugging via IDE is possible because those tests are executed locally where as on the gitlab CI pipeline they run in a docker container within the container network. As a consequence the host names configured in the integration tests are dependant on where they run. For this purpose `integrationtest/utils/settings.py` provides a wrapper which decides when to use localhost or the container network host.

### Start debugging

If this environment variable is **NOT** set, the Pytests will use localhost instead the container network host names which is necessary as the Pytests are performing requests from outside the container network.

We recommend the use of an IDE to which supports Pytests for ease of use.
The Visual Studio Code instance that is part of the devenv is configured to allow debugging.
