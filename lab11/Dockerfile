# Build stage
FROM ghcr.io/astral-sh/uv:python3.12-bookworm-slim AS builder

WORKDIR /app

# Install dependencies
COPY pyproject.toml uv.lock ./
# Sync only inference group to .venv
RUN uv sync --frozen --group inference --no-install-project

# Runtime stage
FROM python:3.12-slim-bookworm

WORKDIR /app

# Copy virtual environment
COPY --from=builder /app/.venv /app/.venv
ENV PATH="/app/.venv/bin:$PATH"

# Copy application code
COPY sentiment_app ./sentiment_app
COPY src ./src

# Copy model artifacts (ONNX + tokenizer.json + classifier.joblib)
COPY model ./model

# Add sentiment_app and root to PYTHONPATH so "app.handler" and "src" can be found
ENV PYTHONPATH="/app/sentiment_app:/app"

# Lambda entrypoint
ENTRYPOINT ["python", "-m", "awslambdaric"]
CMD ["app.handler"]
