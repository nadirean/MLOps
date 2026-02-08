FROM python:3.13-slim-bookworm

WORKDIR /app

COPY pyproject.toml uv.lock ./
COPY app.py ./
COPY model/ ./model/

RUN pip install uv && uv sync --no-dev

EXPOSE 8000

CMD ["uv", "run", "uvicorn", "app:app", "--host", "0.0.0.0", "--port", "8000"]
