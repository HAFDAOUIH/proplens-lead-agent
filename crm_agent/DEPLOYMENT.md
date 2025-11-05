# Deployment Guide - CRM Agent

Choose your deployment method:

---

## Quick Links

- **Render.com** (Recommended): [DEPLOYMENT_RENDER.md](DEPLOYMENT_RENDER.md) ← **Start here**
- **Docker**: See below for local/self-hosted deployment

---

## Option 1: Render.com (Recommended for Production)

**Best for:** Production deployment with minimal setup

See complete guide: **[DEPLOYMENT_RENDER.md](DEPLOYMENT_RENDER.md)**

**Quick Summary:**
1. Push code to GitHub
2. Connect to Render (uses `render.yaml`)
3. Add environment variables (SECRET_KEY, GROQ_API_KEY)
4. Add persistent disk (10GB)
5. Deploy!

**Time:** 10-15 minutes
**Cost:** $7/month (Starter plan)
**Features:** Auto-deploy, SSL, monitoring, scaling

---

## Option 2: Docker (Local/Self-Hosted)

**Best for:** Local development, testing, or self-hosted VPS

### Quick Start

```bash
cd /home/hafdaoui/Documents/Proplens/crm_agent

# Create environment file
cp .env.example .env
nano .env  # Add GROQ_API_KEY and SECRET_KEY

# Start with Docker Compose
docker-compose up -d

# Check logs
docker-compose logs -f

# Access
# http://localhost:8000
# http://localhost:8000/api/docs
```

### Docker Commands

```bash
# Start services
docker-compose up -d

# Stop services
docker-compose down

# View logs
docker-compose logs -f crm-agent

# Rebuild after code changes
docker-compose build --no-cache
docker-compose up -d

# Create superuser
docker-compose exec crm-agent python app/manage.py createsuperuser

# Access shell
docker-compose exec crm-agent bash

# Run migrations
docker-compose exec crm-agent python app/manage.py migrate
```

### Environment Variables

Required in `.env` file:

```bash
SECRET_KEY=your-django-secret-key-change-this
GROQ_API_KEY=gsk_your_groq_api_key_here
DEBUG=False
ALLOWED_HOSTS=localhost,127.0.0.1
```

Generate SECRET_KEY:
```python
python -c "from django.core.management.utils import get_random_secret_key; print(get_random_secret_key())"
```

### Docker Configuration

The included `docker-compose.yml` provides:
- ✅ Persistent volumes (ChromaDB, database, uploads)
- ✅ Health checks
- ✅ Auto-restart
- ✅ Network isolation

### Production Docker Setup

For production on a VPS with Docker:

1. **Install Docker:**
   ```bash
   curl -fsSL https://get.docker.com -o get-docker.sh
   sudo sh get-docker.sh
   sudo usermod -aG docker $USER
   ```

2. **Clone and configure:**
   ```bash
   git clone <your-repo>
   cd crm_agent
   cp .env.example .env
   nano .env  # Configure
   ```

3. **Deploy:**
   ```bash
   docker-compose up -d
   ```

4. **Add Nginx (optional):**
   ```nginx
   # /etc/nginx/sites-available/crm-agent
   server {
       listen 80;
       server_name your-domain.com;

       location / {
           proxy_pass http://localhost:8000;
           proxy_set_header Host $host;
           proxy_set_header X-Real-IP $remote_addr;
       }
   }
   ```

5. **Enable SSL:**
   ```bash
   sudo apt install certbot python3-certbot-nginx
   sudo certbot --nginx -d your-domain.com
   ```

---

## Environment Configuration

### Required Variables

```bash
SECRET_KEY=<50-character-random-string>
GROQ_API_KEY=gsk_your_groq_api_key
DEBUG=False
ALLOWED_HOSTS=your-domain.com,localhost
```

### Optional Variables

```bash
OPENAI_API_KEY=sk_your_key  # For DeepEval only
CHROMA_DIR=/app/data/chroma  # ChromaDB storage
DATABASE_URL=postgresql://...  # If using PostgreSQL
```

---

## Post-Deployment Steps

### 1. Verify Health

```bash
curl https://your-domain.com/api/health
```

Expected: `{"status": "healthy"}`

### 2. Create Admin User

```bash
# Render: Use Shell in dashboard
# Docker: docker-compose exec crm-agent python app/manage.py createsuperuser

cd app
python manage.py createsuperuser
```

### 3. Test API

