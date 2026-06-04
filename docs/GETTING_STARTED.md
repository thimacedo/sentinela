# Getting Started Guide — Sentinela Democrática

**Purpose**: Quick start guide for new developers  
**Time to Setup**: ~30 minutes  
**Prerequisites**: Git, Node.js 20+, Python 3.11+, Docker (optional)

---

## 🎯 Quick Start (5 minutes)

### 1. Clone Repository

```bash
git clone https://github.com/abacusai/sentinela.git
cd sentinela
```

### 2. Copy Environment Files

```bash
# Backend
cp .env.example .env
# Edit .env with your configuration

# Frontend  
cd frontend
cp .env.local.example .env.local
cd ..
```

### 3. Install Dependencies

```bash
# Backend
pip install -r requirements.txt

# Frontend
cd frontend
npm install
cd ..
```

### 4. Start Development Servers

```bash
# Terminal 1: Backend API
python -m uvicorn api.index:app --reload --port 8000

# Terminal 2: Frontend
cd frontend
npm run dev
# http://localhost:3000
```

✅ **Done! Visit http://localhost:3000**

---

## 📦 Project Structure

```
sentinela/
├── api/                    # Backend API (FastAPI/Python)
│   ├── index.py           # Main API app
│   ├── v1/                # API v1 endpoints
│   ├── config/            # Configuration modules
│   ├── middleware/        # Auth, CORS middleware
│   ├── services/          # Business logic
│   └── common.py          # Shared utilities
├── core/                   # Core services
│   ├── queue_manager.py   # Distributed queue
│   ├── fallback_llm.py    # AI provider fallback
│   └── ai_service.py      # AI integration
├── processing/             # Workers
│   ├── network_miner/     # Social network analysis
│   ├── treasurer/         # Financial tracking
│   ├── target_research/   # Research automation
│   ├── dossier/          # Report generation
│   └── alert/            # Alert system
├── frontend/               # Next.js Frontend
│   ├── app/              # Pages/routes
│   ├── components/       # React components
│   ├── hooks/            # Custom hooks
│   ├── lib/              # Utilities
│   └── public/           # Static assets
├── docs/                  # Documentation
│   ├── core/             # Core service docs
│   ├── frontend/         # Frontend docs
│   ├── ENDPOINTS.md      # API endpoints
│   ├── DEPLOYMENT.md     # Deployment guide
│   └── MONITORING.md     # Monitoring guide
└── scripts/              # Utility scripts
    ├── db/              # Database management
    ├── workers/         # Worker management
    └── tools/           # Development tools
```

---

## 🔧 Backend Setup

### Install Python Dependencies

```bash
# Create virtual environment
python3.11 -m venv venv
source venv/bin/activate  # On Windows: venv\Scripts\activate

# Install dependencies
pip install -r requirements.txt

# Install additional tools
pip install pytest pytest-cov black pylint
```

### Configure Environment

```env
# .env file
ENVIRONMENT=development
DEBUG=true

# Database
DATABASE_URL=postgresql://postgres:password@localhost:5432/sentinela
SUPABASE_URL=https://your-instance.supabase.co
SUPABASE_KEY=your-key

# JWT / Security
JWT_SECRET_KEY=dev-secret-key-change-in-production
CORS_ORIGINS=http://localhost:3000,http://localhost:5173

# API Keys (optional for dev)
OPENAI_API_KEY=sk-...
GROQ_API_KEY=gsk_...
```

### Run Migrations

```bash
# Create database
createdb sentinela

# Run migrations
alembic upgrade head

# Check migrations
alembic current
```

### Start Backend

```bash
# Development with reload
python -m uvicorn api.index:app --reload --port 8000

# With workers
python -m uvicorn api.index:app --port 8000 &
python processing/workers_launcher.py

# View API docs
# http://localhost:8000/docs (Swagger)
# http://localhost:8000/redoc (ReDoc)
```

---

## 🎨 Frontend Setup

### Install Dependencies

```bash
cd frontend
npm install
```

### Configure Environment

```env
# frontend/.env.local
NEXT_PUBLIC_API_URL=http://localhost:8000
NEXT_PUBLIC_SUPABASE_URL=https://your-instance.supabase.co
NEXT_PUBLIC_SUPABASE_ANON_KEY=your-anon-key
```

### Start Development Server

```bash
npm run dev
# http://localhost:3000

# Lint code
npm run lint

# Build for production
npm run build
npm start
```

