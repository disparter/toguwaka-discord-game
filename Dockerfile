# Build stage
FROM python:3.11-alpine AS builder

WORKDIR /app

# Install build dependencies and required system libraries
RUN apk add --no-cache \
    build-base \
    python3-dev \
    py3-pip \
    libffi-dev \
    cairo-dev \
    pango-dev \
    gdk-pixbuf-dev \
    gcc \
    musl-dev \
    linux-headers \
    g++ \
    make \
    freetype-dev \
    libpng-dev \
    openblas-dev

# Install setuptools and wheel first
RUN pip install --no-cache-dir setuptools wheel

# Install Python dependencies
COPY requirements.txt .
RUN pip install --user --no-cache-dir -r requirements.txt

# Copy only necessary source files
COPY . .

# Final stage
FROM python:3.11-alpine

WORKDIR /app

# Install runtime dependencies
RUN apk add --no-cache \
    libstdc++ \
    cairo \
    pango \
    gdk-pixbuf \
    freetype \
    libpng \
    openblas

# Copy installed Python packages from builder
COPY --from=builder /root/.local /root/.local
ENV PATH=/root/.local/bin:$PATH

# Copy application code
COPY --from=builder /app .

# Set environment variables
ENV PYTHONPATH=/app

CMD ["python", "bot.py"]