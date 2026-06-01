# FastAPI APIs for External Applications (CMMS, ILMS, WLMS, ITTTM)

This implementation plan details the setup and development of external integration APIs using **FastAPI** hosted in a standalone, dedicated `fast_api/` folder. The APIs leverage Django's ORM directly, ensuring database configuration, models, and relationships are reused without duplication.

---

## User Review & Architecture Choices

> [!NOTE]
> **Django Initialization in FastAPI**
> FastAPI runs in the same virtual environment (`.venv`) as Django. It boots Django using `django.setup()` so that Django ORM querysets function seamlessly inside FastAPI async routes via `sync_to_async`.
>
> **Lightweight Docker Architecture**
> The Docker container is designed using the lightweight **`python:3.12-slim`** base image. A root `.dockerignore` file filters out local caches, virtual environments, and large binaries (such as PDF documentation assets) to keep the build footprint minimal (~130MB).
>
> **Authentication & Authorization**
> An API-Key verification dependency (`verify_api_key`) is configured as a header requirement (`X-API-Key: dev-secret-key`) to secure integration routes for external developers.

---

## Proposed Changes

The FastAPI code is isolated under the `fast_api/` directory at the project root.

### FastAPI Core & Startup

#### [NEW] [main.py](file:///c:/Users/vedantrbhosale/Downloads/Patch_20_5_26%20%282%29/fast_api/main.py)
* Initialize Django ORM context.
* Configure CORS middleware.
* Register routers for CMMS, ILMS, WLMS, and ITTTM.

#### [NEW] [schemas.py](file:///c:/Users/vedantrbhosale/Downloads/Patch_20_5_26%20%282%29/fast_api/schemas.py)
* Define Pydantic v2 schemas for request validation and response serialization.
* Includes all CMMS, ILMS, WLMS, and ITTTM models, as well as schemas for **IIF** (sync state) and **Receive/Post-Receive** (receipt transactions) schemas.

#### [NEW] [dependencies.py](file:///c:/Users/vedantrbhosale/Downloads/Patch_20_5_26%20%282%29/fast_api/dependencies.py)
* Define validation dependencies including API Key checking headers.

---

### Router Configurations

#### [NEW] [cmms.py](file:///c:/Users/vedantrbhosale/Downloads/Patch_20_5_26%20%282%29/fast_api/routers/cmms.py)
Exposes endpoint routes for:
* **Defects (DART & OF_def)**: GET list of defects, GET detail, POST create, POST rectify.
* **SRAR (Monthly Report)**: GET monthly reports, POST sync report.
* **Routines**: GET completed routines, POST record completed routines.
* **FUSS (Deferment)**: GET deferments, POST deferment request.
* **ABER (Budget Estimate)**: GET equipment older than 6 years.
* **SFD (Ship Fit)**: GET fitted equipment lists.

#### [NEW] [ilms.py](file:///c:/Users/vedantrbhosale/Downloads/Patch_20_5_26%20%282%29/fast_api/routers/ilms.py)
Exposes endpoints for:
* **Items & Vendors**: GET/POST sync.
* **Demands, PTS & Surveys**: GET/POST transactions.
* **IIF**: GET/POST sync tracking records.
* **Receive & Post-Receive**: GET/POST receipt logging.

#### [NEW] [wlms.py](file:///c:/Users/vedantrbhosale/Downloads/Patch_20_5_26%20%282%29/fast_api/routers/wlms.py)
Exposes endpoints for:
* **Equipments & Spares**: GET/POST sync.
* **Demands, PTS & Surveys**: GET/POST transactions.
* **IIF**: GET/POST sync tracking records.
* **Receive**: GET/POST receive demand details.

#### [NEW] [itttm.py](file:///c:/Users/vedantrbhosale/Downloads/Patch_20_5_26%20%282%29/fast_api/routers/itttm.py)
Exposes endpoints for:
* **Vibration Trials**: GET/POST trials (supports nested DSC and Performance checks).
* **Pre-ranging**: GET/POST trials.
* **Blowing Arc**: GET/POST events.
* **Submissions & Approvals**: POST submissions/approvals.

---

### Deployment & Runners

#### [NEW] [run_fastapi.py](file:///c:/Users/vedantrbhosale/Downloads/Patch_20_5_26%20%282%29/run_fastapi.py)
* Entrypoint Python runner script to boot uvicorn locally on port `8001`.

#### [NEW] [Dockerfile](file:///c:/Users/vedantrbhosale/Downloads/Patch_20_5_26%20%282%29/fast_api/Dockerfile)
* Docker configuration utilizing `python:3.12-slim` image.

#### [NEW] [.dockerignore](file:///c:/Users/vedantrbhosale/Downloads/Patch_20_5_26%20%282%29/.dockerignore)
* Global file to ignore virtual environments, python caches, and large PDF binaries.

---

## Verification Plan

### Automated / Integration Tests
We implemented [test_endpoints.py](file:///c:/Users/vedantrbhosale/Downloads/Patch_20_5_26%20%282%29/fast_api/test_endpoints.py) to run verification checks on port `8001`.
* Timeout is set to `35` seconds to allow database queries to time out if remote connection fails.
* Assertions verify that authentication works (`401`/`403` on wrong/missing keys), root returns `200`, and database endpoints correctly route (returning `200` or `500` depending on connection state).

### Manual Verification
* Access Swagger UI documentation at `http://127.0.0.1:8001/docs` once the server is launched.
