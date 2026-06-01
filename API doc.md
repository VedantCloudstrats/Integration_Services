# SWMM CMMS Integration APIs

## Overview

This service is a stateless FastAPI application for CMMS integration request
routing and Pydantic request/response validation.

The application does not connect to a database and does not persist payloads.
Read endpoints return empty response-shaped payloads. Write endpoints validate
incoming request bodies and return acknowledgement or derived identifier
responses.

## Application

- Entry point: `app.main:app`
- Local command: `python -m uvicorn app.main:app --host 127.0.0.1 --port 8001 --reload`
- API docs: `/docs`
- Health endpoint: `/health`

## Authentication

All application path operations require an API key header:

```http
X-API-Key: dev-secret-key
```

Missing keys return `401 Unauthorized`. Invalid keys return `403 Forbidden`.
The key is configured through `API_KEY` in `.env`.

## API Prefix

All CMMS routes are mounted under:

```text
/api/cmms
```

## Modules

- DART defect validation
- SRAR report validation
- FUSS deferment validation
- ABER estimate validation
- SFD sync payload shape validation
- Refit event validation
- OPDEF event validation
- MAINTOP sync validation

## Version Control

The project is tracked in Git and pushed to:

```text
https://github.com/VedantCloudstrats/Integration_Services.git
```

Local environment files and virtual environments are ignored. Use
`.env.example` as the template for local configuration.
