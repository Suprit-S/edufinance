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

**Live instance:** <https://edufinance-suprit.swedencentral.cloudapp.azure.com>
(Sweden Central, Standard_B2ats_v2). The steps below are the ones used to set it up.

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
Open **Cost Management**. If the scope shows your *billing account* (your name), click
**(change)** and select the **Azure for Students** subscription. Then **Monitoring → Budgets → Add**:
- amount **USD 10**, monthly;
- alerts at 50 % and 100 % to your e-mail.

You then hear about any unexpected cost long before the credit is used up.

### 1.3 Find the regions you may use
Azure for Students only allows a fixed set of regions for each subscription. Other regions fail
at *Create* with `RequestDisallowedByAzure` ("This policy maintains a set of best available
regions…").

**Policy → Assignments → *Allowed resource deployment regions* → Parameters** shows the list.
For this project it was:

`switzerlandnorth, germanywestcentral, norwayeast, swedencentral, austriaeast`

(Central India and West Europe were **not** allowed.) Pick one from your own list.

### 1.4 Create the virtual machine
**Virtual machines → Create → Azure virtual machine**

| Setting | Value |
|---|---|
| Resource group | `edufinance-rg` (new) |
| Name | `edufinance-vm` |
| Region | an allowed region from 1.3 – used here: **Sweden Central** |
| Image | Ubuntu Server 24.04 LTS – x64 Gen2 |
| VM architecture | x64 |
| Size | **See all sizes** → search `B2ats` → **Standard_B2ats_v2** (2 vCPU, 1 GiB, free services eligible, about $4.49/month list price). If it is greyed out, the region has no capacity: try another allowed region. *B1s also works but builds more slowly.* Never keep the pre-selected D-series size (≈ $88/month). |
| Authentication | SSH public key, user name `azureuser`, **Generate new key pair**, name `edufinance-vm_key` |
| Inbound ports | Allow selected ports: SSH (22), HTTP (80), HTTPS (443) |
| Disks tab | OS disk size **64 GiB (P6)**, **Premium SSD** (matches the free-tier disk) |

Choose **Review + create → Create** and **download the private key** (`.pem`) when asked. Azure
cannot show it again – keep it safe (e.g. `C:\Users\<you>\.ssh\`).

### 1.5 Give the VM a DNS name
**VM → Overview → DNS name → Configure.** Set a unique label, e.g. `edufinance-suprit`, and
**Save**. The VM is now reachable at `<label>.<region>.cloudapp.azure.com`, here:

```
edufinance-suprit.swedencentral.cloudapp.azure.com
```

Caddy uses this name to get a free Let's Encrypt certificate. You don't need to
buy a domain.

### 1.6 Prepare the server (once)
```powershell
# on your computer (Windows: PowerShell), in the folder with the key
ssh -i .\edufinance-vm_key.pem azureuser@edufinance-suprit.swedencentral.cloudapp.azure.com
# first time: answer "yes"
```

If Windows reports *UNPROTECTED PRIVATE KEY FILE*, restrict the key to your user:

```powershell
icacls .\edufinance-vm_key.pem /inheritance:r
icacls .\edufinance-vm_key.pem /grant:r "$($env:USERNAME):(R)"
icacls .\edufinance-vm_key.pem /remove "Authenticated Users" "BUILTIN\Users" "Everyone"
```

On the VM:

```bash
curl -fsSL https://get.docker.com | sudo sh          # Docker Engine + Compose plugin
sudo usermod -aG docker $USER && newgrp docker

# 2 GB swap: the frontend build needs more than 1 GiB RAM
sudo fallocate -l 2G /swapfile && sudo chmod 600 /swapfile
sudo mkswap /swapfile && sudo swapon /swapfile
echo '/swapfile none swap sw 0 0' | sudo tee -a /etc/fstab

docker compose version                                  # must be v2.24 or newer
```

### 1.7 Get the code and configure it
```bash
cd ~
git clone https://github.com/<your-account>/edufinance.git   # private repo: password = personal access token (scope "repo")
cd edufinance
```

Create `.env` with three random secrets and your DNS name (no manual editing needed):

```bash
cp .env.example .env
sed -i "s|^POSTGRES_PASSWORD=.*|POSTGRES_PASSWORD=$(openssl rand -hex 32)|" .env
sed -i "s|^SECRET_KEY=.*|SECRET_KEY=$(openssl rand -hex 32)|" .env
sed -i "s|^JWT_SECRET_KEY=.*|JWT_SECRET_KEY=$(openssl rand -hex 32)|" .env
sed -i "s|^DOMAIN=.*|DOMAIN=edufinance-suprit.swedencentral.cloudapp.azure.com|" .env
chmod 600 .env
```

`SEED_DEMO=true` (default) creates the demo login for the tutor; set it to `false` for real use.

### 1.8 Start
```bash
docker compose -f docker-compose.yml -f docker-compose.prod.yml up -d --build
docker compose -f docker-compose.yml -f docker-compose.prod.yml ps        # all "running/healthy"
```

The first build took about 7 minutes on the B2ats_v2 VM (including all downloads). On start-up, the
backend runs the database migrations, seeds the master data and (with
`SEED_DEMO=true`) creates the demo user.

### 1.9 Check
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
| `RequestDisallowedByAzure` when creating the VM | Region not allowed for the subscription – see 1.3. |
| Size greyed out / "not available" | No capacity for that size in the region – choose another allowed region. |
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
