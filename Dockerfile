# syntax=docker/dockerfile:1
ARG RCLONE_VERSION=1.68.2
FROM rclone/rclone:${RCLONE_VERSION} AS rclone

FROM python:3.12-slim
LABEL org.opencontainers.image.title="CloudUpper" \
      org.opencontainers.image.description="Dateien in Google Drive, OneDrive, HiDrive & Co. hochladen und von TorBox laden" \
      org.opencontainers.image.source="https://github.com/kernelguru/cloudupper"
ENV PYTHONDONTWRITEBYTECODE=1 \
    PYTHONUNBUFFERED=1 \
    CONFIG_DIR=/config \
    DATA_DIR=/data \
    PORT=8080 \
    HOME=/tmp \
    PUID=99 \
    PGID=100 \
    UMASK=000

RUN apt-get update \
 && apt-get install -y --no-install-recommends ca-certificates tini \
      wireguard-tools iproute2 iptables \
 && rm -rf /var/lib/apt/lists/*
COPY --from=rclone /usr/local/bin/rclone /usr/local/bin/rclone

WORKDIR /srv
COPY requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt
COPY app ./app

COPY entrypoint.sh /entrypoint.sh
COPY vpn.sh /usr/local/bin/cloudupper-vpn
RUN chmod +x /entrypoint.sh /usr/local/bin/cloudupper-vpn

VOLUME ["/config", "/data"]
EXPOSE 8080
HEALTHCHECK --interval=30s --timeout=5s CMD python -c "import urllib.request,os;urllib.request.urlopen(f'http://127.0.0.1:{os.environ.get(\"PORT\",\"8080\")}/api/session')" || exit 1
ENTRYPOINT ["/usr/bin/tini", "--", "/entrypoint.sh"]
CMD ["sh", "-c", "exec uvicorn app.main:app --host 0.0.0.0 --port ${PORT} --proxy-headers --forwarded-allow-ips='*'"]
