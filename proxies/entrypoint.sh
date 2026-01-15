#!/bin/sh
set -e
CFG="${CONFIG_PATH:-/etc/3proxy/3proxy.cfg}"

if [ ! -f "$CFG" ]; then
  echo "3proxy: config not found at $CFG"
  exit 1
fi

echo "3proxy: starting with config $CFG"
exec /usr/local/bin/3proxy "$CFG"