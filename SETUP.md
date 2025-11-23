# Setup Guide - College App Demo

This guide will help you get the application running locally.

## Prerequisites

- Docker and Docker Compose
- Python 3.11+ (for local development without Docker)
- Node.js 20+ (for frontend development)

## Quick Start with Docker (Recommended)

### 1. Clone and Setup Environment

```bash
git clone https://github.com/stdmitry04/campus-usa-demo.git
cd campus-usa-demo
```

### 2. Configure Backend Environment

```bash
cd server
cp .env.example .env
```

**Edit `server/.env` with your credentials:**

**Minimum required for local development:**
```env
SECRET_KEY=your-secret-key-here-generate-a-random-string
DEBUG=True
DOCKER=True
USE_S3_STORAGE=False
OPENAI_API_KEY=your-openai-api-key-here
```

> **Note:** You need an OpenAI API key for AI features. Get one at https://platform.openai.com/api-keys

**Full configuration (optional):**
- See `server/.env.example` for all available options
- AWS S3 credentials (if you want cloud storage instead of local)
- PostgreSQL database URL (if you want to use Postgres instead of SQLite)

### 3. Start Services

```bash
cd ..  # Back to project root
docker-compose up -d
```

This will start:
- **Django API** on http://localhost:8000
- **Redis** for task queue
- **Qdrant** vector database on http://localhost:6333
- **Celery** workers for async tasks

### 4. Run Database Migrations

```bash
docker-compose exec web python manage.py migrate
docker-compose exec web python manage.py createsuperuser
docker-compose exec web python manage.py seed_universities
```

### 5. Access the Application

- **API:** http://localhost:8000
- **API Docs:** http://localhost:8000/api/
- **Admin Panel:** http://localhost:8000/admin
- **Qdrant Dashboard:** http://localhost:6333/dashboard

## Frontend Setup (Optional)

The backend API is standalone and can be tested via the admin panel or API directly. To run the frontend:

### 1. Install Dependencies

```bash
cd website
npm install
```

### 2. Configure Frontend Environment

```bash
cp .env.example .env.local
```

The default configuration (`NEXT_PUBLIC_API_URL=http://localhost:8000/api`) should work out of the box.

### 3. Run Development Server

```bash
npm run dev
```

Access at http://localhost:3000

## Local Development (Without Docker)

### Backend Setup

1. **Create Virtual Environment**
```bash
cd server
python -m venv .venv
source .venv/bin/activate  # On Windows: .venv\Scripts\activate
```

2. **Install Dependencies**
```bash
pip install -r requirements.txt
```

3. **Configure Environment**
```bash
cp .env.example .env
# Edit .env and set DOCKER=False
```

4. **Install Required Services**
- Redis: `brew install redis` (Mac) or download from redis.io
- Qdrant: Run with Docker: `docker run -p 6333:6333 qdrant/qdrant`

5. **Run Migrations**
```bash
python manage.py migrate
python manage.py createsuperuser
python manage.py seed_universities
```

6. **Start Services**

Terminal 1 - Django:
```bash
python manage.py runserver
```

Terminal 2 - Celery:
```bash
celery -A celery_app worker --loglevel=info
```

Terminal 3 - Redis (if not running):
```bash
redis-server
```

## Features & Testing

### 1. Document Upload & OCR
- Upload PDFs, images, or Word documents
- Automatic text extraction via OCR
- View extracted text and metadata

### 2. RAG Chat Assistant
- Ask questions about uploaded documents
- Semantic search using vector embeddings
- Context-aware responses

### 3. University Search (Demo Data)
- Browse demo universities
- Filter and search capabilities
- Save favorites

### 4. Essay Management
- Create and manage essays
- Get mock AI feedback (proprietary logic removed)

## Configuration Options

### Storage Options

**Local Storage (Default):**
```env
USE_S3_STORAGE=False
```
Files stored in `server/media/`

**AWS S3 Storage:**
```env
USE_S3_STORAGE=True
AWS_ACCESS_KEY_ID=your-key
AWS_SECRET_ACCESS_KEY=your-secret
AWS_STORAGE_BUCKET_NAME=your-bucket
```

### Database Options

**SQLite (Default):**
No configuration needed - uses `server/db.sqlite3`

**PostgreSQL:**
```env
DATABASE_URL=postgresql://user:password@localhost:5432/dbname
```

### AI Features

**Required for:**
- Document embeddings
- RAG chat
- Semantic search

```env
OPENAI_API_KEY=sk-...
```

**Optional Services:**
```env
ENABLE_VIRUS_SCANNING=False
ENABLE_CONTENT_ANALYSIS=False
```

## Troubleshooting

### Port Already in Use
```bash
# Change ports in docker-compose.yml
ports:
  - "8001:8000"  # Use 8001 instead of 8000
```

### Redis Connection Failed
```bash
# Check Redis is running
docker-compose ps redis

# Restart Redis
docker-compose restart redis
```

### Celery Tasks Not Running
```bash
# Check Celery worker logs
docker-compose logs celery

# Restart Celery
docker-compose restart celery
```

### Database Migrations
```bash
# Reset database (CAUTION: deletes all data)
docker-compose exec web python manage.py flush
docker-compose exec web python manage.py migrate
docker-compose exec web python manage.py seed_universities
```

## Development Notes

### Demo Limitations

**Replaced with Mock Data:**
- AI essay generation (returns hardcoded feedback)
- Real university partnerships (generic demo universities)

**Fully Functional:**
- Complete OCR pipeline
- RAG system with vector search
- Document management
- User authentication
- All CRUD operations

### API Testing

Use the Django admin or tools like Postman/curl:

```bash
# Get JWT token
curl -X POST http://localhost:8000/api/auth/login/ \
  -H "Content-Type: application/json" \
  -d '{"username":"admin","password":"your-password"}'

# Use token in requests
curl http://localhost:8000/api/documents/ \
  -H "Authorization: Bearer YOUR_TOKEN"
```

## Production Deployment

This is a demo repository. For production:

1. Set `DEBUG=False`
2. Use PostgreSQL database
3. Configure AWS S3 for file storage
4. Set strong `SECRET_KEY`
5. Configure proper `ALLOWED_HOSTS`
6. Enable SSL/HTTPS
7. Use environment variables for all secrets
8. Set up monitoring and logging

## Support

This is a demonstration project. For questions about the technical implementation, review the code and documentation.

## License

MIT License - see LICENSE file
