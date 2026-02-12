# GitHub Scraper FastAPI

A RESTful API for scraping GitHub profiles, repositories, and README files built with FastAPI.

## 🚀 Features

- ✅ **Async Operations** - High-performance async scraping with aiohttp
- ✅ **Background Jobs** - Long-running scrapes with job tracking
- ✅ **Caching** - In-memory caching with TTL support
- ✅ **Multiple Export Formats** - Excel, CSV, JSON
- ✅ **Rate Limiting** - Built-in rate limit protection
- ✅ **OpenAPI Docs** - Auto-generated interactive API documentation
- ✅ **CORS Support** - Configurable CORS for web clients
- ✅ **Job Management** - Track, cancel, and cleanup background jobs

## 📋 Requirements

- Python 3.8+
- FastAPI
- uvicorn
- aiohttp
- pandas
- openpyxl

## 🔧 Installation

### 1. Clone or Extract

```bash
cd github-scraper-api
```

### 2. Create Virtual Environment

```bash
python -m venv venv

# Activate (Linux/Mac)
source venv/bin/activate

# Activate (Windows)
venv\Scripts\activate
```

### 3. Install Dependencies

```bash
pip install -r requirements.txt
```

### 4. Configure Environment

```bash
cp .env.example .env
# Edit .env with your settings
```

## 🏃 Running the API

### Development Mode

```bash
# Start with auto-reload
uvicorn app.main:app --reload

# Or use the main module
python -m app.main
```

### Production Mode

```bash
uvicorn app.main:app --host 0.0.0.0 --port 8000 --workers 4
```

The API will be available at:
- **API**: http://localhost:8000
- **Interactive Docs**: http://localhost:8000/docs
- **Alternative Docs**: http://localhost:8000/redoc

## 📚 API Endpoints

### Health & Info

```bash
# Root endpoint
GET /

# Health check
GET /health

# API statistics
GET /api/v1/stats
```

### Scraping Endpoints

#### Scrape User Profile

```bash
GET /api/v1/scrape/profile/{username}?token=YOUR_TOKEN
```

**Example:**
```bash
curl http://localhost:8000/api/v1/scrape/profile/octocat
```

**Response:**
```json
{
  "success": true,
  "username": "octocat",
  "profile": {
    "login": "octocat",
    "name": "The Octocat",
    "bio": "...",
    "public_repos": 8,
    "followers": 9999
  },
  "cached": false,
  "timestamp": "2024-02-11T10:00:00"
}
```

#### Scrape Repositories

```bash
GET /api/v1/scrape/repositories/{username}?max_repos=50&include_readme=true
```

**Example:**
```bash
curl "http://localhost:8000/api/v1/scrape/repositories/torvalds?max_repos=10"
```

#### Complete Scrape

```bash
GET /api/v1/scrape/complete/{username}
```

**Example:**
```bash
curl http://localhost:8000/api/v1/scrape/complete/octocat
```

**Response:**
```json
{
  "success": true,
  "username": "octocat",
  "profile": {...},
  "repositories": [...],
  "total_stars": 12345,
  "total_forks": 5678,
  "top_languages": {
    "Python": 10,
    "JavaScript": 5
  }
}
```

#### Async Scraping (Background Job)

```bash
POST /api/v1/scrape/async/{username}
```

**Request Body:**
```json
{
  "username": "torvalds",
  "token": "your_token",
  "max_repos": 100,
  "include_readme": true,
  "truncate_readme": true,
  "export_format": "excel"
}
```

**Example:**
```bash
curl -X POST http://localhost:8000/api/v1/scrape/async/torvalds \
  -H "Content-Type: application/json" \
  -d '{"username": "torvalds", "export_format": "excel"}'
```

**Response:**
```json
{
  "job_id": "123e4567-e89b-12d3-a456-426614174000",
  "status": "pending",
  "message": "Scraping job started",
  "status_url": "/api/v1/jobs/123e4567-e89b-12d3-a456-426614174000"
}
```

### Job Management

#### Get Job Status

```bash
GET /api/v1/jobs/{job_id}
```

