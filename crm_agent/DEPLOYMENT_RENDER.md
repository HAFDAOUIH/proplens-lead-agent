# Deploy to Render - CRM Agent

Simple guide to deploy CRM Agent to Render.com in 10 minutes.

---

## Prerequisites

- ✅ GitHub account with repository
- ✅ Render account (free at https://render.com)
- ✅ Groq API key (get from https://console.groq.com)

---

## Step 1: Push to GitHub

```bash
cd /home/hafdaoui/Documents/Proplens/crm_agent

# Initialize git (if not already)
git init
git add .
git commit -m "Initial commit - CRM Agent"

# Push to GitHub
git remote add origin https://github.com/your-username/crm-agent.git
git branch -M main
git push -u origin main
```

---

## Step 2: Deploy with Render Blueprint

### Option A: Automatic (Recommended)

1. Go to https://dashboard.render.com
2. Click **"New"** → **"Blueprint"**
3. Connect your GitHub repository
4. Render will automatically detect `render.yaml`
5. Click **"Apply"**

### Option B: Manual

1. Go to https://dashboard.render.com
2. Click **"New"** → **"Web Service"**
3. Connect your GitHub repository
4. Configure:
   - **Name**: `crm-agent`
   - **Environment**: `Python 3`
   - **Build Command**:
     ```bash
     pip install -r requirements.txt && cd app && python manage.py migrate --noinput && python manage.py collectstatic --noinput
     ```
   - **Start Command**:
     ```bash
     cd app && gunicorn app.wsgi:application --bind 0.0.0.0:$PORT --workers 2 --threads 4 --timeout 120
     ```
   - **Plan**: Starter ($7/month) or Free

---

## Step 3: Configure Environment Variables

In Render Dashboard → Your Service → **Environment**:

### Required Variables

Click **"Add Environment Variable"** for each:

| Key | Value | Notes |
|-----|-------|-------|
| `SECRET_KEY` | Click "Generate" | Auto-generates secure key |
| `GROQ_API_KEY` | `gsk_your_key_here` | From console.groq.com |
| `DEBUG` | `False` | Production mode |
| `ALLOWED_HOSTS` | `crm-agent.onrender.com` | Your Render URL |
| `PYTHONPATH` | `/opt/render/project/src` | Required for imports |
| `CHROMA_DIR` | `/opt/render/project/src/data/chroma` | ChromaDB storage |

### Optional Variables

| Key | Value | Notes |
|-----|-------|-------|
| `OPENAI_API_KEY` | `sk_your_key` | Only for DeepEval testing |

---

## Step 4: Add Persistent Disk

**Important:** Without this, your data will be lost on restart!

1. In Render Dashboard → Your Service → **Disks**
2. Click **"Add Disk"**
3. Configure:
   - **Name**: `crm-agent-data`
   - **Mount Path**: `/opt/render/project/src/data`
   - **Size**: `10 GB`
4. Click **"Create"**

---

## Step 5: Deploy

1. Render will automatically deploy after adding disk
2. Or click **"Manual Deploy"** → **"Deploy latest commit"**
3. Wait 5-10 minutes (first deploy takes longer)
4. Watch the **Logs** tab for progress

Expected log output:
```
==> Building...
==> Installing dependencies...
==> Running migrations...
==> Collecting static files...
==> Starting application...
==> Your service is live!
```

---

## Step 6: Verify Deployment

### Check Health
```bash
curl https://crm-agent.onrender.com/api/health
```

Expected response:
```json
{
  "status": "healthy",
  "timestamp": "2025-11-05T..."
}
```

### Access Swagger Docs
Open in browser: https://crm-agent.onrender.com/api/docs

---

## Step 7: Create Admin User

1. In Render Dashboard → Your Service → **Shell**
2. Run:
   ```bash
   cd app
   python manage.py createsuperuser
   ```
3. Follow prompts to create admin user

---

## Step 8: Test the API

```bash
# Set your URL
URL="https://crm-agent.onrender.com"

# Login
TOKEN=$(curl -s -X POST "$URL/api/auth/login" \
  -H "Content-Type: application/json" \
  -d '{"username": "admin", "password": "your-password"}' | jq -r '.access')

# Test Agent (RAG)
curl -X POST "$URL/api/agent/query" \
  -H "Authorization: Bearer $TOKEN" \
  -H "Content-Type: application/json" \
  -d '{"question": "What amenities does Beachgate have?"}' | jq

# Test Agent (Analytics)
curl -X POST "$URL/api/agent/query" \
  -H "Authorization: Bearer $TOKEN" \
  -H "Content-Type: application/json" \
  -d '{"question": "How many Connected leads do we have?"}' | jq
```

---

## Step 9: Import Sample Data (Optional)

### Option A: Via Shell
```bash
# In Render Shell
cd app
python manage.py shell

>>> from crm_agent.ingestion.crm_loader import import_leads_from_excel
>>> import_leads_from_excel('/path/to/leads.xlsx')
>>> exit()
```

### Option B: Use Existing Data
The included `db.sqlite3` already has 300 sample leads. Your persistent disk will preserve this.

### Seed Vanna Training
```bash
# In Render Shell
cd app
python manage.py shell

>>> from crm_agent.ingestion.vanna_seed import VannaSeeder
>>> VannaSeeder().seed()
>>> exit()
```

---

## Step 10: Custom Domain (Optional)

1. In Render Dashboard → Your Service → **Settings**
2. Scroll to **Custom Domains**
3. Click **"Add Custom Domain"**
4. Enter your domain (e.g., `api.yourdomain.com`)
5. Configure DNS:
   - Add CNAME record: `api.yourdomain.com` → `crm-agent.onrender.com`
6. Wait for SSL certificate (automatic, ~5 minutes)

---

## Auto-Deploy on Git Push

Render automatically deploys when you push to your main branch:

```bash
# Make changes
git add .
git commit -m "Update feature"
git push

# Render automatically detects and deploys
```

---

## Monitoring & Logs

### View Logs
Dashboard → Your Service → **Logs** tab

### Check Metrics
Dashboard → Your Service → **Metrics** tab
- CPU usage
- Memory usage
- Request count
- Response times

### Health Checks
Render automatically checks `/api/health` every 30 seconds

---

## Scaling

### Upgrade Plan
Dashboard → Your Service → **Settings** → **Instance Type**
- Free: Sleeps after 15 minutes of inactivity
- Starter ($7/mo): Always on, better performance
- Standard ($25/mo): More memory/CPU

### Multiple Instances
Dashboard → Your Service → **Settings** → **Scaling**
- Increase instance count for high traffic
- Load balancing automatic

---

## Troubleshooting

### Issue: 500 Internal Server Error
**Check Logs:**
```
Dashboard → Logs tab
```
Common causes:
- Missing environment variables
- ALLOWED_HOSTS not set correctly
- Database migration failed

### Issue: Application sleeps (Free tier)
**Solution:** Upgrade to Starter plan ($7/mo)

### Issue: Data lost after restart
**Check:** Persistent disk is mounted at `/opt/render/project/src/data`

### Issue: Slow first request after sleep
**Expected:** Free tier sleeps after 15 minutes inactivity
- First request takes 30-60 seconds to wake up
- Upgrade to Starter for always-on

---

## Cost

### Free Tier
- $0/month
- 750 hours/month
- Sleeps after 15 minutes inactivity
- Good for testing

### Starter (Recommended)
- $7/month
- Always on
- Better performance
- Custom domains
- Good for production

### Storage
- 10GB disk: Included in plan
- Database: SQLite (included) or PostgreSQL (+$7/mo)

---

## Maintenance

### Update Application
```bash
# Local changes
git add .
git commit -m "Update"
git push

# Render auto-deploys
```

### Manual Deploy
Dashboard → Your Service → **Manual Deploy**

### Rollback
Dashboard → Your Service → **Events** → Click rollback on previous deploy

### Restart
Dashboard → Your Service → **Manual Deploy** → **Clear build cache & deploy**

---

## Security Best Practices

✅ **Done Automatically:**
- HTTPS with auto-renewing SSL
- Environment variable secrets
- Automatic security updates
- DDoS protection

✅ **You Should:**
- Use strong SECRET_KEY (auto-generated)
- Rotate API keys periodically
- Keep dependencies updated
- Monitor logs for suspicious activity

---

## Support

### Render Documentation
https://render.com/docs

### CRM Agent Docs
- **API Reference**: Swagger at `/api/docs`
- **Main Docs**: [README.md](README.md)
- **Test Commands**: [RUNBOOK.md](RUNBOOK.md)

### Common Commands
```bash
# View live logs
render logs -t <service-id>

# SSH into service (Starter plan+)
render shell <service-id>
```

---

## Success Checklist

- ✅ GitHub repository created and pushed
- ✅ Render service deployed successfully
- ✅ Environment variables configured
- ✅ Persistent disk added (10GB)
- ✅ Health check returns 200
- ✅ Swagger docs accessible
- ✅ Admin user created
- ✅ Sample data imported
- ✅ API endpoints tested
- ✅ Custom domain configured (optional)

---

**Your CRM Agent is now live!** 🚀

Access at: https://crm-agent.onrender.com/api/docs

Need help? Check [README.md](README.md) or [RUNBOOK.md](RUNBOOK.md).
