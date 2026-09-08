web: gunicorn app:app --bind 0.0.0.0:$PORT --timeout 300 --graceful-timeout 300 --worker-class gthread --workers 2 --threads 4 --forwarded-allow-ips='*' --access-logfile - --error-logfile -
