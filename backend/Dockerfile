FROM python:3.11-slim

WORKDIR /app

# Install system dependencies
RUN apt-get update && apt-get install -y \
    gcc \
    g++ \
    postgresql-client \
    && rm -rf /var/lib/apt/lists/*

# Copy requirements and replace the base image's setuptools.  Its older
# vendored packages contain known vulnerabilities even though EpiSphere does
# not directly depend on them at runtime.
COPY requirements.txt .
RUN pip install --no-cache-dir --upgrade setuptools==84.0.0 \
    && pip install --no-cache-dir -r requirements.txt

# Create a non-root user and group
RUN groupadd -r episphere && useradd -r -g episphere episphere

# Copy application code
COPY . .

# Create uploads directory, make entrypoint executable, and change ownership
RUN mkdir -p /app/uploads \
    && chmod +x entrypoint.sh \
    && chown -R episphere:episphere /app

# Switch to non-root user
USER episphere

# Expose port
EXPOSE 8000

# Run the application through the entrypoint
ENTRYPOINT ["./entrypoint.sh"]
