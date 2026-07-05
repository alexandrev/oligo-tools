# https://hub.docker.com/_/python
FROM python:3.12-slim-bookworm

ENV PYTHONUNBUFFERED=True
ENV APP_HOME=/app
WORKDIR $APP_HOME

# Install dependencies first to leverage Docker layer caching
COPY requirements.txt ./
RUN pip install --no-cache-dir -r requirements.txt

COPY . ./

# Run as a non-root user (security hardening)
RUN useradd --create-home --uid 10001 appuser && chown -R appuser $APP_HOME
USER appuser

CMD ["uvicorn", "main:app", "--host", "0.0.0.0", "--port", "8080"]
