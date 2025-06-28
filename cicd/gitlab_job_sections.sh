#!/usr/bin/env bash
# Create collapsible section in bash script with a preheader
# This script just provides the functions to manage gitlab
# job-log sections. It does not perform any actual actions.
#
# see:
#  - https://docs.gitlab.com/ci/jobs/job_logs/#custom-collapsible-sections

# Start a gitlab job log section
# $1 : name of the section
# $2 (optional) : description of the section
# If the description is not provided, the name will be used as the description
section_start() {
  local section_title
  section_title="${1}" && shift
  local section_description
  section_description="${1:-${section_title}}"

  local date_now
  date_now=$(date +%s)
  echo -e "section_start:${date_now}:${section_title}[collapsed=true]\r\e[0K${section_description}"
}

# End a gitlab job log section
# $1 : name of the section
section_end() {
  local section_title
  section_title="${1}" && shift

  local date_now
  date_now=$(date +%s)
  echo -e "section_end:${date_now}:${section_title}\r\e[0K"
}