---

## 🗄️ Database Setup

### Using Docker Compose

```bash
# Start PostgreSQL and Redis
docker-compose up -d postgres redis

# Check logs
docker-compose logs postgres

# Connect to database
psql postgresql://postgres:password@localhost:5432/sentinela
```

### Local PostgreSQL

```bash
# Mac
brew install postgresql
brew services start postgresql

# Linux
sudo apt-get install postgresql
sudo service postgresql start

# Create database
createdb sentinela

# Create user
psql -c "CREATE USER sentinela_user WITH PASSWORD 'password';"
psql -c "GRANT ALL PRIVILEGES ON DATABASE sentinela TO sentinela_user;"
```

---

## 🧪 Testing

### Backend Tests

```bash
# Run all tests
pytest

# Run with coverage
pytest --cov=api --cov-report=html

# Run specific test
pytest tests/test_api.py::test_login

# Watch mode
pytest-watch tests/
```

### Frontend Tests

```bash
cd frontend

# Run tests
npm test

# Watch mode
npm test -- --watch

# Coverage
npm test -- --coverage
```

---

## 🔐 Authentication

### Login to Application

```
Email: test@example.com
Password: test123456
```

### Generate Test Token (Backend)

```python
from api.services.jwt_service import generate_token_pair

tokens = generate_token_pair(user_id="test-user-123")
print(tokens["access_token"])
```

### Use Token in API

```bash
# Set token in environment
export TOKEN="<your-token>"

# Make authenticated request
curl -H "Authorization: Bearer $TOKEN" http://localhost:8000/api/v1/targets
```

---

## 🚀 Common Tasks

### Create New API Endpoint

```python
# api/v1/example.py
from fastapi import APIRouter, Depends
from api.middleware import verify_user_token

router = APIRouter(prefix="/api/v1", tags=["example"])

@router.get("/example")
async def get_example(user_id: str = Depends(verify_user_token)):
    """Get example data"""
    return {"message": "Hello, World!"}

# Add to api/index.py
from api.v1.example import router as example_router
app.include_router(example_router)
```

### Create New Frontend Component

```typescript
// frontend/components/Example.tsx
import { Button } from '@/components/ui/button'
import { Card } from '@/components/ui/card'

interface ExampleProps {
  title: string
  onClick: () => void
}

export function Example({ title, onClick }: ExampleProps) {
  return (
    <Card>
      <h2>{title}</h2>
      <Button onClick={onClick}>Click me</Button>
    </Card>
  )
}

// Use in page
import { Example } from '@/components/Example'

export default function ExamplePage() {
  return <Example title="Test" onClick={() => alert('Clicked!')} />
}
```

### Add Database Migration

```bash
# Create migration file
alembic revision --autogenerate -m "Add new column"

# Review generated migration in alembic/versions/

# Apply migration
alembic upgrade head

# Rollback if needed
alembic downgrade -1
```

### Run Background Worker

```bash
# Start specific worker
python processing/workers/network_miner.py

# Start all workers
python processing/workers_launcher.py

# Check worker status
ps aux | grep worker
```

---

## 🐛 Debugging

### Backend Debugging

```python
# Add print statements
print(f"DEBUG: value = {value}")

# Use debugger
import pdb
pdb.set_trace()

# Use logging
import logging
logger = logging.getLogger(__name__)
logger.info(f"User ID: {user_id}")
```

### Frontend Debugging

```typescript
// Console logging
console.log('Debug:', variable)

// React DevTools
// Install React DevTools browser extension

// VS Code Debugger
// Add .vscode/launch.json and set breakpoints
```

### Check Application State

```bash
# Backend: Check API health
curl http://localhost:8000/api/health

# Backend: Check database
psql postgresql://user:pass@localhost:5432/sentinela

# Frontend: Check console
# Open browser DevTools (F12) → Console tab

# Backend: Check logs
tail -f logs/app.log
```

---

## 📚 Key Documentation

- **API Endpoints**: See [ENDPOINTS.md](docs/ENDPOINTS.md)
- **Frontend Architecture**: See [docs/frontend/ARCHITECTURE.md](docs/frontend/ARCHITECTURE.md)
- **Database Schema**: See [DATABASE_SCHEMA.md](docs/DATABASE_SCHEMA.md)
- **Deployment**: See [DEPLOYMENT.md](docs/DEPLOYMENT.md)
- **Security**: See [SECURITY_REMEDIATION_PLAN.md](docs/SECURITY_REMEDIATION_PLAN.md)

