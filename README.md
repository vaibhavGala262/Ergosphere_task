# Book Document Intelligence Platform

Full-stack AI-powered platform for scraping books, indexing semantic chunks, running RAG Q&A, and serving a modern frontend.

## Implemented Scope

### Backend (Django REST Framework)
- `Book`, `BookChunk`, `ChatHistory` models
- APIs:
  - `GET /api/books/`
  - `GET /api/books/{id}/`
  - `GET /api/books/{id}/recommend/`
  - `POST /api/books/upload/`
  - `GET /api/books/upload/{task_id}/status/`
  - `POST /api/query/`
- Full RAG flow:
  - semantic + overlap chunking
  - embedding generation (Gemini/OpenAI/SentenceTransformers)
  - ChromaDB storage + retrieval
  - grounded answer generation with citations
- AI features:
  - summary generation
  - genre classification
  - sentiment analysis
  - recommendation by embedding similarity
- Advanced features:
  - Redis caching
  - Celery background ingestion
  - rate limiting
  - chat history by session ID

### Frontend (Next.js + Tailwind)
- Dashboard with search/filter, cards, and ingestion panel
- Book detail page with summary/genre/sentiment/recommendations
- Q&A page with citations, loading states, and toast status feedback
- Dark mode and responsive layout

### Infrastructure
- Dockerized multi-service stack:
  - `frontend`
  - `backend`
  - `celery`
  - `mysql`
  - `redis`
  - `selenium` (for scraping)

---

## Run On Any Machine (Docker-First)

### 1. Pull code

```bash
git pull
```

### 2. Prepare docker env

```bash
cp .env.docker.example .env.docker
```

Edit `.env.docker` and set at least:
- `DJANGO_SECRET_KEY`
- `GEMINI_API_KEY` (or OpenAI keys if using OpenAI)
- MySQL creds if you change defaults

### 3. Build and start

```bash
docker compose --env-file .env.docker up --build -d
```

### 4. Check containers

```bash
docker compose ps
```

All should be `running`:
- `dip_mysql`
- `dip_redis`
- `dip_selenium`
- `dip_backend`
- `dip_celery`
- `dip_frontend`

### 5. Open app
- Frontend: `http://localhost:3000`
- API base: `http://localhost:8000/api`

### 6. First data ingestion

```bash
curl -X POST http://localhost:8000/api/books/upload/ \
  -H "Content-Type: application/json" \
  -d "{\"pages\":2}"
```

Capture `task_id`, then monitor:

```bash
curl http://localhost:8000/api/books/upload/<task_id>/status/
```

When status is `SUCCESS`, test books:

```bash
curl http://localhost:8000/api/books/
```

Test RAG:

```bash
curl -X POST http://localhost:8000/api/query/ \
  -H "Content-Type: application/json" \
  -d "{\"question\":\"Which books have hopeful emotional themes?\",\"top_k\":4}"
```

---

## Local Run (Without Docker)

### 1. Environment

```bash
cp .env.example .env
```

Use:
- `DB_ENGINE=sqlite` for quick local run
- or `DB_ENGINE=mysql` if local MySQL is available

Run Redis locally if using Celery/cache in local mode.

### 2. Backend

```bash
python -m venv .venv
# Windows:
.venv\Scripts\activate
pip install -r requirements.txt
cd backend
python manage.py migrate
python manage.py runserver
```

### 3. Celery

```bash
cd backend
celery -A config worker -l info --pool=solo
```

### 4. Frontend

```bash
cd frontend
npm install
npm run dev
```

---

## Provider Configuration

### Gemini

```env
LLM_PROVIDER=gemini
EMBEDDING_PROVIDER=gemini
GEMINI_API_KEY=your_key
GEMINI_CHAT_MODEL=gemini-2.5-flash
GEMINI_EMBEDDING_MODEL=text-embedding-004
```

### OpenAI

```env
LLM_PROVIDER=openai
EMBEDDING_PROVIDER=openai
OPENAI_API_KEY=your_key
OPENAI_CHAT_MODEL=gpt-4o-mini
OPENAI_EMBEDDING_MODEL=text-embedding-3-small
```

### Hybrid

```env
LLM_PROVIDER=gemini
EMBEDDING_PROVIDER=sentence-transformers
EMBEDDING_MODEL=sentence-transformers/all-MiniLM-L6-v2
```

---

## API Quick Reference

### GET
- `/api/books/`
- `/api/books/{id}/`
- `/api/books/{id}/recommend/`
- `/api/books/upload/{task_id}/status/`

### POST
- `/api/books/upload/`
```json
{ "pages": 3, "start_url": "https://books.toscrape.com/" }
```
- `/api/query/`
```json
{ "question": "Which books focus on emotional recovery?", "session_id": "optional", "top_k": 4 }
```

---

## Notes

- Scraper target is `books.toscrape.com` for safe public scraping demos.
- In Docker mode, Selenium is provided by `selenium/standalone-chrome`.
- Chroma data persists via Docker volume (`chroma_data`).
- MySQL data persists via Docker volume (`mysql_data`).
