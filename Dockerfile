# VoxShield AI — production image for Koyeb/any Docker host.
# No PyTorch: the signal-analysis baseline is the shipped detector and torch
# would blow the 512 MB free-tier memory ceiling.
FROM python:3.13-slim-bookworm

ENV PYTHONDONTWRITEBYTECODE=1 \
    PYTHONUNBUFFERED=1 \
    PIP_NO_CACHE_DIR=1

WORKDIR /app

# Install dependencies first for layer caching
COPY backend/requirements.txt backend/requirements-deploy.txt /app/backend/
RUN pip install -r /app/backend/requirements-deploy.txt

# Application code + assets (backend/, ml/, static/, data/)
COPY . /app

# The app writes its SQLite database next to the backend package
RUN mkdir -p /app/backend

EXPOSE 8000
WORKDIR /app/backend

# Koyeb injects PORT for web services; default to 8000 for local runs
CMD ["sh", "-c", "uvicorn app.main:app --host 0.0.0.0 --port ${PORT:-8000}"]