---

## 🆘 Troubleshooting

### Backend Won't Start

```bash
# Check port in use
lsof -i :8000  # Mac/Linux
netstat -ano | findstr :8000  # Windows

# Check database connection
python -c "from api.common import get_supa; print(get_supa())"

# Check dependencies
pip list | grep -i fastapi

# Reinstall dependencies
pip install -r requirements.txt --force-reinstall
```

### Frontend Won't Load

```bash
# Clear cache
rm -rf frontend/.next frontend/node_modules
npm install

# Check Node version
node --version  # Should be 20+

# Check API URL
echo $NEXT_PUBLIC_API_URL

# Check console for errors
# Browser DevTools → Console tab
```

### Database Connection Refused

```bash
# Check if database is running
psql --version

# Start PostgreSQL
# Mac: brew services start postgresql
# Linux: sudo service postgresql start

# Check connection string
echo $DATABASE_URL

# Test connection
psql $DATABASE_URL -c "SELECT 1"
```

### API Returns 401 Unauthorized

```bash
# Token might be expired
# Generate new token:
curl -X POST http://localhost:8000/api/v1/auth/login \
  -H "Content-Type: application/json" \
  -d '{"email":"test@example.com","password":"test123456"}'

# Use new token in subsequent requests
curl -H "Authorization: Bearer <token>" http://localhost:8000/api/v1/targets
```

---

## 💡 Tips & Tricks

### Use Environment Variables

```bash
# Create .env file
echo "DATABASE_URL=postgresql://..." > .env

# Load in Python
from dotenv import load_dotenv
import os
load_dotenv()
url = os.getenv("DATABASE_URL")
```

### Format Code

```bash
# Python
black api/
pylint api/

# JavaScript
npm run lint -- --fix
```

### Watch for Changes

```bash
# Python: Use --reload
python -m uvicorn api.index:app --reload

# JavaScript: Automatic with npm run dev

# Database migrations: Use alembic
alembic upgrade head
```

### Access Database Directly

```bash
# psql prompt
psql -d sentinela

# List tables
\dt

# View specific table
SELECT * FROM targets LIMIT 10;

# Exit
\q
```

---

## 📞 Getting Help

### Documentation
1. Check [README.md](README.md) in root
2. Browse [docs/](docs/) folder
3. Check code comments and docstrings
4. Review existing tests for usage examples

### Community
- **Issues**: GitHub Issues for bugs/features
- **Discussions**: GitHub Discussions for questions
- **Email**: contact@sentinela.com

### Code Examples
- Backend: See `api/v1/*.py` for endpoint examples
- Frontend: See `frontend/components/` for component examples
- Tests: See `tests/` for testing patterns
- Workers: See `processing/workers/` for worker examples

---

## ✅ What's Next?

After setup, explore these areas:

1. **API Development**
   - Add new endpoints (see ENDPOINTS.md)
   - Implement business logic (see core services docs)

2. **Frontend Development**
   - Create new components (see COMPONENTS.md)
   - Integrate with API (see API_INTEGRATION.md)

3. **Database**
   - Create migrations (see DATABASE_SCHEMA.md)
   - Query optimization

4. **Deployment**
   - Docker setup (see DEPLOYMENT.md)
   - Production configuration

5. **Monitoring**
   - Set up logging (see MONITORING.md)
   - Configure alerts

---

## 🔗 Quick Links

| Resource | Location |
|----------|----------|
| API Docs | http://localhost:8000/docs |
| Frontend | http://localhost:3000 |
| Swagger | http://localhost:8000/redoc |
| Database | postgresql://localhost:5432/sentinela |
| API Endpoints | [docs/ENDPOINTS.md](docs/ENDPOINTS.md) |
| Architecture | [docs/frontend/ARCHITECTURE.md](docs/frontend/ARCHITECTURE.md) |
| Deployment | [docs/DEPLOYMENT.md](docs/DEPLOYMENT.md) |

---

## 🎓 Learning Resources

- **FastAPI**: https://fastapi.tiangolo.com
- **Next.js**: https://nextjs.org
- **React**: https://react.dev
- **PostgreSQL**: https://postgresql.org
- **Python**: https://python.org

Happy Coding! 🚀
