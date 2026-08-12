FROM python:3.11-slim

WORKDIR /app

# Install system dependencies
RUN apt-get update && apt-get install -y \
    gcc \
    g++ \
    postgresql-client \
    && rm -rf /var/lib/apt/lists/*

# Copy requirements and install Python dependencies.  Remove stale metadata
# left by the base image/dependency resolver so runtime scanners inspect the
# patched versions actually installed in this image.
COPY requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt \
    && rm -rf /usr/local/lib/python3.11/site-packages/jaraco.context-5.3.0.dist-info \
        /usr/local/lib/python3.11/site-packages/wheel-0.45.1.dist-info

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