**Response:**
```json
{
  "job_id": "123e4567-e89b-12d3-a456-426614174000",
  "status": "completed",
  "username": "torvalds",
  "progress": 100,
  "result": {...},
  "export_files": ["torvalds_data.xlsx"],
  "created_at": "2024-02-11T10:00:00",
  "updated_at": "2024-02-11T10:05:00"
}
```

#### List All Jobs

```bash
GET /api/v1/jobs?status=completed&limit=50
```

#### Cancel Job

```bash
POST /api/v1/jobs/{job_id}/cancel
```

#### Delete Job

```bash
DELETE /api/v1/jobs/{job_id}
```

### Export Endpoints

#### Export Job Data

```bash
GET /api/v1/export/{job_id}/{format}?download=true
```

**Formats:** `excel`, `csv`, `json`

**Example:**
```bash
# Export to Excel
curl http://localhost:8000/api/v1/export/JOB_ID/excel

# Download directly
curl -O http://localhost:8000/api/v1/export/JOB_ID/excel?download=true
```

#### Download File

```bash
GET /api/v1/download/{job_id}/{filename}
```

#### List Export Files

```bash
GET /api/v1/export/{job_id}/files
```

## 🔐 Authentication

Set your GitHub token in the `.env` file or pass it as a query parameter:

```bash
# In .env
GITHUB_TOKEN=ghp_your_token_here

# Or as query parameter
?token=ghp_your_token_here
```

## 💾 Caching

The API caches responses for better performance:

- **Cache TTL**: 1 hour (configurable)
- **Max Entries**: 1000 (configurable)
- **LRU Eviction**: Automatic cleanup

Disable cache per request:
```bash
GET /api/v1/scrape/profile/octocat?use_cache=false
```

## 📊 Response Format

All endpoints return JSON with consistent structure:

**Success Response:**
```json
{
  "success": true,
  "data": {...},
  "cached": false,
  "timestamp": "2024-02-11T10:00:00"
}
```

**Error Response:**
```json
{
  "error": "Error message",
  "detail": "Detailed error information",
  "status_code": 404,
  "timestamp": "2024-02-11T10:00:00"
}
```

## 🧪 Testing

### Using cURL

```bash
# Profile
curl http://localhost:8000/api/v1/scrape/profile/octocat

# Repositories
curl "http://localhost:8000/api/v1/scrape/repositories/octocat?max_repos=5"

# Complete scrape
curl http://localhost:8000/api/v1/scrape/complete/octocat
```

### Using Python

```python
import requests

# Scrape profile
response = requests.get('http://localhost:8000/api/v1/scrape/profile/octocat')
data = response.json()
print(data)

# Start async job
job_response = requests.post(
    'http://localhost:8000/api/v1/scrape/async/torvalds',
    json={
        'username': 'torvalds',
        'max_repos': 50,
        'export_format': 'excel'
    }
)
job_id = job_response.json()['job_id']

# Check job status
status = requests.get(f'http://localhost:8000/api/v1/jobs/{job_id}')
print(status.json())
```

### Using JavaScript/Fetch

```javascript
// Scrape profile
const response = await fetch('http://localhost:8000/api/v1/scrape/profile/octocat');
const data = await response.json();
console.log(data);

// Start async job
const jobResponse = await fetch('http://localhost:8000/api/v1/scrape/async/torvalds', {
  method: 'POST',
  headers: { 'Content-Type': 'application/json' },
  body: JSON.stringify({
    username: 'torvalds',
    max_repos: 50,
    export_format: 'excel'
  })
});
const job = await jobResponse.json();
console.log(job.job_id);
```

## 📁 Project Structure

```
github-scraper-api/
├── app/
│   ├── __init__.py
│   ├── main.py              # FastAPI app & startup
│   ├── core/
│   │   ├── config.py        # Settings & configuration
│   │   ├── cache.py         # Cache manager
│   │   └── jobs.py          # Job manager
│   ├── models/
│   │   └── schemas.py       # Pydantic models
│   ├── routers/
│   │   ├── scraper.py       # Scraping endpoints
│   │   ├── jobs.py          # Job endpoints
│   │   └── export.py        # Export endpoints
│   └── services/
│       ├── scraper.py       # GitHub scraper service
│       └── exporter.py      # Export service
├── tests/                   # Test files
├── data/                    # Output directory
├── requirements.txt         # Dependencies
├── .env.example            # Environment template
├── .env                    # Environment variables (create this)
└── README.md               # This file
```

