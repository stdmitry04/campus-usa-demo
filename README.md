# College Application Platform - Demo

A comprehensive full-stack web application demonstrating modern college application management with intelligent university matching, document management, and AI-powered guidance.

**Note:** This is a demonstration version of a production education platform. Proprietary business logic, real university partnerships, and customer-specific features have been replaced with generic implementations.

## Architecture Overview

This application demonstrates modern full-stack development practices with a Django REST API backend and Next.js frontend, implementing secure file handling, real-time features, and scalable cloud architecture.

### System Architecture

**Technology Stack:**
- **Backend:** Python 3.11.8, Django 5.2, Django REST Framework, JWT Authentication, AWS S3 Integration
- **Frontend:** Node 20.17.0, Next.js 15 (App Router), React 19, TypeScript, Tailwind CSS
- **Database:** PostgreSQL (Production), SQLite (Development)
- **Infrastructure:** Docker Compose, AWS S3 (File Storage)
- **Development:** Docker support, automated migrations, comprehensive testing

## Key Features & Technical Implementation

### 1. Secure File Management System
- **AWS S3 Integration:** Direct client-to-S3 uploads using pre-signed URLs
- **Security:** Multi-layer file validation (client-side, server-side, MIME type verification)
- **Scalability:** Handles large file uploads without server load
- **File Types:** PDF, Microsoft Office documents, images with automatic processing

### 2. University Database (Demo Data)
- **Dynamic Filtering:** University search and filtering capabilities
- **Performance Optimization:** Cached queries, indexed database searches
- **Data Management:** Sample university database for demonstration
- **User Experience:** Save/bookmark functionality with optimistic UI updates

### 3. AI-Powered RAG Chat Assistant
- **Conversational AI:** Context-aware responses using RAG (Retrieval Augmented Generation)
- **Document Search:** Semantic search over uploaded documents using vector embeddings
- **Chat Management:** Persistent conversation history with user sessions
- **Vector Database:** Qdrant integration for efficient similarity search

### 4. Advanced Profile Management
- **Multi-section Profiles:** Academic information, preferences, document tracking
- **Progress Tracking:** Completion indicators and guided onboarding
- **Data Validation:** Comprehensive form validation with real-time feedback
- **Image Handling:** Avatar upload with compression and format optimization

## Technical Highlights

### Backend Architecture

**Django REST API Design:**
- Token-based authentication with JWT
- User-scoped data isolation
- Async task processing with Celery
- OCR and document processing pipeline
- RAG system with OpenAI embeddings and Qdrant

**Key Technical Patterns:**
- Service layer architecture
- Async task chains with Celery
- S3 pre-signed URL uploads
- Vector embeddings for semantic search
- Document validation and OCR

### Frontend Architecture

**Next.js 15 App Router:**
- Server and client components
- API route handlers
- TypeScript for type safety
- Tailwind CSS for styling
- React Query for data fetching

## Quick Start

### Prerequisites
- Docker and Docker Compose
- AWS S3 bucket (for file storage)
- OpenAI API key (for embeddings and AI features)

### Environment Setup

1. **Clone and Setup:**
```bash
cd server
cp .env.example .env
# Edit .env with your credentials
```

2. **Required Environment Variables:**
```
# Django
SECRET_KEY=your-secret-key
DEBUG=True
ALLOWED_HOSTS=localhost,127.0.0.1

# AWS S3
AWS_ACCESS_KEY_ID=your-access-key
AWS_SECRET_ACCESS_KEY=your-secret-key
AWS_STORAGE_BUCKET_NAME=your-bucket-name
AWS_S3_REGION_NAME=us-east-1

# OpenAI
OPENAI_API_KEY=your-openai-key

# Qdrant
QDRANT_URL=http://qdrant:6333

# Redis
REDIS_HOST=redis
REDIS_PORT=6379
```

3. **Start Services:**
```bash
docker-compose up -d
```

4. **Run Migrations:**
```bash
docker-compose exec web python manage.py migrate
docker-compose exec web python manage.py createsuperuser
docker-compose exec web python manage.py seed_universities
```

5. **Access Application:**
- API: http://localhost:8000
- Admin: http://localhost:8000/admin
- Qdrant Dashboard: http://localhost:6333/dashboard

## Project Structure

```
college-app-demo/
├── server/                 # Django backend
│   ├── core/              # Core services (OCR, RAG, embeddings)
│   ├── documents/         # Document management
│   ├── essays/            # Essay storage
│   ├── messaging/         # AI chat with RAG
│   ├── universities/      # University database (demo data)
│   └── users/             # Authentication & profiles
├── website/               # Next.js frontend
│   └── src/
│       ├── app/          # App router pages
│       ├── components/   # React components
│       ├── hooks/        # Custom hooks
│       └── lib/          # Utilities and API client
└── docker-compose.yml    # Docker orchestration
```

## Demo Limitations

**Proprietary Business Logic Removed:**
- AI essay generation and feedback (replaced with mock responses)
- Real university partnership data (replaced with generic demo universities)
- Custom validation rules (genericized)
- Business-specific workflows

**What's Preserved:**
- Complete technical architecture
- OCR and document processing
- RAG system with vector search
- All common technical patterns
- Full authentication system

## License

MIT License - This is a demonstration project

## Author

**Dmitry** - Full-Stack Engineer

This system demonstrates enterprise-level full-stack development capabilities while respecting proprietary business requirements.
