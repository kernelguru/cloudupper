#!/bin/sh
# Startet die App als PUID/PGID (Standard 1000), damit Dateien in /config und /data
# dem richtigen Benutzer auf dem Host gehören.
set -e
PUID="${PUID:-1000}"
PGID="${PGID:-1000}"
mkdir -p /config /data
if [ "$(id -u)" = "0" ]; then
  chown -R "$PUID:$PGID" /config 2>/dev/null || true
  chown "$PUID:$PGID" /data 2>/dev/null || true
  exec setpriv --reuid="$PUID" --regid="$PGID" --clear-groups "$@"
fi
exec "$@"
