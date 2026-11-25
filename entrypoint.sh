#!/bin/sh
# Startet die App als PUID/PGID, damit neue Dateien in /config und /data dem
# richtigen Benutzer gehören (Unraid: PUID=99 / PGID=100 = nobody:users).
set -e
PUID="${PUID:-99}"
PGID="${PGID:-100}"
umask "${UMASK:-000}"
mkdir -p /config
if [ "$(id -u)" = "0" ]; then
  # Nur das eigene appdata-Verzeichnis anpassen – deine Shares unter /data bleiben unangetastet.
  chown -R "$PUID:$PGID" /config 2>/dev/null || true
  exec setpriv --reuid="$PUID" --regid="$PGID" --clear-groups "$@"
fi
exec "$@"
