FROM python:3.10-slim

WORKDIR /app

# Set environment variables
ENV PYTHONDONTWRITEBYTECODE=1 \
    PYTHONUNBUFFERED=1 \
    PYTHONPATH=/app

# Install system dependencies
RUN apt-get update && apt-get install -y --no-install-recommends \
    build-essential \
    && apt-get clean \
    && rm -rf /var/lib/apt/lists/*

# Install Python dependencies
COPY requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt

# Create data directory
RUN mkdir -p /app/data

# Copy application code
COPY . .

# Make scripts executable
RUN chmod +x /app/entrypoint.sh
RUN chmod +x /app/src/run_dashboard.py

# Expose API port and Dashboard port
EXPOSE 8000 8501

# Use entrypoint script
ENTRYPOINT ["/app/entrypoint.sh"] 