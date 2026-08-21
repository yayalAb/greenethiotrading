# Deploy Green Ethio Trading (Odoo 18) on a New Server

This stack runs **Odoo 18**, **PostgreSQL 15**, **Nginx**, and **Certbot** with Docker Compose.

**Production URL:** `https://erp.temesgenkefyalew.com`

SSL is issued automatically by the Certbot container once DNS points at this server. Nginx starts on HTTP, then reloads to HTTPS when the certificate appears.

## Prerequisites

- Ubuntu 22.04 or 24.04 (or similar Debian-based distro)
- Docker 24+ and Docker Compose v2+
- 4 GB RAM minimum (8 GB+ recommended)
- 2 vCPUs minimum (4+ recommended)
- Ports **80** and **443** open to the internet
- Ability to create a DNS A record for `erp.temesgenkefyalew.com`

---

## Step 1 — Point DNS at the VPS (Zergaw Cloud CWP)

Do **not** use **+Add a New SubDomain**. That creates a site on Zergaw hosting and often adds a second A record to the shared-hosting IP. Odoo runs on your VPS, so only one DNS **A** record should exist for `erp`.

1. Log in to Zergaw Cloud for `temesgenkefyalew.com`.
2. Open **DNS Functions → Edit DNS Zone** and select `temesgenkefyalew.com`.
3. Search for `erp`. Keep **only** this record:

| Type | Name | Value | TTL |
|------|------|-------|-----|
| A | `erp` or `erp.temesgenkefyalew.com` | **`196.188.249.207`** (VPS) | 300 |

If a second A record points `erp` to `196.188.249.61` (Zergaw hosting), **delete** it.

Leave `@`, `www`, and MX unchanged so the main site and email on Zergaw keep working.

Check:

```bash
nslookup erp.temesgenkefyalew.com
```

It must return **only** `196.188.249.207`. Two addresses means SSL and the site will fail at random.

---

## Step 2 — Install Docker on Ubuntu

```bash
sudo apt update && sudo apt upgrade -y

sudo apt install -y ca-certificates curl gnupg git
sudo install -m 0755 -d /etc/apt/keyrings
curl -fsSL https://download.docker.com/linux/ubuntu/gpg | sudo gpg --dearmor -o /etc/apt/keyrings/docker.gpg
sudo chmod a+r /etc/apt/keyrings/docker.gpg

echo "deb [arch=$(dpkg --print-architecture) signed-by=/etc/apt/keyrings/docker.gpg] https://download.docker.com/linux/ubuntu $(. /etc/os-release && echo "$VERSION_CODENAME") stable" | sudo tee /etc/apt/sources.list.d/docker.list > /dev/null

sudo apt update
sudo apt install -y docker-ce docker-ce-cli containerd.io docker-buildx-plugin docker-compose-plugin

sudo usermod -aG docker $USER
```

Log out and log back in (or reboot) so the `docker` group takes effect.

```bash
docker --version
docker compose version
```

---

## Step 3 — Copy the project onto the server

If this repo is on Git:

```bash
cd /opt
sudo git clone <YOUR_REPO_URL> greenethiotrading
sudo chown -R $USER:$USER /opt/greenethiotrading
cd /opt/greenethiotrading
```

Or copy the project folder from your current machine (SCP / rsync), then `cd` into it.

---

## Step 4 — Configure environment and database password

```bash
cp .env.example .env
nano .env
```

Set at least:

```bash
POSTGRES_USER=odoo
POSTGRES_PASSWORD=use-a-strong-unique-password
SSL_DOMAIN=erp.temesgenkefyalew.com
CERTBOT_EMAIL=you@your-real-email.com
```

`CERTBOT_EMAIL` must be a mailbox you can receive Let’s Encrypt notices at.

**Password must match Odoo config.** `etc/odoo.conf` has `db_password`. Set it to the same value as `POSTGRES_PASSWORD` in `.env`:

```ini
db_host = db
db_user = odoo
db_password = use-a-strong-unique-password
```

Also change `admin_passwd` in `etc/odoo.conf` (this is the Odoo master password used to create/manage databases). Do not keep the sample value on a public server.

---

## Step 5 — Open the firewall

```bash
sudo ufw allow OpenSSH
sudo ufw allow 80/tcp
sudo ufw allow 443/tcp
sudo ufw enable
sudo ufw status
```

Do **not** expose PostgreSQL (`5432`) or Odoo (`8069`) on the public internet in production. Those ports are published in `docker-compose.yml` for local/admin access; restrict them with UFW if the server is public:

```bash
# Optional: block public access to DB and Odoo direct ports
sudo ufw deny 5432/tcp
sudo ufw deny 8069/tcp
```

---

## Step 6 — Create SSL helper directories

```bash
mkdir -p certbot-webroot letsencrypt
```

---

