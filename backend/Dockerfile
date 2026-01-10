FROM python:3.11-slim

WORKDIR /app

# Install system dependencies
RUN apt-get update && apt-get install -y \
    gcc \
    g++ \
    && rm -rf /var/lib/apt/lists/*

# Copy requirements
COPY requirements.txt .

# Install CPU-only PyTorch first (reduces image size by ~3GB)
RUN pip install --no-cache-dir torch --index-url https://download.pytorch.org/whl/cpu

# Install Python dependencies
RUN pip install --no-cache-dir -r requirements.txt

# Download spaCy model (optional - will download on first use if not present)
# RUN python -m spacy download en_core_web_sm

# Copy application code
COPY app/ ./app/
COPY config/ ./config/
COPY data ./data/
COPY migrations/ ./migrations/

# Create data directories
RUN mkdir -p /app/data/raw /app/data/processed /app/data/chroma_db

# Expose port
EXPOSE 8000

# Run application
CMD ["uvicorn", "app.main:app", "--host", "0.0.0.0", "--port", "8000"]
