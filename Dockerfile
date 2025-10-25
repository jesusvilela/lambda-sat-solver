# Lambda SAT Middleware - Docker Container
# Provides a complete environment with Kissat, drat-trim, and Python middleware

FROM python:3.11-slim

# Install build dependencies
RUN apt-get update && apt-get install -y \
    build-essential \
    git \
    wget \
    && rm -rf /var/lib/apt/lists/*

# Create app directory
WORKDIR /app

# Build and install Kissat
RUN cd /tmp && \
    git clone https://github.com/arminbiere/kissat.git && \
    cd kissat && \
    ./configure && \
    make && \
    cp build/kissat /usr/local/bin/ && \
    cd / && rm -rf /tmp/kissat

# Build and install drat-trim
RUN cd /tmp && \
    git clone https://github.com/marijnheule/drat-trim.git && \
    cd drat-trim && \
    make && \
    cp drat-trim /usr/local/bin/ && \
    cd / && rm -rf /tmp/drat-trim

# Verify installations
RUN kissat --version
RUN drat-trim --help || true

# Copy Python backend
COPY backend /app/backend
COPY backend/requirements.txt /app/requirements.txt

# Install Python dependencies
RUN pip install --no-cache-dir -r requirements.txt

# Copy examples
COPY examples /app/examples

# Create non-root user
RUN useradd -m -u 1000 satuser && \
    chown -R satuser:satuser /app
USER satuser

# Expose API port
EXPOSE 5001

# Default command: run API server
CMD ["python", "-m", "backend.api_server"]
