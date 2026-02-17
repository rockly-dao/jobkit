FROM python:3.11-slim

WORKDIR /app

# Install system dependencies for Playwright
RUN apt-get update && apt-get install -y \
    wget \
    gnupg \
    && rm -rf /var/lib/apt/lists/*

# Copy requirements first for better caching
COPY requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt

# Install Playwright browsers
RUN playwright install chromium && playwright install-deps chromium

# Copy application code
COPY src/ src/
COPY pyproject.toml .

# Install the package
RUN pip install -e .

# Create data directory
RUN mkdir -p /data

ENV JOBKIT_DATA_DIR=/data

EXPOSE 5000

CMD ["jobkit", "web", "--host", "0.0.0.0", "--port", "5000"]
