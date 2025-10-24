#!/bin/bash
set -e



# echo "Starting Gunicorn..."
exec uv run gunicorn \
    --bind 0.0.0.0:8000 \
    --workers 3 \
    --worker-class sync \
    --worker-connections 1000 \
    --max-requests 1000 \
    --max-requests-jitter 100 \
    --timeout 30 \
    --keep-alive 2 \
    --log-level info \
    --access-logfile - \
    --error-logfile - \
    /app/app.py:app
 
echo "staring gunicorn ...."
gunicorn -w 4 -b 0.0.0.0:8000 'src.app:create_app()'
