#!/bin/bash

set -e

BRANCH=$1
TMPDIR=$(mktemp -d)
echo "Using branch $BRANCH, using temp dir $TMPDIR!, kernel $(uname -r), uptime $(uptime)"

echo "Performing git clone"
git clone --branch "$BRANCH" https://github.com/sched-ext/scx.git "$TMPDIR"

echo "Building..."
cd "$TMPDIR/scheds/rust/scx_rustland/"
cargo build --release

echo "Ensuring no scx is running..."
sudo systemctl disable scx
sudo systemctl stop scx

echo "Starting scheduler..."
timeout -s SIGKILL 5m sudo target/release/scx_rustland

echo "Deleting $TMPDIR"
rm -rf "$TMPDIR"

