# ☁️ CloudUpper

Self-hosted Web-App (Docker), mit der du

- **Dateien vom Server** (gemountetes Verzeichnis) **oder direkt vom iPhone/Browser** in **Google Drive, OneDrive, STRATO HiDrive, Dropbox, WebDAV/Nextcloud, SFTP, S3** und alle weiteren [rclone-Backends](https://rclone.org/overview/) hochlädst,
- dabei den **Zielordner in der Cloud bequem auswählst** (inkl. „Neuer Ordner“ und zuletzt verwendeten Zielen),
- **Dateien aus TorBox** (Torrents, Web-Downloads, Usenet) auswählst und **auf den Server oder direkt in die Cloud** lädst (TorBox → Cloud ohne Umweg über die Festplatte),
- alles in einer **Web-Oberfläche, die sich auf iOS wie eine App installieren lässt** (PWA, Dark Mode, Bottom-Tab-Bar, Safe-Area-Support).

Unter der Haube übernimmt [rclone](https://rclone.org) die Übertragungen – bewährt, schnell, mit Chunked Uploads, Wiederholungen und Token-Refresh.

## Installation auf Unraid

Das Image wird per GitHub Actions automatisch gebaut und als `ghcr.io/kernelguru/cloudupper:latest` veröffentlicht.

1. Im Unraid-Terminal das Template ablegen:
   ```bash
   wget -O /boot/config/plugins/dockerMan/templates-user/my-CloudUpper.xml \
     https://raw.githubusercontent.com/kernelguru/cloudupper/main/unraid/cloudupper.xml
   ```
2. **Docker → Add Container → Template: „CloudUpper“** auswählen.
3. **Passwort** setzen, den Pfad **Dateien** (`/data`) auf deine Shares legen (z. B. `/mnt/user/` oder `/mnt/user/media/`), optional TorBox-API-Key eintragen → **Apply**.
4. WebUI über das Container-Icon öffnen.

Standardwerte passen zu Unraid: `PUID=99`, `PGID=100` (nobody:users), `UMASK=000`, Appdata unter `/mnt/user/appdata/cloudupper`. Der Container ändert keine Besitzrechte deiner Shares – nur neue Dateien (z. B. TorBox-Downloads) gehören `nobody:users`.

> Ist das GHCR-Paket privat, lädt Unraid es nicht. Einmalig auf GitHub unter **Packages → cloudupper → Package settings → Change visibility → Public** stellen.

## Docker Compose (andere Systeme)

```bash
cp .env.example .env          # APP_PASSWORD setzen!
# in docker-compose.yml den Pfad zu deinen Dateien eintragen (/pfad/zu/deinen/dateien)
docker compose up -d          # oder mit `build: .` lokal bauen
```

Dann `http://<server-ip>:8080` öffnen.

## Image bauen (GitHub Actions)

`.github/workflows/docker.yml` läuft bei jedem Push auf `main`, bei Tags `v*`, bei Pull Requests (nur Test, kein Push) und manuell über **Actions → Docker-Image bauen → Run workflow**:

1. Python-Syntaxprüfung
2. Testbuild + Smoke-Test (Container starten, Login-Schutz, Weboberfläche, rclone prüfen)
3. Build für `linux/amd64` und `linux/arm64`, Push nach GHCR

Tags: `latest` (main), `1.2.3` / `1.2` (bei Git-Tag `v1.2.3`), Branch-Name, `sha-abc1234`. Eine neue Version veröffentlichst du mit `git tag v1.0.1 && git push --tags`. Ein Secret musst du nicht anlegen – es wird das eingebaute `GITHUB_TOKEN` verwendet.

## Dateien auf dem Server werden nie automatisch gelöscht

- Standard ist **kopieren** – die Originale bleiben auf dem Server.
- Die Option **„Nach Upload auf dem Server löschen“** ist immer aus, muss pro Upload aktiv angehakt und bestätigt werden und wird danach wieder zurückgesetzt. Gelöscht wird erst, wenn der Upload erfolgreich war.
- Zusätzlich gibt es im Server-Browser einen **Löschen-Button** für ausgewählte Dateien/Ordner – mit Bestätigungsdialog.
- Nur der interne Zwischenspeicher für Uploads vom iPhone (`/config/staging`) wird automatisch aufgeräumt.

| Volume    | Inhalt |
|-----------|--------|
| `/config` | `rclone.conf` (Cloud-Zugänge), `settings.json`, Auftragsliste, Zwischenspeicher für Geräte-Uploads |
| `/data`   | Deine Dateien, die du hochladen willst. TorBox-Downloads landen standardmäßig in `/data/downloads` |

> **Wichtig:** `/config/rclone.conf` enthält die Zugangstoken deiner Clouds – Ordner schützen und sichern.

## Als App auf dem iPhone installieren

1. Seite in **Safari** öffnen (für die Installation idealerweise per HTTPS, siehe unten).
2. Teilen-Symbol → **„Zum Home-Bildschirm“**.
3. CloudUpper startet jetzt im Vollbild ohne Browserleiste, mit eigenem Icon.

Bei Uploads vom iPhone werden Dateien in 16-MB-Abschnitten übertragen; bricht die Verbindung ab, wird automatisch an der richtigen Stelle fortgesetzt. Lass die App während der Übertragung im Vordergrund (iOS pausiert Web-Apps im Hintergrund). Danach übernimmt der Server den Upload in die Cloud – dafür kann das Handy dann gesperrt werden.

## Cloud verbinden

Unter **Clouds → Cloud verbinden** gibt es zwei Wege für Google Drive, OneDrive, HiDrive und Dropbox:

### A) Per Token (ohne eigene OAuth-App, am einfachsten)
1. Auf einem Rechner mit Browser [rclone installieren](https://rclone.org/downloads/).
2. `rclone authorize "drive"` (bzw. `"onedrive"`, `"hidrive"`, `"dropbox"`) ausführen und im Browser anmelden.
3. Die ausgegebene JSON-Zeile `{"access_token":…}` in CloudUpper einfügen – fertig.

### B) „Mit … anmelden“ (eigene OAuth-App, komfortabel auch vom iPhone)
1. `BASE_URL` in `.env` auf die öffentliche Adresse setzen, z. B. `https://cloud.meinedomain.de`.
2. Beim Anbieter eine OAuth-App anlegen und als Weiterleitungs-URI `BASE_URL/api/oauth/callback` eintragen (wird in den Einstellungen angezeigt):
   - **Google:** [Cloud Console](https://console.cloud.google.com/apis/credentials) → Drive API aktivieren → OAuth-Client „Webanwendung“. Google erlaubt nur `https://…`-Domains oder `http://localhost`.
   - **OneDrive:** [Azure App-Registrierung](https://portal.azure.com/#view/Microsoft_AAD_RegisteredApps/ApplicationsListBlade) → „Persönliche Microsoft-Konten und Organisationen“ → Plattform „Web“ → Client-Secret erzeugen.
   - **HiDrive:** [developer.hidrive.com](https://developer.hidrive.com/) → App/Client anfordern.
   - **Dropbox:** [App Console](https://www.dropbox.com/developers/apps) → Scoped Access, Berechtigungen `files.content.write/read`.
3. Client-ID/-Secret in **Clouds → Einstellungen → Eigene OAuth-Apps** eintragen (oder per Umgebungsvariable).

WebDAV/Nextcloud, SFTP/NAS, S3 und **jeder andere rclone-Typ** (pCloud, MEGA, Box, FTP, SMB, …) lassen sich per Formular verbinden.

## TorBox

API-Key unter [torbox.app/settings](https://torbox.app/settings) kopieren und in der App (oder als `TORBOX_API_KEY`) hinterlegen. Im TorBox-Tab kannst du

- Torrents / Web-Downloads / Usenet-Einträge durchsuchen,
- einzelne Dateien oder ganze Einträge auswählen,
- neue Magnet-Links bzw. Download-Links direkt hinzufügen,
- als Ziel **Server** oder **eine beliebige Cloud inkl. Ordner** wählen.

Download-Links werden erst beim Start eines Auftrags angefordert, damit sie nicht ablaufen.

## Konfiguration (`.env`)

| Variable | Bedeutung |
|----------|-----------|
| `APP_PASSWORD` | Passwort für die Oberfläche (ohne = ungeschützt!) |
| `BASE_URL` | Öffentliche URL, nötig für OAuth-Anmeldung hinter Reverse Proxy |
| `TORBOX_API_KEY` | TorBox-API-Key |
| `MAX_PARALLEL` | gleichzeitige Übertragungen (Standard 2) |
| `RCLONE_FLAGS` | zusätzliche rclone-Optionen, z. B. `--bwlimit 20M --drive-chunk-size 64M` |
| `NOTIFY_URL` | Push bei fertigen/fehlgeschlagenen Aufträgen, z. B. `https://ntfy.sh/dein-topic` (ntfy-App fürs iPhone) |
| `GOOGLE_/ONEDRIVE_/HIDRIVE_/DROPBOX_CLIENT_ID/SECRET` | eigene OAuth-Apps |
| `PUID` / `PGID` / `UMASK` | Benutzer/Gruppe/Rechte für neue Dateien (Standard 99/100/000 wie bei Unraid) |
| `SESSION_DAYS` | Gültigkeit der Anmeldung (Standard 30) |

## HTTPS / Zugriff von unterwegs

Für Zugriff von außen und die iOS-Installation empfiehlt sich ein Reverse Proxy mit HTTPS (Caddy, Nginx Proxy Manager, Traefik) oder **Tailscale** (sicherster Weg – kein offener Port). Beispiel Caddy:

```
cloud.meinedomain.de {
    reverse_proxy cloudupper:8080
}
```

Bei Nginx `client_max_body_size 64m;` setzen (Uploads kommen in 16-MB-Stücken). Durch die Abschnitte funktionieren Uploads auch hinter Cloudflare (100-MB-Limit).

## Funktionen im Überblick

- Auftragswarteschlange mit Fortschritt, Geschwindigkeit, Restzeit, Abbrechen, Wiederholen
- Aufträge laufen nach einem Container-Neustart automatisch weiter
- Löschen auf dem Server nur auf Wunsch (siehe oben)
- Speicherplatzanzeige je Cloud
- Ordner-Auswahl mit Breadcrumbs, „Neuer Ordner“, zuletzt verwendete Ziele
- Light/Dark Mode, Offline-App-Shell, iOS-Home-Screen-Icon
- API-Dokumentation unter `/api/docs`

## Lokale Entwicklung

```bash
pip install -r requirements.txt     # rclone muss im PATH sein
CONFIG_DIR=./config DATA_DIR=./data APP_PASSWORD=test uvicorn app.main:app --reload --port 8080
```

## Ideen für später

- **Native iOS-App** per Capacitor-Wrapper (gleiche Oberfläche) inkl. **Share-Extension**: „Teilen → CloudUpper“ direkt aus Fotos/Dateien und echte Hintergrund-Uploads
- **Automatische Regeln**: neue TorBox-Downloads automatisch in Cloud X / Ordner Y; Watch-Folder auf dem Server
- **Geplante Syncs/Backups** (z. B. nachts `/data/fotos` → Google Drive) mit Zeitplan
- **Cloud-zu-Cloud-Transfers** (z. B. OneDrive → HiDrive) – rclone kann das bereits, es fehlt nur die UI
- Verschlüsselte Ziele mit rclone **crypt** (Ende-zu-Ende verschlüsselt in der Cloud)
- Mehrbenutzerbetrieb, Passkeys/2FA, Telegram-Bot zum Hinzufügen von Magnet-Links
