#!/bin/bash
# Steuerdienst (läuft als root): schaltet das VPN ein/aus, wenn die Weboberfläche
# den gewünschten Zustand in /config/vpn.desired ändert ("on"/"off"), und schreibt
# den aktuellen Status nach $STATE/status.json für die Oberfläche.
set -uo pipefail

VPN="${VPN_BIN:-/usr/local/bin/cloudupper-vpn}"
STATE="${VPN_STATE_DIR:-/run/cloudupper-vpn}"
DESIRED_FILE="${VPN_DESIRED_FILE:-/config/vpn.desired}"
KILLSWITCH="${VPN_KILLSWITCH:-true}"
mkdir -p "$STATE" && chmod 755 "$STATE"

current="off"; state="off"; message=""; changed="$(date +%s)"

desired() {
  local d
  d="$(tr -d '[:space:]' <"$DESIRED_FILE" 2>/dev/null || true)"
  [ "$d" = "on" ] && echo on || echo off
}

json_str() { local s="${1//\\/\\\\}"; s="${s//\"/\\\"}"; printf '"%s"' "${s//$'\n'/ }"; }

write_status() {
  local stats
  stats="$("$VPN" stats 2>/dev/null || echo '{}')"
  [ -n "$stats" ] || stats='{}'
  {
    printf '{"available":true,"desired":"%s","state":"%s","message":%s,"killswitch":%s,"changed":%s,"updated":%s,"wg":%s}\n' \
      "$(desired)" "$state" "$(json_str "$message")" "$KILLSWITCH" "$changed" "$(date +%s)" "$stats"
  } > "$STATE/status.json.tmp"
  chmod 644 "$STATE/status.json.tmp" && mv "$STATE/status.json.tmp" "$STATE/status.json"
}

apply() {
  local want="$1" out
  changed="$(date +%s)"
  if [ "$want" = "on" ]; then
    state="starting"; message="Tunnel wird aufgebaut …"; write_status
    if out="$("$VPN" up 2>&1)"; then
      state="up"; message=""
    else
      state="error"; message="$(grep -E 'FEHLER|WARNUNG' <<<"$out" | tail -n1 | sed 's/^\[vpn\] //')"
      [ -n "$message" ] || message="$(tail -n1 <<<"$out")"
    fi
  else
    state="stopping"; message="VPN wird ausgeschaltet …"; write_status
    out="$("$VPN" down 2>&1)" || true
    state="off"; message=""
  fi
  printf '%s\n' "$out" | sed "s/^/$(date '+%F %T') /" | tee -a "$STATE/vpn.log" >&2
  tail -n 200 "$STATE/vpn.log" > "$STATE/vpn.log.tmp" 2>/dev/null && mv "$STATE/vpn.log.tmp" "$STATE/vpn.log"
  current="$want"
  write_status
}

# Beim Start: gespeicherten Zustand herstellen, bevor die App startet
apply "$(desired)"
touch "$STATE/ready"
[ "${1:-}" = "--once" ] && exit 0

tick=0
while true; do
  want="$(desired)"
  if [ "$want" != "$current" ]; then
    apply "$want"
  elif (( tick % 5 == 0 )); then
    write_status
  fi
  tick=$((tick + 1))
  sleep 2
done
