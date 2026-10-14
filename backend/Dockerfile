FROM python:3.11-slim

ENV PYTHONDONTWRITEBYTECODE=1 PYTHONUNBUFFERED=1
WORKDIR /app/backend

COPY backend/requirements.txt ./requirements.txt
RUN pip install --no-cache-dir -r requirements.txt

COPY backend/ ./

# Non-root runtime; uploads/results are mounted volumes in compose.
RUN useradd -m appuser && mkdir -p uploads results models data/raw data/processed \
  && chown -R appuser:appuser /app/backend
USER appuser

EXPOSE 5000
HEALTHCHECK --interval=30s --timeout=5s --retries=3 CMD python -c "import urllib.request; urllib.request.urlopen('http://localhost:5000/api/livez')"
CMD ["python", "server/app.py"]
