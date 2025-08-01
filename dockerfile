# ./Dockerfile
# ---------- builder ----------
FROM python:3.12-slim AS builder
ENV PYTHONDONTWRITEBYTECODE=1
WORKDIR /app

# Install runtime deps into a staging prefix
COPY requirements.txt .
RUN pip install --upgrade pip \
    && pip install --prefix /install --no-cache-dir -r requirements.txt

# Install your package (editable in builder so src import paths resolve)
COPY pyproject.toml .
COPY src/ ./src/
RUN pip install --prefix /install --no-cache-dir -e .

# ---------- runner ----------
FROM python:3.12-slim

ENV PYTHONDONTWRITEBYTECODE=1 \
    PYTHONUNBUFFERED=1 \
    PORT=8000

# Create non-root user & group (system account, no login shell)
RUN groupadd -r app && useradd -r -g app app

# App directory; ensure our user owns it
WORKDIR /app
RUN chown -R app:app /app

# Bring in the staged site-packages and scripts from builder
COPY --from=builder /install/ /usr/local/

# (Optional) also include source for easier stack traces / debugging
COPY src/ ./src/

# Run as non-root user *and* group
USER app:app

EXPOSE 8000
CMD ["uvicorn", "ai_rag_agent.main:app", "--host", "0.0.0.0", "--port", "8000"]
