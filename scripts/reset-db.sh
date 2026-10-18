#!/bin/sh
# Compatibility entry point: schema initialization no longer deletes stored quarters.
set -eu
exec python3 src/main.py --migrate-only
