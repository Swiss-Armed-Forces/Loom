# CICD

The Gitlab pipeline is currently split into 3 stage:

1. lint: Checks the python and node.js code quality.
2. test: Runs unit tests for for white box testing.
3. build: Conducts an integration test and docker container build. See the integration test for more information.

## The `GITLAB_TOKEN` CI/CD variable

The jobs in the `generate` stage regenerate committed files and end in
`devenv shell -- git-file-changed`, which pushes whatever changed to the merge request's
branch and then fails the job, because the commit the pipeline ran against is not the one
that passes. `cicd/git_file_changed.py` reads `GITLAB_TOKEN` for the two parts of that it
cannot do with the job token: pushing to a fork, and creating the follow-up merge request
pipeline. `cicd/aitools/config.py` takes the same variable as its API token. The scripts
also accept `PROJECT_ACCESS_TOKEN` as a second name for the same credential.

**It has to be the personal access token of a [service account][service-accounts].** The
`api` scope is enough on its own: for a personal access token, `api` also grants push over
Git-over-HTTP, so `write_repository` adds nothing. Give the account a role in this project
that may *merge* to the merge request's target branch — `main` grants merge to Maintainers,
so Maintainer — and add it to the project rather than to the group, which would hand it
every project in the group. Store the variable **masked and not protected**: merge request
pipelines run on `refs/merge-requests/<iid>/head`, which is not a protected ref, so a
protected variable is missing exactly when the fork push needs it.

**A project access token cannot do this job.** Its repository scope is "the repository in
the project", and it [cannot be used to access resources in other projects][pat-scopes]. A
fork is another project, so its push is refused with
`403 You are not allowed to push code to this project` no matter what the merge request
allows, and no scope widens that.

A service account in a role below the one that may merge — Developer, while `main` grants
merge to Maintainers — is refused with that same line, so the message does not say which of
the two is wrong. The account's role is the half to check first, because the pipeline
trigger needs only Developer and keeps working either way.

The push into a fork needs all of:

- the author enabled "Allow commits from members who can merge to the target branch" on the
  merge request (`allow_collaboration`)
- neither project is private
- the fork's source branch is not protected
- the token's account may merge to the target branch in this project

When any of them is missing the job writes `changed-files/fork-update.patch` into its
artifacts, prints the `git apply` line and fails, leaving the commit to the contributor.

The token is in the environment of a job whose `.gitlab-ci.yml` and scripts come from the
contributor's branch whenever a fork's merge request pipeline is run in this project, which
`ci_allow_fork_pipelines_to_run_in_parent_project` permits. Masking keeps it out of the job
log and does nothing else, so run a fork's pipeline here only for a contribution that may
hold the token.

[service-accounts]: https://docs.gitlab.com/user/profile/service_accounts/
[pat-scopes]: https://docs.gitlab.com/security/tokens/access_token_scopes/

## Gitlab Runner installation

1. Install `docker` and `docker-compose`
2. Ensure that the host can pull docker images (maybe via a mirror), especially `gitlab/gitlab-runner`
3. `sudo CI_REGISTRATION_TOKEN=XXXXXXXXXX ./install_runner.sh`

The script also writes the two cleanup cronjobs the host needs to keep its disk
in check. The hourly one skips its run while the host has a job in flight, so it
cannot collect a layer an image pull is still writing - a host registered before
that was added keeps the old cronjob until `install_runner.sh` is run again.
