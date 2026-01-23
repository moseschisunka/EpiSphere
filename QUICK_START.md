# Quick Start Guide - Localhost

## Option 1: Using Docker (Recommended if Docker is installed)

```bash
# Start all services
docker-compose up -d

# Initialize database
docker-compose exec backend python scripts/init_db.py

# View logs
docker-compose logs -f

# Stop services
docker-compose down
```

## Option 2: Manual Setup (No Docker)

### Prerequisites
- Python 3.10+ installed
- Node.js 18+ installed
- PostgreSQL installed and running (or use SQLite for testing)

### Step 1: Start Backend

**Windows:**
```cmd
start_backend.bat
```

**Linux/Mac:**
```bash
cd backend
python3 -m venv venv
source venv/bin/activate
pip install -r requirements.txt
python scripts/init_db.py
uvicorn app.main:app --reload --host 0.0.0.0 --port 8000
```

The backend will be available at: http://localhost:8000
API docs: http://localhost:8000/docs

### Step 2: Start Frontend (in a new terminal)

**Windows:**
```cmd
start_frontend.bat
```

**Linux/Mac:**
```bash
cd frontend
npm install
npm run dev
```

The frontend will be available at: http://localhost:3000

### Step 3: Access the Application

- **Frontend**: http://localhost:3000
- **Backend API**: http://localhost:8000
- **API Documentation**: http://localhost:8000/docs

### Creating a Test User

After starting the backend, create a user via the API:

```bash
curl -X POST "http://localhost:8000/api/v1/auth/register" ^
  -H "Content-Type: application/json" ^
  -d "{\"email\":\"admin@episphere.ai\",\"username\":\"admin\",\"password\":\"admin123\",\"full_name\":\"Admin User\",\"role_id\":4}"
```

Or use the Swagger UI at http://localhost:8000/docs

### Troubleshooting

**Backend won't start:**
- Check if port 8000 is available
- Ensure PostgreSQL is running (or modify DATABASE_URL in backend/.env)
- Check Python version: `python --version` (needs 3.10+)

**Frontend won't start:**
- Check if port 3000 is available
- Ensure Node.js is installed: `node --version` (needs 18+)
- Delete `node_modules` and run `npm install` again

**Database connection errors:**
- Create a `.env` file in the `backend` directory
- Set `DATABASE_URL` to your PostgreSQL connection string
- Or use SQLite for testing: `DATABASE_URL=sqlite:///./episphere.db`
