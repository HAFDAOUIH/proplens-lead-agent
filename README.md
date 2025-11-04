# Proplens CRM Agent

A Django-based CRM agent system with vector search capabilities for real estate lead management and brochure processing.

## Features

- **Lead Management**: Import and manage CRM leads from Excel files
- **Document Processing**: Extract and process PDF brochures with OCR support
- **Vector Search**: Semantic search over brochure content using ChromaDB
- **JWT Authentication**: Secure API access with JWT tokens
- **Lead Shortlisting**: Advanced filtering with multiple criteria

## Tech Stack

- **Framework**: Django 5.1.2 + Django Ninja
- **Database**: SQLite (development)
- **Vector Store**: ChromaDB (embedded, persistent)
- **Embeddings**: sentence-transformers (all-MiniLM-L6-v2)
- **PDF Processing**: pypdf + pytesseract (OCR fallback)

## Quick Start

### Prerequisites

- Python 3.8+
- Virtual environment (recommended)

### Installation

```bash
# Create and activate virtual environment
python -m venv .venv
source .venv/bin/activate  # On Windows: .venv\Scripts\activate

# Install dependencies
pip install -r crm_agent/requirements.txt

# Navigate to Django app
cd crm_agent/app

# Run migrations
python manage.py migrate

# Create superuser (optional, for admin access)
python manage.py createsuperuser

# Run development server
uvicorn app.asgi:application --reload --host 0.0.0.0 --port 8000
```

## API Endpoints

### Authentication
- `POST /api/login` - Get JWT token
- `GET /api/health` - Health check (public)
- `GET /api/health-protected` - Protected health check

### Leads
- `POST /api/leads/import` - Import leads from Excel file
- `POST /api/leads/shortlist` - Filter leads (requires ≥2 filters)

### Documents
- `POST /api/docs/upload` - Upload brochure PDFs
- `GET /api/docs/search` - Semantic search over brochures
- `GET /api/docs/count` - Count total chunks in vector store

## Documentation

For detailed API documentation and usage examples, see:
- [RUNBOOK.md](crm_agent/RUNBOOK.md) - Detailed runbook with test commands

## Project Structure

```
crm_agent/
├── api/           # API endpoints (auth, leads, docs)
├── app/           # Django application
├── core/          # Core services (embeddings, vector store)
├── ingestion/     # Data ingestion utilities
└── data/          # Data storage (vector DB, brochures)
```

## License

MIT

