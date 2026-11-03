FROM python:3.13-slim AS base
ENV PYTHONDONTWRITEBYTECODE=1 PYTHONUNBUFFERED=1 PORTLIGHT_BIND=0.0.0.0 PORTLIGHT_DATA_DIR=/data
WORKDIR /opt/portlight
COPY app/ ./app/
FROM base AS verification
COPY tests/ ./tests/
USER 10001:10001
CMD ["python", "-m", "unittest", "discover", "-s", "tests", "-v"]

FROM base AS runtime
USER 10001:10001
EXPOSE 9090
HEALTHCHECK --interval=20s --timeout=3s --start-period=5s --retries=3 CMD ["python", "-c", "import urllib.request; urllib.request.urlopen('http://127.0.0.1:9090/api/health', timeout=2)"]
CMD ["python", "-m", "app.server"]
