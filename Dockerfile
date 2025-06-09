# Build stage
FROM python:3.13-alpine AS builder

WORKDIR /app

# Install build dependencies
RUN apk add --no-cache build-base

# Install setuptools first
RUN pip install --no-cache-dir setuptools

# Install Python dependencies
COPY requirements.txt .
RUN pip install --user --no-cache-dir -r requirements.txt

# Copy only necessary source files
COPY . .

# Final stage
FROM python:3.13-alpine

WORKDIR /app

# Copy installed Python packages from builder
COPY --from=builder /root/.local /root/.local
ENV PATH=/root/.local/bin:$PATH

# Copy application code
COPY --from=builder /app .

# Set environment variables
ENV PYTHONPATH=/app

CMD ["python", "bot.py"]