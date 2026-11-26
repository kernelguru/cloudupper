#!/bin/sh
# Startet die App als PUID/PGID, damit neue Dateien in /config und /data dem
# richtigen Benutzer gehören (Unraid: PUID=99 / PGID=100 = nobody:users).
set -e
PUID="${PUID:-99}"
PGID="${PGID:-100}"
umask "${UMASK:-000}"
mkdir -p /config
# Optionales WireGuard-VPN (z.B. Proton VPN) mit Kill-Switch – muss als root laufen
if [ "${VPN_ENABLED:-false}" = "true" ]; then
  if [ "$(id -u)" != "0" ]; then
    echo "[vpn] FEHLER: Für das VPN muss der Container als root starten (PUID/PGID statt --user verwenden)." >&2
    exit 1
  fi
  /usr/local/bin/cloudupper-vpn || { echo "[vpn] VPN konnte nicht gestartet werden – Container wird beendet, damit nichts am VPN vorbei übertragen wird." >&2; exit 1; }
fi
if [ "$(id -u)" = "0" ]; then
  # Nur das eigene appdata-Verzeichnis anpassen – deine Shares unter /data bleiben unangetastet.
  chown -R "$PUID:$PGID" /config 2>/dev/null || true
  # Privater WireGuard-Schlüssel nur für root lesbar
  if [ -d /config/wireguard ]; then
    chown -R root:root /config/wireguard 2>/dev/null || true
    chmod 700 /config/wireguard && chmod 600 /config/wireguard/* 2>/dev/null || true
  fi
  exec setpriv --reuid="$PUID" --regid="$PGID" --clear-groups "$@"
fi
exec "$@"
