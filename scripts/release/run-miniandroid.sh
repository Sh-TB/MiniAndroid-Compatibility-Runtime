#!/bin/bash
# Launcher for the MiniAndroid Linux runtime package.
# The binary needs only standard distribution libraries (see README.txt);
# this wrapper simply runs it from the package directory.
DIR="$(cd "$(dirname "$0")" && pwd)"
exec "$DIR/miniandroid" "$@"
