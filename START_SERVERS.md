# Starting EpiSphere AI Servers

## Quick Start Commands

### Option 1: Start Both Servers (Recommended)

Open **two separate terminal windows**:

**Terminal 1 - Backend:**
```powershell
cd C:\Users\PC\Desktop\EpiSphere\backend
.\venv\Scripts\Activate.ps1
uvicorn app.main:app --reload --host 127.0.0.1 --port 8000
```

**Terminal 2 - Frontend:**
```powershell
cd C:\Users\PC\Desktop\EpiSphere\frontend
npm run dev
```

### Option 2: Use Batch Files

**Backend:**
```cmd
start_backend.bat
```

**Frontend:**
```cmd
start_frontend.bat
```

## Access the Application

- **Frontend**: http://localhost:3000 or http://127.0.0.1:3000
- **Backend API**: http://localhost:8000 or http://127.0.0.1:8000
- **API Docs**: http://localhost:8000/docs

## Troubleshooting

### If you get "Connection Refused":

1. **Check if servers are running:**
   ```powershell
   netstat -ano | findstr ":8000"
   netstat -ano | findstr ":3000"
   ```

2. **Try different URLs:**
   - http://127.0.0.1:3000 (instead of localhost)
   - http://127.0.0.1:8000 (instead of localhost)

3. **Check for port conflicts:**
   - Port 8000: Backend
   - Port 3000: Frontend
   - If ports are in use, kill the processes or change ports

4. **Restart servers:**
   - Stop both servers (Ctrl+C)
   - Start backend first, wait 5 seconds
   - Then start frontend

### Common Issues

- **Font error in frontend**: Fixed - font configuration updated
- **Database errors**: Make sure you ran `python scripts\init_db.py`
- **Module not found**: Activate virtual environment first

## Verify Servers are Running

**Backend Health Check:**
```powershell
Invoke-WebRequest -Uri http://127.0.0.1:8000/health
```

**Frontend Check:**
```powershell
Invoke-WebRequest -Uri http://127.0.0.1:3000
```
