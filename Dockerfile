# ===== Base image (stable Debian Bullseye) =====
FROM python:3.11-slim-bullseye

# ===== Working directory =====
WORKDIR /app

# ===== Install minimal dependencies for Playwright Firefox + missing libraries =====
RUN apt-get update && \
    apt-get install -y --no-install-recommends \
        libnss3 \
        libx11-xcb1 \
        libxcomposite1 \
        libxdamage1 \
        libxrender1 \
        libatk1.0-0 \
        libatk-bridge2.0-0 \
        libdrm2 \
        libgbm1 \
        libxss1 \
        libxrandr2 \
        libpangocairo-1.0-0 \
        libcairo-gobject2 \
        libgtk-3-0 \
        libgdk-pixbuf-2.0-0 \
        python3-tk \
        libasound2 \
        libdbus-glib-1-2 \
        libxtst6 \
        libxext6 \
        libxfixes3 \
        libxinerama1 \
        libgl1 \
    && rm -rf /var/lib/apt/lists/* /tmp/* /var/tmp/*

# ===== Install Python dependencies + Playwright with its bundled Firefox =====
COPY requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt && \
    playwright install firefox && \
    pip cache purge

# ===== Find Firefox installation and set environment variable =====
RUN FIREFOX_PATH=$(find /root/.cache/ms-playwright -name "firefox" -type f -executable 2>/dev/null | head -1) && \
    echo "export FIREFOX_BIN=$FIREFOX_PATH" >> /etc/environment && \
    echo "Firefox installed at: $FIREFOX_PATH"

# ===== Environment variables =====
ENV DEBIAN_FRONTEND=noninteractive \
    PYTHONUNBUFFERED=1 \
    PYTHONDONTWRITEBYTECODE=1 \
    DOCKER_CONTAINER=true

# ===== Copy environment config and app =====
COPY .env .env
COPY . .

# ===== Create output directory =====
RUN mkdir -p /app/output

# ===== Expose FastAPI port =====
EXPOSE 8080

# ===== Launch command =====
CMD ["uvicorn", "init:app", "--host", "0.0.0.0", "--port", "8080"]
