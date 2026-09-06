#!/bin/bash
# GIT_ASKPASS helper - credentials come from environment only
case "$1" in
  Username*) echo "${GIT_USERNAME:-Sh-TB}" ;;
  Password*) echo "$GH_TOKEN_VALUE" ;;
  *) echo "" ;;
esac