```bash
URL="https://your-domain.com"

# Login
TOKEN=$(curl -s -X POST "$URL/api/auth/login" \
  -H "Content-Type: application/json" \
  -d '{"username": "admin", "password": "your-pass"}' | jq -r '.access')

# Test
curl -X POST "$URL/api/agent/query" \
  -H "Authorization: Bearer $TOKEN" \
  -H "Content-Type: application/json" \
  -d '{"question": "What amenities does Beachgate have?"}' | jq
```

### 4. Import Data (Optional)

The included `db.sqlite3` has 300 sample leads. To import your own:

```bash
python app/manage.py shell

>>> from crm_agent.ingestion.crm_loader import import_leads_from_excel
>>> import_leads_from_excel('/path/to/leads.xlsx')
>>> exit()
```

### 5. Seed Vanna Training

```bash
python app/manage.py shell

>>> from crm_agent.ingestion.vanna_seed import VannaSeeder
>>> VannaSeeder().seed()
>>> exit()
```

---

## Monitoring

### Health Checks

Endpoint: `GET /api/health`

Returns:
```json
{
  "status": "healthy",
  "timestamp": "2025-11-05T16:30:00Z"
}
```

### Logs

**Render:** Dashboard → Logs tab
**Docker:** `docker-compose logs -f`

### Metrics

Monitor:
- Response times (aim for < 3s)
- Error rate (aim for < 1%)
- Memory usage
- Disk usage

---

## Troubleshooting

### Issue: Can't connect to API

**Check:**
- Service is running
- Firewall allows ports (80/443 or 8000)
- ALLOWED_HOSTS includes your domain
- DNS configured correctly

### Issue: 500 Internal Server Error

**Check logs for:**
- Missing environment variables
- Database connection issues
- Import errors

**Solution:**
```bash
# Render: Check Dashboard → Logs
# Docker: docker-compose logs crm-agent
```

### Issue: ChromaDB data lost

**Render:** Verify persistent disk is mounted
**Docker:** Check volumes: `docker volume ls`

### Issue: Slow responses

**Possible causes:**
- Render free tier sleep (upgrade to Starter)
- Cold start (first request after inactivity)
- Large ChromaDB queries (optimize k parameter)

---

## Scaling

### Render

- **Vertical:** Upgrade plan (Starter → Standard)
- **Horizontal:** Increase instance count in dashboard

### Docker

- **Vertical:** Increase memory/CPU in docker-compose.yml
- **Horizontal:** Use Docker Swarm or Kubernetes

---

## Backup Strategy

### Database Backup

```bash
# SQLite
cp app/db.sqlite3 backup_$(date +%Y%m%d).sqlite3

# PostgreSQL
pg_dump dbname > backup_$(date +%Y%m%d).sql
```

### ChromaDB Backup

```bash
tar -czf chroma_backup_$(date +%Y%m%d).tar.gz data/chroma/
```

### Automated Backups

**Render:** Use persistent disk snapshots
**Docker:** Cron job + cloud storage

---

## Security Checklist

- ✅ DEBUG=False
- ✅ Strong SECRET_KEY
- ✅ HTTPS enabled
- ✅ API keys in environment variables
- ✅ ALLOWED_HOSTS configured
- ✅ Regular updates
- ✅ Monitoring enabled

---

## Cost Comparison

| Option | Cost/Month | Pros | Cons |
|--------|-----------|------|------|
| **Render Starter** | $7 | Easy, auto-SSL, always-on | Limited resources |
| **Docker VPS** | $6+ | Full control, flexible | Manual SSL, maintenance |
| **Render Free** | $0 | Testing | Sleeps after 15min |

---

## Support

- **Render Guide:** [DEPLOYMENT_RENDER.md](DEPLOYMENT_RENDER.md)
- **API Docs:** `/api/docs` (Swagger)
- **Main Docs:** [README.md](README.md)
- **Test Commands:** [RUNBOOK.md](RUNBOOK.md)

---

## Quick Decision Matrix

**Choose Render if:**
- ✅ You want easiest deployment
- ✅ You need production-ready quickly
- ✅ You want auto-deploy on git push
- ✅ You prefer managed hosting

**Choose Docker if:**
- ✅ You want full control
- ✅ You already have a VPS
- ✅ You need custom networking
- ✅ You're developing locally

---

**Recommendation:** Start with **[Render](DEPLOYMENT_RENDER.md)** for production. Use Docker for local development.

🚀 **Ready?** Go to [DEPLOYMENT_RENDER.md](DEPLOYMENT_RENDER.md) to deploy now!