## Step 7 — Start the stack

```bash
docker compose up -d
docker compose ps
```

Wait until `odoo18-web` is healthy (first start can take 1–2 minutes):

```bash
docker compose logs -f odoo
```

Until the certificate is issued, the site is available on HTTP:

`http://erp.temesgenkefyalew.com`

---

## Step 8 — Wait for the Let’s Encrypt certificate

Certbot requests the certificate automatically. Watch it:

```bash
docker compose logs -f certbot
```

You want to see:

- `Certbot: requesting/expanding certificate...`
- `Certbot: certificate ready`

Nginx then reloads HTTPS by itself (it polls for the cert every 15 seconds). Confirm:

```bash
docker compose logs nginx | grep -i ssl
ls -l letsencrypt/live/erp.temesgenkefyalew.com/
```

Open:

**https://erp.temesgenkefyalew.com**

HTTP should redirect to HTTPS after the cert exists.

If certbot retries with “certificate request failed”, DNS is not pointing here yet, or ports 80/443 are blocked. Fix DNS/firewall and wait — it retries every 5 minutes.

You can also start/restart SSL with:

```bash
chmod +x setup-ssl.sh renew-ssl.sh
./setup-ssl.sh erp.temesgenkefyalew.com you@your-real-email.com
```

---

## Step 9 — Create the Odoo database (first login)

1. Open `https://erp.temesgenkefyalew.com`
2. Create the database (master password = `admin_passwd` from `etc/odoo.conf`)
3. In Odoo: **Settings → Technical → System Parameters** (enable Developer Mode first)
4. Set:

| Key | Value |
|-----|--------|
| `web.base.url` | `https://erp.temesgenkefyalew.com` |
| `web.base.url.freeze` | `True` |

That keeps email links, reports, and portal URLs on the HTTPS domain.

---

## Step 10 — Custom addons

Custom modules are already mounted from:

- `addons`, `addons_e`, `project`, `accounting`, `fleet`, `hr`, `inv_purchase_sales`, `manufacturing`, `theme`

After adding or changing modules:

```bash
docker compose restart odoo
```

In Odoo: **Apps → Update Apps List**, then install the modules you need.

---

## Useful commands

```bash
# Logs
docker compose logs -f odoo
docker compose logs -f nginx
docker compose logs -f certbot

# Restart
docker compose restart odoo
docker compose restart nginx

# Stop (keeps data)
docker compose down

# Stop and delete all data (destructive)
docker compose down -v

# Manual SSL renewal (also runs automatically about every 12 hours)
./renew-ssl.sh

# Database backup
docker compose exec db pg_dump -U odoo postgres > backup_$(date +%Y%m%d).sql

# Restore
cat backup_YYYYMMDD.sql | docker compose exec -T db psql -U odoo postgres
```

---

## Architecture

```
Internet
   │
   ├─ :80  ACME challenge + HTTP → HTTPS redirect
   └─ :443 TLS (Let's Encrypt)
         │
      Nginx (odoo18-nginx)
         │
      Odoo 18 :8069 (odoo18-web)
         │
      PostgreSQL :5432 (odoo18-db)
```

- **Nginx** reverse-proxies Odoo and terminates SSL. Active config is generated from `nginx/templates/` using `SSL_DOMAIN`.
- **Certbot** writes certificates into `./letsencrypt`.
- **Odoo** uses `etc/odoo.conf` (`proxy_mode = True`).

---

## Troubleshooting

| Issue | What to check |
|-------|----------------|
| Certbot keeps retrying | `nslookup erp.temesgenkefyalew.com` must return only this server IP (`196.188.249.207`). Ports 80 and 443 must be open. |
| 502 Bad Gateway | Odoo still starting: `docker compose ps` and `docker compose logs odoo` |
| Odoo will not start | Password mismatch between `.env` `POSTGRES_PASSWORD` and `etc/odoo.conf` `db_password` |
| Site stays on HTTP | `docker compose logs certbot` and `ls letsencrypt/live/` |
| Wrong host in emails/links | Set `web.base.url` as in Step 9 |
| Custom apps missing | Confirm folder is mounted and restart Odoo, then **Update Apps List** |

---

## Production checklist

- [ ] DNS A record for `erp.temesgenkefyalew.com` → `196.188.249.207` only (no second IP)
- [ ] Strong `POSTGRES_PASSWORD` in `.env` matching `db_password` in `etc/odoo.conf`
- [ ] Changed `admin_passwd` in `etc/odoo.conf`
- [ ] Real `CERTBOT_EMAIL` in `.env`
- [ ] Firewall: 22, 80, 443 only (block 5432/8069 from the public internet)
- [ ] HTTPS loads and HTTP redirects
- [ ] `web.base.url` set to `https://erp.temesgenkefyalew.com`
- [ ] Database backup scheduled

