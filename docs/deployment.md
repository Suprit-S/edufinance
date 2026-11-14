# Deployment guide

EduFinance runs as four containers: PostgreSQL, the Flask API (gunicorn), the
React build served by nginx, and Caddy for HTTPS. The same Docker Compose files
run locally and in the cloud. Only the `.env` file and one override file change.

```
Internet ──443──▶ Caddy ──▶ nginx (React build) ──/api──▶ gunicorn/Flask ──▶ PostgreSQL
                  (TLS)     frontend                      backend             db (volume)
```

| | Local | Cloud |
|---|---|---|
| Command | `docker compose up --build` | `docker compose -f docker-compose.yml -f docker-compose.prod.yml up -d --build` |
| URL | http://localhost:8080 | https://`$DOMAIN` |
| Secrets | defaults are fine | **required**: the stack refuses to start without them |
| Public ports | 8080 | 80 and 443 (Caddy only) |

---

## 1. Recommended host: Azure for Students

**Why:** Azure for Students needs no credit card. You sign up with your
university e-mail and get **USD 100 credit for 12 months**. It also includes
**750 hours per month of a small Linux VM** (B1s, B2ats v2 or B2pts v2) for
12 months, which is enough to run one VM all month. You can renew it every year
while you are a student. A VM runs the exact `docker compose` stack that was
tested locally, so there are no platform-specific changes.
([Azure for Students](https://azure.microsoft.com/en-us/free/students))

### 1.1 Activate the subscription
1. Open <https://azure.microsoft.com/free/students> and choose **Start free**.
2. Sign in with your IU student account and verify your student status.
3. In the Azure portal, check **Subscriptions**: you should see "Azure for Students".

### 1.2 Set a budget alert (do this first)
**Cost Management → Budgets → Add:**
- amount **USD 10**, monthly;
- alerts at 50 % and 100 % to your e-mail.

You then hear about any unexpected cost long before the credit is used up.

### 1.3 Create the virtual machine
**Virtual machines → Create → Azure virtual machine**

| Setting | Value |
|---|---|
| Resource group | `edufinance-rg` (new) |
| Name | `edufinance-vm` |
| Region | West Europe or Germany West Central |
| Image | Ubuntu Server 24.04 LTS – x64 Gen2 |
| Size | **Standard_B2ats_v2** (2 vCPU, 1 GiB, free tier). *B1s also works but builds more slowly.* |
| Authentication | SSH public key, user name `azureuser` |
| Inbound ports | SSH (22), HTTP (80), HTTPS (443) |
| OS disk | keep the default (Standard SSD) |

Choose **Review + create → Create** and download the private key (`.pem`) when asked.

### 1.4 Give the VM a DNS name
**VM → Overview → DNS name → Configure.** Set a label, e.g. `edufinance-yourname`.
The VM is now reachable at:

```
edufinance-yourname.westeurope.cloudapp.azure.com
```

Caddy uses this name to get a free Let's Encrypt certificate. You don't need to
buy a domain.

### 1.5 Prepare the server (once)
```bash
# on your computer (Windows: PowerShell)
ssh -i path/to/edufinance-vm_key.pem azureuser@edufinance-yourname.westeurope.cloudapp.azure.com

# on the VM
curl -fsSL https://get.docker.com | sudo sh          # Docker Engine + Compose plugin
sudo usermod -aG docker $USER && newgrp docker

# 2 GB swap: the frontend build needs more than 1 GiB RAM
sudo fallocate -l 2G /swapfile && sudo chmod 600 /swapfile
sudo mkswap /swapfile && sudo swapon /swapfile
echo '/swapfile none swap sw 0 0' | sudo tee -a /etc/fstab

docker compose version                                  # must be v2.24 or newer
```

### 1.6 Get the code and configure it
```bash
git clone https://github.com/<your-account>/edufinance.git
cd edufinance
cp .env.example .env

# generate three secrets and paste them into .env
python3 -c "import secrets; [print(secrets.token_hex(32)) for _ in range(3)]"
nano .env
```

Set at least these values in `.env`:

```dotenv
POSTGRES_PASSWORD=<secret 1>
SECRET_KEY=<secret 2>
JWT_SECRET_KEY=<secret 3>
DOMAIN=edufinance-yourname.westeurope.cloudapp.azure.com
SEED_DEMO=true          # demo login for the tutor; set to false for real use
```

### 1.7 Start
```bash
docker compose -f docker-compose.yml -f docker-compose.prod.yml up -d --build
docker compose -f docker-compose.yml -f docker-compose.prod.yml ps        # all "running/healthy"
```

The first build takes about 5–10 minutes on the small VM. On start-up, the
backend runs the database migrations, seeds the master data and (with
`SEED_DEMO=true`) creates the demo user.

### 1.8 Check
| Check | Expected |
|---|---|
| `https://$DOMAIN/api/health` | `{"status": "ok", ...}` |
| `https://$DOMAIN` | Login page with a padlock (valid certificate) |
| Log in with **demo@edufinance.app / Demo#2026** | Dashboard of Ananya Rao |
| `http://$DOMAIN` | Redirects to https |

To keep typing short, add an alias on the VM:

```bash
echo "alias dc='docker compose -f docker-compose.yml -f docker-compose.prod.yml'" >> ~/.bashrc && source ~/.bashrc
```

---

## 2. Operating the app

| Task | Command (on the VM, in `edufinance/`) |
|---|---|
| Deploy a new version | `git pull && dc up -d --build` |
| Show logs | `dc logs -f backend` (or `caddy`, `frontend`, `db`) |
| Recreate the demo data | `dc exec backend flask seed-demo --reset` |
| Back up the database | `dc exec -T db pg_dump -U edufinance edufinance > backup.sql` |
| Restore a backup | `dc exec -T db psql -U edufinance edufinance < backup.sql` |
| Stop everything | `dc down` (the data stays in the `db_data` volume) |
| Save credit while not needed | Azure portal → VM → **Stop** (deallocates; the DNS name stays) |

Migrations are applied automatically on every start (`entrypoint.sh`), and so is
the master data seed. Both steps are idempotent.

### Security checklist
- [ ] Real secrets in `.env`; `.env` is never committed (it is in `.gitignore`).
- [ ] SSH only with a key; no password login (the Azure default for key-based VMs).
- [ ] Only ports 22, 80 and 443 are open in the network security group.
- [ ] `SEED_DEMO=false` once the app holds real personal data.
- [ ] Ubuntu security updates: `sudo apt update && sudo apt upgrade -y` from time to time.

### Troubleshooting
| Symptom | Cause / fix |
|---|---|
| `required variable ... is missing a value` | A secret or `DOMAIN` is missing in `.env`. |
| `!reset` unknown | Docker Compose is too old; reinstall Docker with the script above. |
| Browser warns about the certificate | DNS name and `DOMAIN` differ, or port 80/443 is closed. Check with `dc logs caddy`. |
| Build is killed (exit 137) | Out of memory: check the swap with `swapon --show`. |
| Amounts show "estimated" | The exchange-rate API was unreachable; the app uses the cache or fallback rates (ADR-0003). It recovers on its own. |

---

## 3. Alternative without a VM: Render + Neon

Use this if Azure is not available. Both have free tiers without a credit card.
1. **Neon** (<https://neon.tech>): create a PostgreSQL 16 project and copy the
   connection string. Change `postgresql://` to `postgresql+psycopg://` and keep
   `?sslmode=require`.
2. **Render** (<https://render.com>) → *New Web Service* from the repository:
   - root directory `backend`, runtime Docker;
   - environment: `DATABASE_URL`, `SECRET_KEY`, `JWT_SECRET_KEY`, `SEED_DEMO`.
3. **Render** → *New Static Site*:
   - root `frontend`, build `npm ci && npm run build`, publish `dist`;
   - rewrite rule `/api/*` → `https://<backend>.onrender.com/api/*`;
   - rewrite rule `/*` → `/index.html`.

Trade-offs: free Render services sleep after inactivity, so the first request
takes about a minute. The free Neon database is small but enough for a demo.
The Azure VM keeps the exact stack that was tested locally, which is why it is
the recommended option (see ADR-0010).
