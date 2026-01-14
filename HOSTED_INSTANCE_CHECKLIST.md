# Single-Tenant Hosted Instance Checklist

Manual setup checklist for spinning up a dedicated instance for one customer.

---

## Pre-Setup

- [ ] Customer name: _______________
- [ ] Customer email: _______________
- [ ] Instance subdomain: _______________.actionledger.io
- [ ] Agreed to Early Access Disclaimer: Yes / No

---

## Infrastructure (per instance)

**Server:**
- [ ] Provision VPS (minimum: 1 vCPU, 1GB RAM, 20GB disk)
- [ ] Ubuntu 22.04 or 24.04
- [ ] Docker + Docker Compose installed
- [ ] SSH access configured

**Domain:**
- [ ] Create DNS A record: `[subdomain].actionledger.io` → server IP
- [ ] SSL certificate (Let's Encrypt or similar)

---

## Deployment

**1. Clone repo:**
```bash
git clone [your-repo] /opt/ai-action-ledger
cd /opt/ai-action-ledger
```

**2. Create `.env` file:**
```bash
POSTGRES_USER=ledger
POSTGRES_PASSWORD=[generate-strong-password]
POSTGRES_DB=ledger
API_KEY=[generate-unique-api-key]
ARCHIVE_PATH=/archive
CORS_ALLOW_ORIGINS=https://[subdomain].actionledger.io
```

- [ ] Strong password generated for Postgres
- [ ] Unique API key generated for customer

**3. Create archive directory:**
```bash
mkdir -p archive
```

**4. Start services:**
```bash
docker compose up -d --build
```

**5. Verify health:**
```bash
curl http://localhost:8000/health
```

- [ ] Returns `{"status":"healthy","database":"healthy","archive":"healthy"}`

---

## SSL / Reverse Proxy

**Option A: Nginx with Let's Encrypt**

- [ ] Install Nginx
- [ ] Configure reverse proxy to localhost:8000 (API) and localhost:3000 (dashboard)
- [ ] Install certbot and obtain certificate
- [ ] Verify HTTPS works

**Option B: Cloudflare Tunnel**

- [ ] Configure tunnel to point to localhost:8000
- [ ] Enable Cloudflare SSL

---

## Post-Deployment Verification

- [ ] `https://[subdomain].actionledger.io/health` returns healthy
- [ ] Can create event via API with customer's API key
- [ ] Can verify chain via API
- [ ] Dashboard loads at port 3000 (or proxied)
- [ ] Archive files being created in `/opt/ai-action-ledger/archive/`

---

## Customer Handoff

**Send to customer:**
- [ ] API URL: `https://[subdomain].actionledger.io`
- [ ] API Key: `[their-unique-key]`
- [ ] Dashboard URL: `https://[subdomain].actionledger.io:3000` (or proxied)
- [ ] ONBOARDING.md
- [ ] EARLY_ACCESS_DISCLAIMER.md
- [ ] SDK files (or link to repo)

**Confirm with customer:**
- [ ] They can hit `/health`
- [ ] They can log a test event
- [ ] They can verify the chain
- [ ] They have your support email

---

## Ongoing Maintenance

**Daily (automated):**
- [ ] Database backups configured (pg_dump or managed backup)
- [ ] Archive directory backed up (rsync to S3 or similar)

**Weekly (manual):**
- [ ] Check disk usage
- [ ] Check container health (`docker compose ps`)
- [ ] Review any error logs

**As needed:**
- [ ] Apply security updates
- [ ] Update application (pull + rebuild)

---

## Shutdown / Offboarding

If customer leaves:
- [ ] Export their data (JSON export via API)
- [ ] Provide data to customer if requested
- [ ] Delete instance after retention period
- [ ] Remove DNS record

---

## Notes

Instance ID: _______________  
Provisioned date: _______________  
Notes: _______________
