# EpiSphere AI

**AI-Powered Global Disease Surveillance and Outbreak Intelligence Platform**

EpiSphere AI is a production-ready global public health surveillance application that continuously monitors disease cases worldwide, detects early outbreak signals using machine learning, and provides actionable intelligence for epidemiologists, countries, and the public.

## 🏗️ Architecture

- **Backend**: FastAPI (Python) with RESTful API
- **Frontend**: Next.js (React, TypeScript, TailwindCSS)
- **Databases**: PostgreSQL (primary), TimescaleDB (time-series), Redis (caching)
- **AI/ML**: Python with scikit-learn, statsmodels, Prophet, PyTorch
- **DevOps**: Docker containerization

## 🚀 Quick Start

### Prerequisites

- Docker and Docker Compose
- Node.js 18+ (for local frontend development)
- Python 3.10+ (for local backend development)

### Using Docker (Recommended)

```bash
# Start all services
docker-compose up -d

# View logs
docker-compose logs -f

# Stop services
docker-compose down
```

The application will be available at:
- Frontend: http://localhost:3000
- Backend API: http://localhost:8000
- API Docs: http://localhost:8000/docs

### Manual Setup

#### Backend

```bash
cd backend
python -m venv venv
source venv/bin/activate  # On Windows: venv\Scripts\activate
pip install -r requirements.txt

# Set up environment variables
cp .env.example .env
# Edit .env with your database credentials

# Run migrations
alembic upgrade head

# Start server
uvicorn app.main:app --reload --host 0.0.0.0 --port 8000
```

#### Frontend

```bash
cd frontend
npm install
npm run dev
```

## 📁 Project Structure

```
EpiSphere/
├── backend/                 # FastAPI backend
│   ├── app/
│   │   ├── api/            # API routes
│   │   ├── core/           # Core config, security, dependencies
│   │   ├── db/             # Database models and session
│   │   ├── ml/             # ML pipelines and models
│   │   ├── schemas/        # Pydantic schemas
│   │   └── services/       # Business logic
│   ├── alembic/            # Database migrations
│   └── requirements.txt
├── frontend/               # Next.js frontend
│   ├── app/                # Next.js app directory
│   ├── components/         # React components
│   ├── lib/                # Utilities and API clients
│   └── public/             # Static assets
├── docker-compose.yml      # Docker orchestration
└── README.md
```

## 👥 User Roles

- **Public User**: View aggregated global and country-level data
- **Country Data Officer**: Upload case data, view country dashboards
- **Epidemiologist**: Advanced analytics, forecasting, stratified views
- **Admin**: Manage users, diseases, permissions, alerts

## 🔑 Features

### 1. Global Surveillance Dashboard
- World map with daily/cumulative cases
- Incidence per 100,000
- Filters by disease, date range, region

### 2. Country-Level Dashboard
- Time-series visualizations
- 7-day moving averages
- Subnational maps
- CFR, incidence, growth rate metrics

### 3. AI Outbreak Detection
- Multiple detection algorithms:
  - Baseline statistical thresholds
  - Seasonal anomaly detection
  - Isolation Forest
  - CUSUM change detection
  - LSTM residual anomalies
- Automated alerts with severity levels

### 4. Forecasting Engine
- Short-term forecasts (7-30 days)
- Models: ARIMA, Prophet, LSTM
- Automatic model selection
- Confidence intervals

### 5. Alerts System
- Central alert dashboard
- Alert lifecycle management
- Email notifications (architecture ready)

### 6. Data Upload & Integration
- CSV/Excel upload with column mapping
- API ingestion endpoints
- Data validation and quality checks

### 7. Reporting Module
- Weekly/Monthly epidemiological bulletins
- Auto-generated summaries
- Export to PDF, DOCX, CSV

### 8. Monitoring & Evaluation
- Reporting completeness tracking
- Timeliness metrics
- Data quality indicators
- Performance visualizations

## 🔐 Security

- JWT authentication
- Role-based access control (RBAC)
- Data encryption at rest
- Audit logs for data access
- Rate limiting

## 📊 API Documentation

Once the backend is running, visit:
- Swagger UI: http://localhost:8000/docs
- ReDoc: http://localhost:8000/redoc

## 🤝 Contributing

This is a production system designed for real-world use by Ministries of Health and epidemiologists. Code quality, correctness, and security are paramount.

## 🚀 Getting Started

See [SETUP.md](./SETUP.md) for detailed setup instructions.

### Quick Start

```bash
# Start all services
docker-compose up -d

# Initialize database
docker-compose exec backend python scripts/init_db.py

# Access the application
# Frontend: http://localhost:3000
# Backend API: http://localhost:8000/docs
```

## 📝 License

[Specify your license]

## 🆘 Support

For issues and questions, please refer to the documentation or contact the development team.

## 🏗️ Architecture Details

### Backend Structure

```
backend/
├── app/
│   ├── api/v1/endpoints/    # API route handlers
│   ├── core/                # Configuration, security, database
│   ├── db/                 # Database models
│   ├── ml/                 # ML pipelines (outbreak detection, forecasting)
│   ├── schemas/            # Pydantic schemas for validation
│   └── services/           # Business logic services
├── alembic/                # Database migrations
└── scripts/                # Utility scripts
```

### Frontend Structure

```
frontend/
├── app/                    # Next.js app directory (pages)
├── components/             # React components
├── lib/                    # Utilities and API clients
└── public/                 # Static assets
```

### Key Technologies

- **Backend**: FastAPI, SQLAlchemy, Alembic, Pydantic
- **Frontend**: Next.js 14, React, TypeScript, TailwindCSS
- **ML/AI**: scikit-learn, statsmodels, Prophet, PyTorch
- **Databases**: PostgreSQL, TimescaleDB, Redis
- **Visualization**: Apache ECharts, Leaflet (maps)

## 🔧 Development

### Running Tests

```bash
# Backend tests (when implemented)
cd backend
pytest

# Frontend tests (when implemented)
cd frontend
npm test
```

### Code Quality

- Backend: Follow PEP 8, use type hints
- Frontend: Follow ESLint rules, use TypeScript strictly
- Both: Write docstrings and comments for complex logic
