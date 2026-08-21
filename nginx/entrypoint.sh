#!/bin/sh
set -e

DOMAIN="${SSL_DOMAIN:-erp.temesgenkefyalew.com}"
EXTRA_DOMAINS="${SSL_EXTRA_DOMAINS:-}"
TEMPLATES_DIR=/etc/nginx/templates
CONF=/etc/nginx/conf.d/default.conf
CERT="/etc/letsencrypt/live/${DOMAIN}/fullchain.pem"
CERT_MTIME_FILE=/tmp/nginx-cert-mtime

server_names() {
    names="$DOMAIN"
    old_ifs=$IFS
    IFS=,
    for extra in $EXTRA_DOMAINS; do
        extra=$(echo "$extra" | tr -d ' ')
        if [ -n "$extra" ] && [ "$extra" != "$DOMAIN" ]; then
            names="$names $extra"
        fi
    done
    IFS=$old_ifs
    echo "$names"
}

SERVER_NAMES="$(server_names)"

render_config() {
    if [ -f "$CERT" ]; then
        echo "Nginx: using HTTPS for ${SERVER_NAMES}"
        sed -e "s/__SSL_SERVER_NAMES__/${SERVER_NAMES}/g" \
            -e "s/__SSL_DOMAIN__/${DOMAIN}/g" \
            "${TEMPLATES_DIR}/odoo-ssl.conf" > "$CONF"
    else
        echo "Nginx: no certificate yet — serving HTTP for ${SERVER_NAMES}"
        sed -e "s/__SSL_SERVER_NAMES__/${SERVER_NAMES}/g" \
            -e "s/__SSL_DOMAIN__/${DOMAIN}/g" \
            "${TEMPLATES_DIR}/odoo-http.conf" > "$CONF"
    fi
}

cert_mtime() {
    if [ -f "$CERT" ]; then
        date -r "$CERT" +%s
    else
        echo 0
    fi
}

render_config
echo "$(cert_mtime)" > "$CERT_MTIME_FILE"

(
    while true; do
        sleep 15
        CURRENT=$(cert_mtime)
        PREVIOUS=$(cat "$CERT_MTIME_FILE" 2>/dev/null || echo 0)
        if [ "$CURRENT" != "$PREVIOUS" ]; then
            echo "$CURRENT" > "$CERT_MTIME_FILE"
            render_config
            nginx -s reload 2>/dev/null && echo "Nginx: reloaded after certificate change" || true
        fi
    done
) &

exec nginx -g 'daemon off;'
