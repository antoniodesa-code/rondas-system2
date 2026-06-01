```powershell
docker compose up -d

Start-Sleep -Seconds 5

Start-Process powershell -ArgumentList "-NoExit", "-Command", "cd C:\rondas\ronda-system\backend; if (-not (Test-Path '.venv')) { python -m venv .venv }; .\.venv\Scripts\Activate.ps1; pip install -r requirements.txt; python seed.py; uvicorn app.main:app --reload --port 8000"

Start-Process powershell -ArgumentList "-NoExit", "-Command", "cd C:\rondas\ronda-system\frontend; npm run dev"
```
