#!/bin/bash
# WireGuard-VPN (z.B. Proton VPN) für den gesamten Container-Verkehr – mit Kill-Switch.
#
#   cloudupper-vpn up     Tunnel + Kill-Switch einrichten
#   cloudupper-vpn down   alles wieder entfernen (Verkehr läuft direkt)
#   cloudupper-vpn stats  Handshake/Datenmenge als JSON ausgeben
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
APPLIED="$STATE/applied.env"
KILLSWITCH="${VPN_KILLSWITCH:-true}"
LAN_NETWORK="${LAN_NETWORK:-192.168.0.0/16,172.16.0.0/12,10.0.0.0/8,100.64.0.0/10}"
DRY="${DRY_RUN:-0}"
MARK=0x6a5
TABLE=6741

log() { echo "[vpn] $*"; }
die() { echo "[vpn] FEHLER: $*" >&2; exit 1; }
run() { if [ "$DRY" = 1 ]; then echo "+ $*"; else "$@"; fi; }
quiet() { if [ "$DRY" = 1 ]; then echo "+ $*"; else "$@" 2>/dev/null || true; fi; }
split() { tr ',' '\n' <<<"$1" | sed 's/^[[:space:]]*//;s/[[:space:]]*$//' | grep -v '^$' || true; }

# iptables-Variante wählen (nft oder legacy – je nach Kernel des Hosts)
IPT=iptables; IP6T=ip6tables
if [ "$DRY" != 1 ] && ! iptables -L -n >/dev/null 2>&1 && command -v iptables-legacy >/dev/null; then
  IPT=iptables-legacy; IP6T=ip6tables-legacy
fi
have_ip6t() { command -v "$IP6T" >/dev/null && { [ "$DRY" = 1 ] || $IP6T -L -n >/dev/null 2>&1; }; }

net_defaults() {
  if [ "$DRY" = 1 ]; then
    GW="${TEST_GW:-172.17.0.1}"; DEV="${TEST_DEV:-eth0}"; SUBNET="${TEST_SUBNET:-172.17.0.0/16}"
  else
    GW="$(ip -4 route show default | awk '/default/{print $3; exit}')"
    DEV="$(ip -4 route show default | awk '/default/{print $5; exit}')"
    SUBNET="$(ip -4 route show dev "$DEV" scope link 2>/dev/null | awk 'NR==1{print $1}')"
  fi
}

# =================================================================== down
cmd_down() {
  EP_IP=""; GW=""; DEV=""; NETS=""
  # shellcheck disable=SC1090
  [ -f "$APPLIED" ] && . "$APPLIED"
  [ -n "$DEV" ] || net_defaults
  quiet ip link del "$IFACE"                         # entfernt auch alle Routen über wg0
  [ -n "$EP_IP" ] && quiet ip route del "$EP_IP/32" via "$GW" dev "$DEV"
  for net in $(split "${NETS:-}"); do quiet ip route del "$net" via "$GW" dev "$DEV"; done
  quiet $IPT -D OUTPUT -j CU_VPN; quiet $IPT -F CU_VPN; quiet $IPT -X CU_VPN
  if have_ip6t; then quiet $IP6T -D OUTPUT -j CU_VPN6; quiet $IP6T -F CU_VPN6; quiet $IP6T -X CU_VPN6; fi
  quiet $IPT -t mangle -D PREROUTING -i "$DEV" -m conntrack --ctstate NEW -j CONNMARK --set-mark "$MARK"
  quiet $IPT -t mangle -D OUTPUT -m connmark --mark "$MARK" -j MARK --set-mark "$MARK"
  quiet ip rule del fwmark "$MARK" table "$TABLE"
  quiet ip route flush table "$TABLE"
  if [ "$DRY" = 1 ]; then echo "+ /etc/resolv.conf wiederherstellen"
  elif [ -f "$STATE/resolv.conf.orig" ]; then cat "$STATE/resolv.conf.orig" > /etc/resolv.conf; rm -f "$STATE/resolv.conf.orig"; fi
  [ "$DRY" = 1 ] || rm -f "$APPLIED"
  log "VPN aus – der Verkehr läuft wieder direkt."
}

