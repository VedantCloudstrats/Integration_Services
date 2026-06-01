# ==========================================
# Dockerfile for SWMM FastAPI Integration App
# Base Image: Python 3.12 Slim (Lightweight, Debian-based)
# ==========================================
FROM python:3.12-slim

# Set environment variables
# Prevents Python from writing pyc files to disc
ENV PYTHONDONTWRITEBYTECODE=1
# Prevents Python from buffering stdout/stderr
ENV PYTHONUNBUFFERED=1

# Set working directory inside container
WORKDIR /app

# Install basic system build dependencies for database interfaces
RUN apt-get update && apt-get install -y --no-install-recommends \
    build-essential \
    libpq-dev \
    && rm -rf /var/lib/apt/lists/*

# Copy requirements from the local fast_api directory
COPY fast_api/requirements.txt /app/requirements.txt

# Install python dependencies without saving pip cache
RUN pip install --no-cache-dir -r /app/requirements.txt

# Copy the entire workspace into /app.
# This is required because FastAPI directly references and setup Django settings/models 
# (e.g. dart.models, ILMS.models, srar.models, SWMM.settings, etc.)
COPY . /app/

# Expose port 8001 for external applications
EXPOSE 8001

# Set startup command to launch uvicorn
CMD ["uvicorn", "fast_api.main:app", "--host", "0.0.0.0", "--port", "8001"]
