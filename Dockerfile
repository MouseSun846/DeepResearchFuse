FROM python:3.12-slim-bookworm AS build

# Set build arguments
ARG APP_HOME=/app
ARG TARGETARCH

ENV PYTHONFAULTHANDLER=1 \
    PYTHONHASHSEED=random \
    PYTHONUNBUFFERED=1 \
    PIP_NO_CACHE_DIR=1 \
    PYTHONDONTWRITEBYTECODE=1 \
    PIP_DISABLE_PIP_VERSION_CHECK=1 \
    PIP_DEFAULT_TIMEOUT=100 \
    DEBIAN_FRONTEND=noninteractive

LABEL maintainer="antigravity"
LABEL description="DeepResearchFuse: Automated research using Playwright with noVNC"
LABEL version="1.1"

# Install system dependencies and VNC stack
RUN apt-get update && apt-get install -y --no-install-recommends \
    build-essential \
    curl \
    wget \
    gnupg \
    git \
    xvfb \
    x11vnc \
    novnc \
    websockify \
    fluxbox \
    supervisor \
    && apt-get clean \ 
    && rm -rf /var/lib/apt/lists/*

# Create a non-root user and group
RUN groupadd -r appuser && useradd --no-log-init -r -g appuser appuser

# Create and set permissions for appuser home directory
RUN mkdir -p /home/appuser && chown -R appuser:appuser /home/appuser

WORKDIR ${APP_HOME}

# Copy requirements and install
COPY requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt

# Install Playwright and browsers
RUN playwright install chromium --with-deps

# Ensure all cache directories belong to appuser
RUN mkdir -p /home/appuser/.cache/ms-playwright \
    && cp -r /root/.cache/ms-playwright/chromium-* /home/appuser/.cache/ms-playwright/ \
    && chown -R appuser:appuser /home/appuser/.cache/ms-playwright

# Copy application code
COPY . ${APP_HOME}/

# Copy supervisor config
COPY supervisord.conf /etc/supervisor/conf.d/supervisord.conf

# Create log directory for supervisor
RUN mkdir -p /var/log/supervisor && chown -R appuser:appuser /var/log/supervisor

# Change ownership of the application directory to the non-root user
RUN chown -R appuser:appuser ${APP_HOME}

# Switch to the non-root user
USER appuser

# Set environment variables
ENV PYTHON_ENV=production 
ENV HEADLESS=false
ENV DISPLAY=:99
ENV HOME=/home/appuser

# Expose noVNC port
EXPOSE 6080

# Start supervisor
CMD ["/usr/bin/supervisord", "-c", "/etc/supervisor/conf.d/supervisord.conf"]
