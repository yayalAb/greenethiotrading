#!/bin/sh
set -e

DOMAIN="${SSL_DOMAIN:-temesgenkefyalew.com}"
EXTRA_DOMAINS="${SSL_EXTRA_DOMAINS:-www.temesgenkefyalew.com,greenethiotrading.com,www.greenethiotrading.com}"
EMAIL="${CERTBOT_EMAIL:-admin@temesgenkefyalew.com}"
WEBROOT=/var/www/certbot
CERT="/etc/letsencrypt/live/${DOMAIN}/fullchain.pem"
RETRY_SECONDS="${CERTBOT_RETRY_SECONDS:-300}"
RENEW_INTERVAL="${CERTBOT_RENEW_INTERVAL:-43200}"

CERTBOT_D_FLAGS="-d ${DOMAIN}"
old_ifs=$IFS
IFS=,
for extra in $EXTRA_DOMAINS; do
    extra=$(echo "$extra" | tr -d ' ')
    if [ -n "$extra" ] && [ "$extra" != "$DOMAIN" ]; then
        CERTBOT_D_FLAGS="$CERTBOT_D_FLAGS -d $extra"
    fi
done
IFS=$old_ifs

echo "Certbot: domains=${CERTBOT_D_FLAGS} email=${EMAIL}"

# Nginx must be up to answer the ACME webroot challenge
sleep 15

request_certificate() {
    # Word-splitting of CERTBOT_D_FLAGS is intentional so each -d is a flag
    # shellcheck disable=SC2086
    certbot certonly --webroot \
        -w "$WEBROOT" \
        $CERTBOT_D_FLAGS \
        --email "$EMAIL" \
        --agree-tos \
        --non-interactive \
        --keep-until-expiring \
        --expand
}

echo "Certbot: requesting/expanding certificate..."
until request_certificate; do
    echo "Certbot: certificate request failed — retrying in ${RETRY_SECONDS}s"
    echo "Certbot: every hostname must have a DNS A record pointing at this server"
    sleep "$RETRY_SECONDS"
done
echo "Certbot: certificate ready"

while true; do
    sleep "$RENEW_INTERVAL"
    if certbot renew --webroot -w "$WEBROOT" --quiet; then
        echo "Certbot: renewal check complete"
    fi
done