## ⚙️ Configuration

Edit `.env` file to configure:

```bash
# API Settings
DEBUG=False
HOST=0.0.0.0
PORT=8000

# GitHub Token (for higher rate limits)
GITHUB_TOKEN=your_token_here

# Cache Settings
CACHE_TTL=3600              # 1 hour
CACHE_MAX_SIZE=1000

# Job Settings
JOB_TIMEOUT=600             # 10 minutes
JOB_RETENTION_DAYS=7

# Scraping
DEFAULT_MAX_REPOS=100
REQUEST_DELAY=0.5
```

## 🚦 Rate Limits

### Without Token
- 60 requests/hour

### With Token
- 5000 requests/hour

The API automatically handles rate limits and displays warnings.

## 🔄 Background Jobs

Long-running scrapes are handled as background jobs:

1. **Create Job** - POST to `/api/v1/scrape/async/{username}`
2. **Check Status** - GET `/api/v1/jobs/{job_id}`
3. **Download Results** - GET `/api/v1/export/{job_id}/excel`

Jobs are automatically cleaned up after 7 days.

## 📝 Examples

### Example 1: Quick Profile Check

```bash
curl http://localhost:8000/api/v1/scrape/profile/octocat | jq
```

### Example 2: Async Scrape with Export

```bash
# Start job
JOB_ID=$(curl -X POST http://localhost:8000/api/v1/scrape/async/torvalds \
  -H "Content-Type: application/json" \
  -d '{"username": "torvalds", "export_format": "excel"}' \
  | jq -r '.job_id')

# Wait and check status
sleep 30
curl http://localhost:8000/api/v1/jobs/$JOB_ID | jq

# Download results
curl -O http://localhost:8000/api/v1/export/$JOB_ID/excel?download=true
```

### Example 3: Batch Scraping

```python
import requests
import time

users = ['octocat', 'torvalds', 'gvanrossum']
jobs = []

# Start all jobs
for user in users:
    response = requests.post(
        f'http://localhost:8000/api/v1/scrape/async/{user}',
        json={'username': user, 'export_format': 'json'}
    )
    jobs.append(response.json()['job_id'])

# Wait for completion
for job_id in jobs:
    while True:
        status = requests.get(f'http://localhost:8000/api/v1/jobs/{job_id}').json()
        if status['status'] in ['completed', 'failed']:
            break
        time.sleep(5)
    
    print(f"Job {job_id}: {status['status']}")
```

## 🐳 Docker Support

```dockerfile
FROM python:3.11-slim

WORKDIR /app

COPY requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt

COPY . .

CMD ["uvicorn", "app.main:app", "--host", "0.0.0.0", "--port", "8000"]
```

```bash
# Build
docker build -t github-scraper-api .

# Run
docker run -p 8000:8000 -e GITHUB_TOKEN=your_token github-scraper-api
```

## 🤝 Contributing

Contributions welcome! Please see the main project's CONTRIBUTING.md.

## 📄 License

MIT License - See LICENSE file for details.

## 🆘 Troubleshooting

### Issue: Module not found
```bash
# Make sure you're in the right directory
cd github-scraper-api
pip install -r requirements.txt
```

### Issue: Port already in use
```bash
# Use a different port
uvicorn app.main:app --port 8001
```

### Issue: Rate limit exceeded
```bash
# Add GitHub token to .env
GITHUB_TOKEN=your_token_here
```

## 📚 Additional Resources

- **FastAPI Docs**: https://fastapi.tiangolo.com
- **GitHub API**: https://docs.github.com/en/rest
- **Interactive API Docs**: http://localhost:8000/docs

---

**Built with FastAPI ⚡ | Powered by GitHub API 🚀**
