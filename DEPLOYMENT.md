# Deploy Green Ethio Trading (Odoo 18) on a New Server

This stack runs **Odoo 18**, **PostgreSQL 15**, **Nginx**, and **Certbot** with Docker Compose.

**Production URLs (same Odoo, one SSL certificate):**
- `https://temesgenkefyalew.com`
- `https://www.temesgenkefyalew.com`
- `https://greenethiotrading.com`
- `https://www.greenethiotrading.com`

SSL is issued automatically once **every** hostname above has a DNS A (or CNAME) record pointing **only** at the VPS IP `196.188.249.207`.

## Prerequisites

- Ubuntu 22.04 or 24.04 (or similar Debian-based distro)
- Docker 24+ and Docker Compose v2+
- 4 GB RAM minimum (8 GB+ recommended)
- 2 vCPUs minimum (4+ recommended)
- Ports **80** and **443** open to the internet
- Ability to point `temesgenkefyalew.com` and `greenethiotrading.com` at the VPS

---

## Step 1 — Point both domains at the VPS (DNS)

VPS IP: **`196.188.249.207`**

**Edit** existing A records. Do **not** add a second A for the same name (Let’s Encrypt fails if two IPs exist). Do **not** use **+Add a New SubDomain**.

Leave **MX**, `webmail`, `cpanel`, and `cwp` on Zergaw (`196.188.249.61`) so email keeps working.

### A) `temesgenkefyalew.com` in Zergaw Cloud

**DNS Functions → Edit DNS Zone** → `temesgenkefyalew.com`

| Record | Action |
|--------|--------|
| `temesgenkefyalew.com.` **A** `196.188.249.61` | **Edit** to `196.188.249.207` (do not add another A) |
| `www` **CNAME** `temesgenkefyalew.com` | Keep (www will follow the new A) |
| `erp...` A record | Optional: delete; not used anymore |
| MX / webmail / cpanel / cwp | Do not change |

### B) `greenethiotrading.com` in that domain’s DNS panel

Open DNS for **`greenethiotrading.com`** (Zergaw if the domain is there, otherwise the registrar).

| Type | Name | Value |
|------|------|--------|
| A | `@` or `greenethiotrading.com` | `196.188.249.207` |
| A or CNAME | `www` | `196.188.249.207` or `greenethiotrading.com` |

Only **one** A record per name. If `@` already exists, edit it; do not create a duplicate.

### Check (must be a single IP each)

```bash
nslookup temesgenkefyalew.com 8.8.8.8
nslookup www.temesgenkefyalew.com 8.8.8.8
nslookup greenethiotrading.com 8.8.8.8
nslookup www.greenethiotrading.com 8.8.8.8
```

Every name must return **only** `196.188.249.207`. If you still see `196.188.249.61` as well, SSL will fail.

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
SSL_DOMAIN=temesgenkefyalew.com
SSL_EXTRA_DOMAINS=www.temesgenkefyalew.com,greenethiotrading.com,www.greenethiotrading.com
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

- `http://temesgenkefyalew.com`
- `http://greenethiotrading.com`

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
ls -l letsencrypt/live/temesgenkefyalew.com/
```

Open:

- **https://temesgenkefyalew.com**
- **https://greenethiotrading.com**

HTTP should redirect to HTTPS after the cert exists.

If certbot retries with “certificate request failed”, DNS is not pointing here yet, or ports 80/443 are blocked. Fix DNS/firewall and wait — it retries every 5 minutes.

You can also start/restart SSL with:

```bash
chmod +x setup-ssl.sh renew-ssl.sh
./setup-ssl.sh temesgenkefyalew.com you@your-real-email.com
```

---

## Step 9 — Create the Odoo database (first login)

1. Open `https://temesgenkefyalew.com` or `https://greenethiotrading.com`
2. Create the database (master password = `admin_passwd` from `etc/odoo.conf`)
3. In Odoo: **Settings → Technical → System Parameters** (enable Developer Mode first)
4. Set:

| Key | Value |
|-----|--------|
| `web.base.url` | `https://greenethiotrading.com` |
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
| Certbot keeps retrying | Every hostname must return **only** `196.188.249.207` (no `61`). Ports 80 and 443 must be open. |
| 502 Bad Gateway | Odoo still starting: `docker compose ps` and `docker compose logs odoo` |
| Odoo will not start | Password mismatch between `.env` `POSTGRES_PASSWORD` and `etc/odoo.conf` `db_password` |
| Site stays on HTTP | `docker compose logs certbot` and `ls letsencrypt/live/` |
| Wrong host in emails/links | Set `web.base.url` as in Step 9 |
| Custom apps missing | Confirm folder is mounted and restart Odoo, then **Update Apps List** |

---

## Production checklist

- [ ] `temesgenkefyalew.com` A → `196.188.249.207` only
- [ ] `greenethiotrading.com` A → `196.188.249.207` only
- [ ] `www` for both domains also resolves to `196.188.249.207`
- [ ] Strong `POSTGRES_PASSWORD` in `.env` matching `db_password` in `etc/odoo.conf`
- [ ] Changed `admin_passwd` in `etc/odoo.conf`
- [ ] Real `CERTBOT_EMAIL` in `.env`
- [ ] Firewall: 22, 80, 443 only (block 5432/8069 from the public internet)
- [ ] HTTPS loads and HTTP redirects
- [ ] `web.base.url` set to `https://greenethiotrading.com`
- [ ] Database backup scheduled

