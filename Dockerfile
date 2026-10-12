FROM python:3.12-slim AS base
ENV PYTHONDONTWRITEBYTECODE=1
ENV PYTHONUNBUFFERED=1
WORKDIR /app
COPY requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt
RUN useradd --create-home --uid 10001 appuser
COPY --chown=appuser:appuser app ./app
USER appuser
EXPOSE 8000
CMD ["uvicorn", "app.main:app", "--host", "0.0.0.0", "--port", "8000"]
FROM base AS tests
COPY --chown=appuser:appuser tests ./tests
COPY --chown=appuser:appuser pytest.ini .
CMD ["python", "-m", "pytest", "-v", "-p", "no:cacheprovider"]
FROM base AS runtime