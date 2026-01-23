# EpiSphere AI - Setup Guide

## Prerequisites

- Docker and Docker Compose installed
- Node.js 18+ (for local frontend development)
- Python 3.10+ (for local backend development)

## Quick Start with Docker

1. **Clone the repository** (if applicable)

2. **Start all services:**
   ```bash
   docker-compose up -d
   ```

3. **Initialize the database:**
   ```bash
   docker-compose exec backend python scripts/init_db.py
   ```

4. **Access the application:**
   - Frontend: http://localhost:3000
   - Backend API: http://localhost:8000
   - API Documentation: http://localhost:8000/docs

## Manual Setup

### Backend Setup

1. **Navigate to backend directory:**
   ```bash
   cd backend
   ```

2. **Create virtual environment:**
   ```bash
   python -m venv venv
   source venv/bin/activate  # On Windows: venv\Scripts\activate
   ```

3. **Install dependencies:**
   ```bash
   pip install -r requirements.txt
   ```

4. **Set up environment variables:**
   ```bash
   cp .env.example .env
   # Edit .env with your database credentials
   ```

5. **Initialize database:**
   ```bash
   python scripts/init_db.py
   ```

6. **Run migrations (if using Alembic):**
   ```bash
   alembic upgrade head
   ```

7. **Start the server:**
   ```bash
   uvicorn app.main:app --reload --host 0.0.0.0 --port 8000
   ```

### Frontend Setup

1. **Navigate to frontend directory:**
   ```bash
   cd frontend
   ```

2. **Install dependencies:**
   ```bash
   npm install
   ```

3. **Set up environment variables:**
   Create a `.env.local` file:
   ```
   NEXT_PUBLIC_API_URL=http://localhost:8000
   ```

4. **Start development server:**
   ```bash
   npm run dev
   ```

## Database Setup

### PostgreSQL with TimescaleDB

The application uses PostgreSQL with TimescaleDB extension for time-series optimization.

1. **Start PostgreSQL:**
   ```bash
   docker-compose up -d postgres
   ```

2. **Connect to database and enable TimescaleDB:**
   ```bash
   docker-compose exec postgres psql -U episphere -d episphere_db
   ```
   
   Then in psql:
   ```sql
   CREATE EXTENSION IF NOT EXISTS timescaledb;
   SELECT create_hypertable('cases', 'date', if_not_exists => TRUE);
   ```

### Initial Data

Run the initialization script to create:
- User roles (public, country_data_officer, epidemiologist, admin)
- Sample countries
- WHO regions
- Common diseases

```bash
python scripts/init_db.py
```

## Creating a Test User

After initialization, you can create a test user via the API:

```bash
curl -X POST "http://localhost:8000/api/v1/auth/register" \
  -H "Content-Type: application/json" \
  -d '{
    "email": "admin@episphere.ai",
    "username": "admin",
    "password": "admin123",
    "full_name": "Admin User",
    "role_id": 4
  }'
```

Roles:
- 1: public
- 2: country_data_officer
- 3: epidemiologist
- 4: admin

## Development

### Backend Development

- API documentation: http://localhost:8000/docs (Swagger UI)
- Alternative docs: http://localhost:8000/redoc (ReDoc)

### Frontend Development

- Development server: http://localhost:3000
- Hot reload enabled by default

## Production Deployment

1. **Update environment variables:**
   - Set `DEBUG=False`
   - Set strong `SECRET_KEY`
   - Configure production database URLs
   - Set proper CORS origins

2. **Build frontend:**
   ```bash
   cd frontend
   npm run build
   ```

3. **Run migrations:**
   ```bash
   cd backend
   alembic upgrade head
   ```

4. **Start services:**
   ```bash
   docker-compose up -d
   ```

## Troubleshooting

### Database Connection Issues

- Ensure PostgreSQL is running
- Check DATABASE_URL in .env
- Verify database credentials

### Port Conflicts

- Change ports in docker-compose.yml if needed
- Backend default: 8000
- Frontend default: 3000
- PostgreSQL default: 5432
- Redis default: 6379

### ML Model Issues

- Ensure all ML dependencies are installed
- Prophet requires additional system dependencies on some platforms
- PyTorch may require CUDA setup for GPU support

## Next Steps

1. Upload sample case data via the upload page
2. Explore the global dashboard
3. Test outbreak detection by uploading data with anomalies
4. Generate forecasts for countries with sufficient data
5. Review alerts in the alerts center
