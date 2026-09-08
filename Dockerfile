FROM python:3.13-slim

# Unbuffer stdout/stderr so logs reach `dokku logs` in real time rather than
# sitting in a block buffer during a long-running summary.
ENV PYTHONUNBUFFERED=1 \
    PYTHONDONTWRITEBYTECODE=1 \
    PIP_NO_CACHE_DIR=1

WORKDIR /app

COPY requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt

COPY . .

# Don't run as root inside the container
RUN useradd --create-home --uid 1000 appuser && chown -R appuser /app
USER appuser

EXPOSE 8000

# --forwarded-allow-ips lets gunicorn trust Dokku's nginx proxy headers.
# The long timeout matches the app: a large summary can take a couple of
# minutes, and threaded workers keep one slow request from blocking the rest.
CMD gunicorn app:app \
    --bind 0.0.0.0:${PORT:-8000} \
    --timeout 300 --graceful-timeout 300 \
    --worker-class gthread --workers 2 --threads 4 \
    --forwarded-allow-ips='*' \
    --access-logfile - --error-logfile -
