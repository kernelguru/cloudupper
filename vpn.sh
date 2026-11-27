#!/bin/bash
# WireGuard-VPN (z.B. Proton VPN) für den gesamten Container-Verkehr – mit Kill-Switch.
#
# Erwartet eine normale WireGuard-Konfiguration (z.B. von account.protonvpn.com →
# Downloads → WireGuard-Konfiguration) unter /config/wireguard/wg0.conf.
# Benötigt: --cap-add=NET_ADMIN und das WireGuard-Kernel-Modul (bei Unraid vorhanden).
#
# DRY_RUN=1 gibt nur die Befehle aus, ohne etwas zu verändern (zum Testen).
set -euo pipefail

CONF="${WG_CONFIG:-/config/wireguard/wg0.conf}"
IFACE=wg0
STATE="${VPN_STATE_DIR:-/run/cloudupper-vpn}"
KILLSWITCH="${VPN_KILLSWITCH:-true}"
LAN_NETWORK="${LAN_NETWORK:-192.168.0.0/16,172.16.0.0/12,10.0.0.0/8,100.64.0.0/10}"
DRY="${DRY_RUN:-0}"

log() { echo "[vpn] $*"; }
die() { echo "[vpn] FEHLER: $*" >&2; exit 1; }
run() { if [ "$DRY" = 1 ]; then echo "+ $*"; else "$@"; fi; }

[ -f "$CONF" ] || die "Keine WireGuard-Konfiguration unter $CONF gefunden. Bei Proton VPN: Konto → Downloads → WireGuard-Konfiguration erstellen und als wg0.conf dort ablegen."

# ------------------------------------------------------------- Konfiguration lesen
# Wert eines Schlüssels (erstes Vorkommen, Groß-/Kleinschreibung egal)
get() { sed -n "s/^[[:space:]]*$1[[:space:]]*=[[:space:]]*//Ip" "$CONF" | head -n1 | tr -d '\r' | sed 's/[[:space:]]*$//'; }
split() { tr ',' '\n' <<<"$1" | sed 's/^[[:space:]]*//;s/[[:space:]]*$//' | grep -v '^$' || true; }

ADDRESSES="$(get Address)"
DNS="$(get DNS)"
ENDPOINT="$(get Endpoint)"
MTU="$(get MTU)"
[ -n "$ADDRESSES" ] || die "In der Konfiguration fehlt 'Address'"
[ -n "$ENDPOINT" ] || die "In der Konfiguration fehlt 'Endpoint'"

EP_PORT="${ENDPOINT##*:}"
EP_HOST="${ENDPOINT%:*}"; EP_HOST="${EP_HOST#[}"; EP_HOST="${EP_HOST%]}"
if [[ "$EP_HOST" =~ ^[0-9]+\.[0-9]+\.[0-9]+\.[0-9]+$ ]]; then
  EP_IP="$EP_HOST"
else
  EP_IP="$(getent ahostsv4 "$EP_HOST" | awk 'NR==1{print $1}')" || true
  [ -n "${EP_IP:-}" ] || die "VPN-Server $EP_HOST konnte nicht aufgelöst werden"
fi

if [ "$DRY" = 1 ]; then
  GW="${TEST_GW:-172.17.0.1}"; DEV="${TEST_DEV:-eth0}"; SUBNET="${TEST_SUBNET:-172.17.0.0/16}"
else
  GW="$(ip -4 route show default | awk '/default/{print $3; exit}')"
  DEV="$(ip -4 route show default | awk '/default/{print $5; exit}')"
  SUBNET="$(ip -4 route show dev "$DEV" scope link | awk 'NR==1{print $1}')"
fi
[ -n "$GW" ] || die "Kein Standard-Gateway gefunden"

