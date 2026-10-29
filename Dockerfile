FROM python:3.12-slim

ENV PYTHONDONTWRITEBYTECODE=1 \
    PYTHONUNBUFFERED=1 \
    PIP_NO_CACHE_DIR=1 \
    FLASK_ENV=production \
    PORT=5000

WORKDIR /app

RUN addgroup --system appgroup && adduser --system --ingroup appgroup appuser

COPY requirements.txt ./
RUN pip install --no-cache-dir -r requirements.txt

COPY --chown=appuser:appgroup . ./
# Personnel photos are kept outside the public static folder; mount a
# persistent volume or disk at /app/uploads so they survive redeploys.
RUN mkdir -p /app/uploads && chown -R appuser:appgroup /app/uploads

USER appuser
EXPOSE 5000

HEALTHCHECK --interval=30s --timeout=5s --start-period=20s --retries=3 \
    CMD python -c "import os; from urllib.request import urlopen; urlopen('http://127.0.0.1:%s/healthz' % os.environ.get('PORT', '5000'), timeout=3)"

# Apply pending migrations, then serve on $PORT (hosts such as Render set it).
CMD ["sh", "-c", "flask --app app:create_app db upgrade && exec gunicorn --bind 0.0.0.0:${PORT} --workers 2 --timeout 60 --access-logfile - app:app"]
