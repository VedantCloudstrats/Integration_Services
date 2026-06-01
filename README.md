# Integration Services

Stateless FastAPI service for CMMS integration routing and Pydantic validation.

## Run Locally

```powershell
cd C:\Users\vedantrbhosale\Desktop\backend_Integration_Services
.\venv\Scripts\Activate.ps1
python -m uvicorn app.main:app --host 127.0.0.1 --port 8001 --reload
```

## API Versioning

All API endpoints are versioned and exposed under:

```text
/api/v1/cmms/...
```

For backward compatibility, the legacy endpoints under `/api/cmms/...` are also supported but deprecated.

## Authentication & Documentation

All application endpoints require API Key verification. 

- **Header Name**: `X-API-Key`
- **Default Key**: `dev-secret-key` (Configure with `API_KEY` in `.env`)

The interactive API documentation is accessible at:
- **Swagger UI**: `/docs`
- **ReDoc**: `/redoc`

The `/docs` page is publicly accessible and features an **Authorize** button. You can click it, enter your API key (e.g. `dev-secret-key`), and test all the endpoints directly from the browser.

## Development

```powershell
python -m black app tests run.py
python -m pytest
```

