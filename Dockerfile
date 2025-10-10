# Lightweight Python 3.12 image for the app
FROM python:3.12-slim

ENV PYTHONUNBUFFERED=1

# Install uv
COPY --from=ghcr.io/astral-sh/uv:latest /uv /uvx /bin/

WORKDIR /app

# Copy only lock/manifest first for better caching
COPY pyproject.toml uv.lock* ./
RUN uv export --format requirements-txt --no-dev > /tmp/reqs.txt \
 && uv pip install --system -r /tmp/reqs.txt


# Now copy the rest of the app
COPY . .

EXPOSE 8000
CMD ["uvicorn", "main:app", "--host", "0.0.0.0", "--port", "8000", "--reload"]