# Nur die Schlüssel, die `wg setconf` versteht (wie `wg-quick strip`)
STRIPPED="$(tr -d '\r' <"$CONF" | awk '
  { l = tolower($0) }
  l ~ /^[[:space:]]*\[/ { print; next }
  l ~ /^[[:space:]]*(privatekey|listenport|fwmark|publickey|presharedkey|allowedips|endpoint|persistentkeepalive)[[:space:]]*=/ { print }')"
grep -qi '^[[:space:]]*\[peer\]' <<<"$STRIPPED" || die "In der Konfiguration fehlt der Abschnitt [Peer]"

log "Server: $EP_HOST ($EP_IP:$EP_PORT) · Gateway: $GW über $DEV · Kill-Switch: $KILLSWITCH"

# iptables-Variante wählen (nft oder legacy – je nach Kernel des Hosts)
IPT=iptables; IP6T=ip6tables
if [ "$DRY" != 1 ] && ! iptables -L -n >/dev/null 2>&1 && command -v iptables-legacy >/dev/null; then
  IPT=iptables-legacy; IP6T=ip6tables-legacy
fi

# ------------------------------------------------------------- Kill-Switch zuerst
# Wird VOR dem Tunnel gesetzt, damit nie etwas am VPN vorbei ins Internet geht.
if [ "$KILLSWITCH" = "true" ]; then
  run $IPT -N CU_VPN 2>/dev/null || true
  run $IPT -F CU_VPN
  run $IPT -A CU_VPN -o lo -j ACCEPT
  run $IPT -A CU_VPN -o "$IFACE" -j ACCEPT
  run $IPT -A CU_VPN -m conntrack --ctstate ESTABLISHED,RELATED -j ACCEPT
  run $IPT -A CU_VPN -d "$EP_IP" -p udp --dport "$EP_PORT" -j ACCEPT
  [ -n "$SUBNET" ] && run $IPT -A CU_VPN -d "$SUBNET" -j ACCEPT
  for net in $(split "$LAN_NETWORK"); do run $IPT -A CU_VPN -d "$net" -j ACCEPT; done
  run $IPT -A CU_VPN -j REJECT
  if [ "$DRY" = 1 ] || ! $IPT -C OUTPUT -j CU_VPN 2>/dev/null; then run $IPT -I OUTPUT 1 -j CU_VPN; fi
  # IPv6 komplett sperren (der Tunnel wird nur für IPv4 eingerichtet)
  if command -v "$IP6T" >/dev/null && { [ "$DRY" = 1 ] || $IP6T -L >/dev/null 2>&1; }; then
    run $IP6T -P OUTPUT DROP
    run $IP6T -A OUTPUT -o lo -j ACCEPT
    # Antworten auf eingehende Verbindungen (z.B. Reverse Proxy über IPv6) erlauben
    run $IP6T -A OUTPUT -m conntrack --ctstate ESTABLISHED,RELATED -j ACCEPT
  fi
fi

# ------------------------------------------------------------- Tunnel aufbauen
[ "$DRY" = 1 ] || ip link del "$IFACE" 2>/dev/null || true
if [ "$DRY" = 1 ] || ip link add "$IFACE" type wireguard 2>/dev/null; then
  [ "$DRY" = 1 ] && echo "+ ip link add $IFACE type wireguard"
else
  die "WireGuard-Interface konnte nicht angelegt werden. Läuft der Container mit --cap-add=NET_ADMIN und ist das WireGuard-Modul geladen (modprobe wireguard)?"
fi

if [ "$DRY" = 1 ]; then
  echo "+ wg setconf $IFACE <(konfiguration ohne Address/DNS/MTU)"
  sed 's/^\(PrivateKey\|PresharedKey\)\([[:space:]]*=[[:space:]]*\).*/\1\2***/I' <<<"$STRIPPED" | sed 's/^/    /'
else
  wg setconf "$IFACE" <(echo "$STRIPPED")
fi

for a in $(split "$ADDRESSES"); do
  [[ "$a" == *:* ]] && { log "IPv6-Adresse $a wird übersprungen"; continue; }
  [[ "$a" == */* ]] || a="$a/32"
  run ip -4 address add "$a" dev "$IFACE"
done
run ip link set mtu "${MTU:-1420}" up dev "$IFACE"

# Routen: VPN-Server und lokales Netz direkt, alles andere durch den Tunnel
run ip route replace "$EP_IP/32" via "$GW" dev "$DEV"
DNS4=()
for d in $(split "$DNS"); do [[ "$d" =~ ^[0-9.]+$ ]] && DNS4+=("$d"); done
for net in $(split "$LAN_NETWORK"); do
  [ "$net" = "$SUBNET" ] && continue
  run ip route replace "$net" via "$GW" dev "$DEV"
done
for d in "${DNS4[@]}"; do run ip route replace "$d/32" dev "$IFACE"; done
run ip route replace 0.0.0.0/1 dev "$IFACE"
run ip route replace 128.0.0.0/1 dev "$IFACE"

# Antworten auf Verbindungen, die von außen über $DEV hereinkommen (Weboberfläche,
# Reverse Proxy, Tailscale, Port-Weiterleitung …), gehen immer über $DEV zurück –
# unabhängig von der Absender-Adresse. Selbst aufgebaute Verbindungen bleiben im Tunnel.
MARK=0x6a5
TABLE=6741
addrule() { # $1=Kette, Rest=Regel – nur anlegen, wenn noch nicht vorhanden
  local chain="$1"; shift
  if [ "$DRY" = 1 ] || ! $IPT -t mangle -C "$chain" "$@" 2>/dev/null; then run $IPT -t mangle -A "$chain" "$@"; fi
}
addrule PREROUTING -i "$DEV" -m conntrack --ctstate NEW -j CONNMARK --set-mark "$MARK"
addrule OUTPUT -m connmark --mark "$MARK" -j MARK --set-mark "$MARK"
[ "$DRY" = 1 ] || ip rule del fwmark "$MARK" table "$TABLE" 2>/dev/null || true
run ip rule add fwmark "$MARK" table "$TABLE" priority 100
run ip route replace default via "$GW" dev "$DEV" table "$TABLE"
# Strenge Absenderprüfung würde die Antworten sonst verwerfen
if [ "$DRY" = 1 ]; then echo "+ sysctl rp_filter=2 (falls möglich)"; else
  for f in /proc/sys/net/ipv4/conf/all/rp_filter "/proc/sys/net/ipv4/conf/$DEV/rp_filter"; do
    [ -w "$f" ] && echo 2 > "$f" 2>/dev/null || true
  done
fi

# DNS über den Tunnel
if [ "${#DNS4[@]}" -gt 0 ]; then
  if [ "$DRY" = 1 ]; then
    echo "+ /etc/resolv.conf ← nameserver ${DNS4[*]}"
  else
    mkdir -p "$STATE"
    [ -f "$STATE/resolv.conf.orig" ] || cp /etc/resolv.conf "$STATE/resolv.conf.orig" 2>/dev/null || true
    printf 'nameserver %s\n' "${DNS4[@]}" > /etc/resolv.conf
  fi
else
  log "Kein DNS in der Konfiguration – DNS-Anfragen laufen trotzdem durch den Tunnel, aber an den bisherigen Server."
fi

[ "$DRY" = 1 ] && { log "Trockenlauf beendet."; exit 0; }

# ------------------------------------------------------------- Verbindung prüfen
# Erste Pakete auslösen, damit WireGuard den Handshake startet
for d in "${DNS4[@]:-1.1.1.1}"; do (echo >"/dev/udp/$d/53") 2>/dev/null || true; done
for _ in $(seq 1 20); do
  hs="$(wg show "$IFACE" latest-handshakes | awk 'NR==1{print $2}')"
  if [ "${hs:-0}" -gt 0 ]; then log "Verbunden (Handshake erfolgreich)."; break; fi
  sleep 1
done
[ "${hs:-0}" -gt 0 ] || log "WARNUNG: Noch kein Handshake mit dem VPN-Server. Kill-Switch bleibt aktiv – ohne VPN gehen keine Daten raus."

# ------------------------------------------------------------- Status für die Weboberfläche
mkdir -p "$STATE" && chmod 755 "$STATE"
(
  while true; do
    read -r _ hs < <(wg show "$IFACE" latest-handshakes 2>/dev/null || echo "x 0")
    read -r _ rx tx < <(wg show "$IFACE" transfer 2>/dev/null || echo "x 0 0")
    up=false; ip link show "$IFACE" >/dev/null 2>&1 && up=true
    printf '{"enabled":true,"interface_up":%s,"endpoint":"%s","latest_handshake":%s,"rx":%s,"tx":%s,"killswitch":%s,"updated":%s}\n' \
      "$up" "$EP_HOST:$EP_PORT" "${hs:-0}" "${rx:-0}" "${tx:-0}" "$KILLSWITCH" "$(date +%s)" > "$STATE/status.json.tmp"
    chmod 644 "$STATE/status.json.tmp" && mv "$STATE/status.json.tmp" "$STATE/status.json"
    sleep 15
  done
) &
