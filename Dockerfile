# NutriSénégal API - Dockerfile
FROM python:3.12-slim

# Metadata
LABEL maintainer="maodo2000diop@gmail.com"
LABEL description="NutriSénégal Food Recommendation System API"
LABEL version="1.0.0"

# Set working directory
WORKDIR /app

# Install system dependencies
RUN apt-get update && apt-get install -y \
    gcc \
    g++ \
    postgresql-client \
    && rm -rf /var/lib/apt/lists/*

# Copy requirements
COPY requirements.txt .

# Install Python dependencies
RUN pip install --no-cache-dir --upgrade pip && \
    pip install --no-cache-dir -r requirements.txt

# Download spaCy model
RUN python -m spacy download fr_core_news_md

# Copy application code
COPY api/ ./api/
COPY .env.example .env

# Create non-root user
RUN useradd -m -u 1000 nutrisenegal && \
    chown -R nutrisenegal:nutrisenegal /app
USER nutrisenegal

# Expose port
EXPOSE 8000

# Health check
HEALTHCHECK --interval=30s --timeout=10s --start-period=5s --retries=3 \
    CMD python -c "import requests; requests.get('http://localhost:8000/docs')"

# Run application
CMD ["uvicorn", "api.main:app", "--host", "0.0.0.0", "--port", "8000"]