# =================================================================== up
cmd_up() {
  [ -f "$CONF" ] || die "Keine WireGuard-Konfiguration unter $CONF gefunden. Bei Proton VPN: Konto → Downloads → WireGuard-Konfiguration erstellen und als wg0.conf in appdata/cloudupper/wireguard/ ablegen."

  # Wert eines Schlüssels (erstes Vorkommen, Groß-/Kleinschreibung egal)
  get() { sed -n "s/^[[:space:]]*$1[[:space:]]*=[[:space:]]*//Ip" "$CONF" | head -n1 | tr -d '\r' | sed 's/[[:space:]]*$//'; }
  local ADDRESSES DNS ENDPOINT MTU EP_PORT EP_HOST
  ADDRESSES="$(get Address)"; DNS="$(get DNS)"; ENDPOINT="$(get Endpoint)"; MTU="$(get MTU)"
  [ -n "$ADDRESSES" ] || die "In der Konfiguration fehlt 'Address'"
  [ -n "$ENDPOINT" ] || die "In der Konfiguration fehlt 'Endpoint'"

  EP_PORT="${ENDPOINT##*:}"
  EP_HOST="${ENDPOINT%:*}"; EP_HOST="${EP_HOST#[}"; EP_HOST="${EP_HOST%]}"
  if [[ "$EP_HOST" =~ ^[0-9]+\.[0-9]+\.[0-9]+\.[0-9]+$ ]]; then EP_IP="$EP_HOST"
  else
    EP_IP="$(getent ahostsv4 "$EP_HOST" | awk 'NR==1{print $1}')" || true
    [ -n "${EP_IP:-}" ] || die "VPN-Server $EP_HOST konnte nicht aufgelöst werden"
  fi

  # Nur die Schlüssel, die `wg setconf` versteht (wie `wg-quick strip`)
  local STRIPPED
  STRIPPED="$(tr -d '\r' <"$CONF" | awk '
    { l = tolower($0) }
    l ~ /^[[:space:]]*\[/ { print; next }
    l ~ /^[[:space:]]*(privatekey|listenport|fwmark|publickey|presharedkey|allowedips|endpoint|persistentkeepalive)[[:space:]]*=/ { print }')"
  grep -qi '^[[:space:]]*\[peer\]' <<<"$STRIPPED" || die "In der Konfiguration fehlt der Abschnitt [Peer]"

  # Sauberer Ausgangszustand (falls von einem früheren Lauf noch etwas übrig ist)
  [ "$DRY" = 1 ] || cmd_down >/dev/null
  net_defaults
  [ -n "$GW" ] || die "Kein Standard-Gateway gefunden"
  local NETS=""
  for net in $(split "$LAN_NETWORK"); do [ "$net" = "$SUBNET" ] || NETS="$NETS${NETS:+,}$net"; done

  log "Server: $EP_HOST ($EP_IP:$EP_PORT) · Gateway: $GW über $DEV · Kill-Switch: $KILLSWITCH"
  if [ "$DRY" != 1 ]; then
    mkdir -p "$STATE" && chmod 755 "$STATE"
    printf 'EP_IP=%q\nGW=%q\nDEV=%q\nNETS=%q\nENDPOINT_LABEL=%q\n' "$EP_IP" "$GW" "$DEV" "$NETS" "$EP_HOST:$EP_PORT" > "$APPLIED"
  fi

  # ----------------------------------------------------------- Kill-Switch zuerst
  # Wird VOR dem Tunnel gesetzt, damit nie etwas am VPN vorbei ins Internet geht.
  if [ "$KILLSWITCH" = "true" ]; then
    run $IPT -N CU_VPN
    run $IPT -A CU_VPN -o lo -j ACCEPT
    run $IPT -A CU_VPN -o "$IFACE" -j ACCEPT
    run $IPT -A CU_VPN -m conntrack --ctstate ESTABLISHED,RELATED -j ACCEPT
    run $IPT -A CU_VPN -d "$EP_IP" -p udp --dport "$EP_PORT" -j ACCEPT
    [ -n "$SUBNET" ] && run $IPT -A CU_VPN -d "$SUBNET" -j ACCEPT
    for net in $(split "$NETS"); do run $IPT -A CU_VPN -d "$net" -j ACCEPT; done
    run $IPT -A CU_VPN -j REJECT
    run $IPT -I OUTPUT 1 -j CU_VPN
    # IPv6 sperren (der Tunnel wird nur für IPv4 eingerichtet); Antworten auf
    # eingehende Verbindungen (z.B. Reverse Proxy über IPv6) bleiben erlaubt.
    if have_ip6t; then
      run $IP6T -N CU_VPN6
      run $IP6T -A CU_VPN6 -o lo -j ACCEPT
      run $IP6T -A CU_VPN6 -m conntrack --ctstate ESTABLISHED,RELATED -j ACCEPT
      run $IP6T -A CU_VPN6 -j REJECT
      run $IP6T -I OUTPUT 1 -j CU_VPN6
    fi
  fi

  # ----------------------------------------------------------- Tunnel
  if [ "$DRY" = 1 ]; then
    echo "+ ip link add $IFACE type wireguard"
    echo "+ wg setconf $IFACE <(konfiguration ohne Address/DNS/MTU)"
    sed 's/^\(PrivateKey\|PresharedKey\)\([[:space:]]*=[[:space:]]*\).*/\1\2***/I' <<<"$STRIPPED" | sed 's/^/    /'
  else
    ip link add "$IFACE" type wireguard 2>/dev/null || die "WireGuard-Interface konnte nicht angelegt werden. Läuft der Container mit --cap-add=NET_ADMIN und ist das WireGuard-Modul geladen (modprobe wireguard)?"
    wg setconf "$IFACE" <(echo "$STRIPPED") || die "WireGuard-Konfiguration ungültig (Schlüssel prüfen)"
  fi
  for a in $(split "$ADDRESSES"); do
    [[ "$a" == *:* ]] && { log "IPv6-Adresse $a wird übersprungen"; continue; }
    [[ "$a" == */* ]] || a="$a/32"
    run ip -4 address add "$a" dev "$IFACE"
  done
  run ip link set mtu "${MTU:-1420}" up dev "$IFACE"

  # Routen: VPN-Server und lokales Netz direkt, alles andere durch den Tunnel
  run ip route replace "$EP_IP/32" via "$GW" dev "$DEV"
  for net in $(split "$NETS"); do run ip route replace "$net" via "$GW" dev "$DEV"; done
  local DNS4=()
  for d in $(split "$DNS"); do [[ "$d" =~ ^[0-9.]+$ ]] && DNS4+=("$d"); done
  for d in "${DNS4[@]}"; do run ip route replace "$d/32" dev "$IFACE"; done
  run ip route replace 0.0.0.0/1 dev "$IFACE"
  run ip route replace 128.0.0.0/1 dev "$IFACE"

  # Antworten auf Verbindungen, die von außen über $DEV hereinkommen (Weboberfläche,
  # Reverse Proxy, Tailscale, Port-Weiterleitung …), gehen immer über $DEV zurück –
  # unabhängig von der Absender-Adresse. Selbst aufgebaute Verbindungen bleiben im Tunnel.
  run $IPT -t mangle -A PREROUTING -i "$DEV" -m conntrack --ctstate NEW -j CONNMARK --set-mark "$MARK"
  run $IPT -t mangle -A OUTPUT -m connmark --mark "$MARK" -j MARK --set-mark "$MARK"
  run ip rule add fwmark "$MARK" table "$TABLE" priority 100
  run ip route replace default via "$GW" dev "$DEV" table "$TABLE"
  if [ "$DRY" = 1 ]; then echo "+ rp_filter=2 (falls möglich)"; else
    for f in /proc/sys/net/ipv4/conf/all/rp_filter "/proc/sys/net/ipv4/conf/$DEV/rp_filter"; do
      [ -w "$f" ] && echo 2 > "$f" 2>/dev/null || true
    done
  fi

  # DNS über den Tunnel
  if [ "${#DNS4[@]}" -gt 0 ]; then
    if [ "$DRY" = 1 ]; then echo "+ /etc/resolv.conf ← nameserver ${DNS4[*]}"
    else
      [ -f "$STATE/resolv.conf.orig" ] || cp /etc/resolv.conf "$STATE/resolv.conf.orig" 2>/dev/null || true
      printf 'nameserver %s\n' "${DNS4[@]}" > /etc/resolv.conf
    fi
  else
    log "Kein DNS in der Konfiguration – DNS-Anfragen laufen trotzdem durch den Tunnel, aber an den bisherigen Server."
  fi

  [ "$DRY" = 1 ] && { log "Trockenlauf beendet."; return 0; }

  # Erste Pakete auslösen, damit WireGuard den Handshake startet
  local hs=0
  for d in "${DNS4[@]:-1.1.1.1}"; do (echo >"/dev/udp/$d/53") 2>/dev/null || true; done
  for _ in $(seq 1 20); do
    hs="$(wg show "$IFACE" latest-handshakes | awk 'NR==1{print $2}')"
    [ "${hs:-0}" -gt 0 ] && { log "Verbunden (Handshake erfolgreich)."; return 0; }
    sleep 1
  done
  die "Kein Handshake mit dem VPN-Server ($EP_HOST). Kill-Switch bleibt aktiv – ohne VPN gehen keine Daten raus. Konfiguration prüfen oder VPN in der App ausschalten."
}

# =================================================================== stats
cmd_stats() {
  local hs=0 rx=0 tx=0 up=false ep=""
  if ip link show "$IFACE" >/dev/null 2>&1; then
    up=true
    read -r _ hs < <(wg show "$IFACE" latest-handshakes 2>/dev/null || echo "x 0")
    read -r _ rx tx < <(wg show "$IFACE" transfer 2>/dev/null || echo "x 0 0")
  fi
  # shellcheck disable=SC1090
  [ -f "$APPLIED" ] && ep="$(. "$APPLIED"; echo "${ENDPOINT_LABEL:-}")"
  local blocking=false
  $IPT -C OUTPUT -j CU_VPN 2>/dev/null && blocking=true
  printf '{"interface_up":%s,"endpoint":"%s","latest_handshake":%s,"rx":%s,"tx":%s,"killswitch_active":%s}\n' \
    "$up" "$ep" "${hs:-0}" "${rx:-0}" "${tx:-0}" "$blocking"
}

case "${1:-up}" in
  up) cmd_up ;;
  down) cmd_down ;;
  stats) cmd_stats ;;
  *) die "Unbekannter Befehl: $1 (up|down|stats)" ;;
esac
