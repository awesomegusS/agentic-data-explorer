# Dockerfile
# Multi-stage Dockerfile for Agentic Data Explorer

# Stage 1: Base image with conda
FROM continuumio/miniconda3:latest as base

# Set environment variables
ENV PYTHONUNBUFFERED=1 \
    PYTHONDONTWRITEBYTECODE=1 \
    CONDA_AUTO_UPDATE_CONDA=false

# Install system dependencies
RUN apt-get update && apt-get install -y \
    curl \
    git \
    && rm -rf /var/lib/apt/lists/*

# Create app directory
WORKDIR /app

# Copy conda environment file
COPY environment.yml .

# Create conda environment
RUN conda env create -f environment.yml && conda clean -ya

# Make RUN commands use the new environment
SHELL ["conda", "run", "-n", "agentic_data_explorer", "/bin/bash", "-c"]

# Stage 2: Development image
FROM base as development

# Copy source code
COPY . .

# Expose port
EXPOSE 8000

# Default command for development
CMD ["conda", "run", "--no-capture-output", "-n", "agentic_data_explorer", "uvicorn", "app.main:app", "--host", "0.0.0.0", "--port", "8000", "--reload"]

# Stage 3: Production image
FROM base as production

# Create non-root user
RUN useradd --create-home --shell /bin/bash app

# Copy source code
COPY --chown=app:app . .

# Create logs directory
RUN mkdir -p /app/logs && chown app:app /app/logs

# Switch to non-root user
USER app

# Health check
HEALTHCHECK --interval=30s --timeout=10s --start-period=30s --retries=3 \
    CMD curl -f http://localhost:8000/api/v1/health || exit 1

# Expose port
EXPOSE 8000

# Production command
CMD ["conda", "run", "--no-capture-output", "-n", "agentic_data_explorer", "uvicorn", "app.main:app", "--host", "0.0.0.0", "--port", "8000", "--workers", "1"]

