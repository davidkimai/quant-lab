FROM python:3.11-slim

WORKDIR /app

# Install system dependencies
RUN apt-get update && apt-get install -y \
    gcc \
    postgresql-client \
    && rm -rf /var/lib/apt/lists/*

# Copy core package
COPY packages/core /app/core

# Copy API package
COPY packages/api /app/api

# Install Python dependencies
# Install core package as editable
RUN pip install --no-cache-dir -e /app/core

# Install API package dependencies and the API package itself
RUN pip install --no-cache-dir \
    fastapi uvicorn[standard] sqlalchemy psycopg2-binary \
    pydantic pydantic-settings aiofiles requests yfinance

# Install API package as editable
RUN pip install --no-cache-dir -e /app/api

# Create data directory for CSV files
RUN mkdir -p /app/data

WORKDIR /app/api

# Expose port
EXPOSE 8000

# Health check
HEALTHCHECK --interval=30s --timeout=3s \
  CMD python -c "import requests; requests.get('http://localhost:8000/health')"

# Run application
CMD ["uvicorn", "quant_lab_api.main:app", "--host", "0.0.0.0", "--port", "8000"]
