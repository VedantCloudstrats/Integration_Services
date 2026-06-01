# Integration Services

Stateless FastAPI service for CMMS integration routing and Pydantic validation.

## Run Locally

```powershell
cd C:\Users\vedantrbhosale\Desktop\backend_Integration_Services
.\venv\Scripts\Activate.ps1
python -m uvicorn app.main:app --host 127.0.0.1 --port 8001 --reload
```

## Authentication

All application endpoints require:

```http
X-API-Key: dev-secret-key
```

Configure the key with `API_KEY` in `.env`. Use `.env.example` as the template.

## Development

```powershell
python -m black app tests run.py
python -m pytest
```
