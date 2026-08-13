# MLOps

Practical MLOps coursework (AGH University of Krakow). Each lab is a self-contained project covering one stage of the ML lifecycle, from data engineering to model serving and monitoring.

Labs 1-13 of the course are covered (lab9 is not part of this repo).

## Labs

| Lab | Topic | Stack |
|-----|-------|-------|
| [lab1](#lab1---ml-api-service) | ML API service | FastAPI, Docker, pydantic-settings, pytest |
| [lab1-homework](#homework-1---sentiment-analysis-api) | Sentiment analysis API | sentence-transformers, FastAPI, Docker |
| [lab2](#lab2---sql--analytical-databases) | SQL & analytical databases | PostgreSQL (psycopg), DuckDB |
| [lab3](#lab3---data-processing-with-polars) | DataFrame processing | Polars (eager/lazy), NYC taxi data |
| [lab4](#lab4---vector-similarity-search--rag) | Vector similarity search & RAG | pgvector/TimescaleDB, Milvus, CLIP, Gemini |
| [lab5](#lab5---data-cleaning-cli-with-dvc) | Data cleaning & versioning | Python CLI, DVC |
| [lab6](#lab6---data-quality-behavioral-testing--explainability) | Data quality & explainability | CleanLab, Giskard, Captum, DistilBERT |
| [lab7](#lab7---inference-optimization--onnx) | Inference optimization | PyTorch, ONNX/ORT, Docker |
| [lab8](#lab8---drift--monitoring-scaffold) | Drift & monitoring (scaffold) | evidently, nannyml |
| [lab10](#lab10---infrastructure-as-code-terraform) | Infrastructure as Code | Terraform |
| [lab11](#lab11---serverless-inference-with-aws-lambda-sam) | Serverless serving & CI/CD | AWS Lambda (SAM), ONNX, GitHub Actions |
| [lab12](#lab12---data-pipelines-with-apache-airflow-3) | Data orchestration | Apache Airflow 3, LocalStack S3, Postgres |
| [lab13](#lab13---llm-serving--agent-tools) | LLM serving & agent tools | FastMCP, guardrails-ai, vLLM |

## Organization

- Each lab is self-contained with its own `pyproject.toml`, `uv.lock`, and where applicable a `.gitignore`; dependencies are managed with [uv](https://docs.astral.sh/uv/).
- Notebook-based labs expect `uv sync` then `jupyter lab`; service-based labs run via `uv run` or `docker compose up`.

---

# Lab 1 - ML API Service

Serve a trained ML model (Iris decision tree) behind a FastAPI REST API, with per-environment config management and a containerized deployment.

- `training.py` - trains a `DecisionTreeClassifier` on the Iris dataset, saves `model.joblib`
- `app.py` - FastAPI service with `/`, `/health`, `/predict`
- `settings.py`, `secrets.yaml`, `.env.{dev,test,prod}` - pydantic-settings config per environment (SOPS-encrypted secrets demo)
- `main.py` - CLI that dumps the environment config for a given environment
- `Dockerfile` + `docker-compose.yaml` - uv-based container serving on port 8000
- `tests/` - pytest for the app, env and settings

```bash
uv sync
python training.py                     # train + save model.joblib
uv run uvicorn app:app --port 8000     # serve the API
uv run pytest                          # run tests
docker compose up                      # or run via Docker
```

Config is loaded per environment (dev/test/prod) via `pydantic-settings`; predictions map to setosa / versicolor / virginica.

---

# Homework 1 - Sentiment Analysis API

Wrap a text-sentiment classifier (negative / neutral / positive) as a FastAPI service with input validation and Docker packaging.

- `app.py` - loads `model/sentence_transformer.model` + `model/classifier.joblib` at startup, exposes `/predict`
- `test_app.py` - 7 pytest cases, incl. 422 on empty / missing / invalid input
- `Dockerfile` + `docker-compose.yaml` - containerized service
- `.pre-commit-config.yaml` - ruff-based pre-commit hooks

```bash
uv sync
uv run uvicorn app:app --port 8000
uv run pytest
docker compose up
```

Requires the model artifacts in `model/` (gitignored); validation returns 422 for empty or malformed requests.

---

# Lab 2 - SQL & Analytical Databases

Query Dutch railway data using PostgreSQL (via psycopg) and DuckDB, and compare the two workflows and file formats.

- `notebook_01_psycopg.ipynb` - Postgres basics + exercise (late trains exported to JSONL)
- `notebook_02_duckdb.ipynb` - DuckDB tutorial + exercises
- `notebook_03_homework.ipynb` - full pipeline: download -> DuckDB tables (`stations`, `distances`, `disruptions`, `services`) -> analytical queries + plots
- `compose.yaml` - PostgreSQL 17 on port 5432
- `exported_query.csv` - sample query export; `data/services_table.sql` - table definition

```bash
docker compose up -d     # start PostgreSQL
jupyter lab              # run the notebooks
```

Key results: benchmark of CSV / JSON / JSONL / Parquet (size + load time); homework plots for average delay by operator, disruptions per year, cancellation fraction, and distance histogram.

---

# Lab 3 - Data Processing with Polars

Process 2024 NYC yellow-taxi trips with Polars: eager and lazy execution, filtering, joins, time aggregations, and dtype optimization.

- `notebook_polars.ipynb` - Polars tutorial + 4 exercise blocks
- `homework.ipynb` - cleaning -> feature extraction -> daily aggregation -> analysis with plots

```bash
uv sync
jupyter lab
```

Key results: daily-aggregated taxi dataset with plots by borough and daily totals; data-quality findings (2002 timestamps, rows with >6 passengers, uniform NULL rows).

---

# Lab 4 - Vector Similarity Search & RAG

Build vector similarity search and retrieval-augmented generation (RAG) on top of vector databases.

- `lab4.ipynb` - pgvector (TimescaleDB) embeddings for Steam games and images; Milvus collection; Gemini-based RAG Q&A over a PDF
- `homework.ipynb` - CLIP image search (`clip-ViT-B-32`) via a custom `ImageSearch` class
- `docker-compose.yml` - TimescaleDB pg16 with the `vector` extension enabled
- `milvus_db/docker-compose.yml` - Milvus standalone (etcd + minio + milvus v2.4.13)

```bash
docker compose up -d                                          # TimescaleDB
docker compose -f milvus_db/docker-compose.yml up -d          # Milvus
jupyter lab
```

Key results: cosine-similarity queries return nearest images / games; RAG answers from the PDF context; the homework shows top-K image matches. The RAG part requires a `GEMINI_KEY` environment variable.

---

# Lab 5 - Data Cleaning CLI with DVC

Reproducibly clean the Ames housing dataset as a CLI step, with the inputs versioned via DVC.

- `ames_data_cleaning.py` - `clean-ames-data --file-path`: NA defaults, categorical encoding, outlier removal, dtype fixes (in-place parquet)
- `ames_inspect_data.py` - `inspect-ames-data --file-path`
- `data/*.dvc` - DVC pointers for the parquet dataset and its description file

```bash
uv sync
dvc pull                    # fetch the data from the remote
uv run python ames_data_cleaning.py --file-path data/ames_data_2006_2008.parquet
```

The raw data is not committed; the `data/*.dvc` pointers are.

---

# Lab 6 - Data Quality, Behavioral Testing & Explainability

Run a full quality workflow for a text classifier on Banking77: label-quality analysis, training, behavioral testing, and explanations.

- `HOMEWORK.ipynb`:
  - CleanLab - label errors / outliers / duplicates on `PolyAI/banking77`
  - Trains a `distilbert-base-uncased` classifier (77 classes)
  - Giskard behavioral `scan()`
  - Captum `InputXGradient` local explanations

```bash
uv sync
jupyter lab     # run HOMEWORK.ipynb (GPU optional)
```

Key results: CleanLab fixes + embedded sentence-transformer + LogisticRegressionCV probabilities; Giskard flags data-diversity issues; Captum shows the model focusing on keywords such as "card".

---

# Lab 7 - Inference Optimization & ONNX

Benchmark transformer inference across optimization levels and compare PyTorch vs ONNX Runtime Docker images (size and response time).

- `lab7.ipynb` - exercises: eval/no_grad/inference_mode, `torch.compile`, dynamic quantization, GPU fp32/fp16/AMP, ONNX export with online/offline ORT optimization
- `docker/Dockerfile.pytorch` + `docker/Dockerfile.onnx` - CPU-only FastAPI services
- `docker/app_pytorch.py`, `docker/app_onnx.py`, `docker/benchmark.py` - 100-request latency benchmark
- Results committed: `docker_size_comparison.png`, `docker_response_time_comparison.png`

```bash
uv sync
jupyter lab                  # exercises 1-6 (exercise 4 needs a GPU)
# Docker comparison
docker build -f docker/Dockerfile.pytorch -t app-pytorch .
docker build -f docker/Dockerfile.onnx -t app-onnx .
uv run python docker/benchmark.py http://localhost:8000/predict
```

Key results: ONNX image is smaller and responds faster than the PyTorch image; ms timings for baseline vs compiled vs quantized vs ONNX, incl. cold start.

---

# Lab 8 - Drift & Monitoring (scaffold)

Experiment with model-drift and LLM monitoring tooling.

- Environment scaffold with dependencies for drift detection and monitoring: `evidently` (0.6.7), `nannyml`, `datasets`, `sentence-transformers`, `transformers`.

```bash
uv sync
```

Only the dependency scaffold is tracked here; no analysis notebooks are included in this repo.

---

# Lab 10 - Infrastructure as Code (Terraform)

Provision cloud resources declaratively with Terraform across three exercises.

- `exercise1-github/` - GitHub repository provisioning via the `integrations/github` provider
- `exercise2-multi-region/` - multi-region AWS S3 buckets (aliased providers + random suffix)
- `exercise3-modules/` - reusable S3 bucket module (versioning + Glacier lifecycle transition)

```bash
cd exerciseN-.../
terraform init
terraform plan        # review changes
terraform apply
```

Requires AWS / GitHub credentials (passed via `variables.tf`). No `tfstate` files are committed.

---

# Lab 11 - Serverless Inference with AWS Lambda (SAM)

Serve a sentiment model on AWS Lambda: export the models to ONNX, package as a Lambda container, deploy with SAM, and orchestrate the whole path via GitHub Actions CI/CD.

- `src/scripts/` - `download_artifacts.py`, `export_sentence_transformer_to_onnx.py`, `export_classifier_to_onnx.py`, `settings.py` (S3 bucket, ONNX paths)
- `sentiment_app/app.py` - ONNX Runtime inference behind FastAPI + Mangum (Lambda handler); `test_app.py`
- `main.py` - CLI: `python main.py download|export`
- `Dockerfile` (Lambda `awslambdaric`) + `Dockerfile.dev` (local uvicorn)
- `sam-template.yaml` - `HttpApi` `/predict`, image package
- `.github/workflows/` - `hello_world.yaml`, `ci_cd_workflow.yaml` (ruff + pytest -> ECR -> SAM deploy)

```bash
uv sync --group integration --group inference
uv run pytest sentiment_app/test_app.py
uv run python main.py download && uv run python main.py export
# local dev
docker build -f Dockerfile.dev -t app .
# deploy via the CI/CD workflow (ECR + SAM)
```

CI/CD uses GitHub Actions secrets for AWS credentials; `successful_run.png` shows an example workflow run.

---

# Lab 12 - Data Pipelines with Apache Airflow 3

Deploy Airflow 3 (Celery executor) with Postgres, Valkey, and LocalStack S3, then build progressive DAG patterns ending in a NYC taxi ingest + training pipeline.

- `compose.yml` - postgres, valkey, localstack (S3), airflow-init/api-server/scheduler/worker/triggerer/dag-processor
- `dags/01_class_pipeline.py` ... `09_nyc_taxi_training.py` - class-based vs TaskFlow, scheduling, backfilling, virtualenv tasks, S3 integration, connections/variables; NYC green-taxi ingest (monthly download -> daily aggregation -> S3) and a training DAG that logs `test_mae` to Postgres `model_performance`
- `localstack-init/ready.d/01-create-buckets.sh` - 5 S3 buckets
- `postgres-init/init.sql` - `exchange_rates`, `model_performance` tables
- `screenshots/` - DAG graphs, runs, buckets, Postgres

```bash
cp .env.example .env        # add TWELVEDATA_API_KEY
docker compose up           # Airflow UI at :8080 (airflow/airflow)
```

Trigger DAGs manually or via backfill. Static keys in `compose.yml` / `config/airflow.cfg` are local-dev placeholders ("fake security for local setup") - use a secret backend in production; pipeline credentials (AWS/LocalStack, Postgres) are local-dev defaults.

---

# Lab 13 - LLM Serving & Agent Tools

Serve LLMs efficiently and extend them with tools: inference with KV-cache sizing, function-calling tools, and MCP servers with guardrails.

- `exercise1_inference.py` - LLM inference with KV-cache memory sizing
- `exercise2_tools.py` - function/tool calling
- `exercise3_mcp_server.py` + `exercise4_mcp_viz.py` / `exercise4_test.py` - MCP server and client
- `exercise5_guardrails.py` - guardrails-ai validation
- `homework.py`, `homework_ow_mcp.py`, `homework_tavily_mcp.py` - homework with a Tavily MCP search tool
- `Dockerfile` + `docker-compose.yml` + `requirements.txt` - vLLM + app containers
- `screenshots/` - results per exercise

```bash
uv sync
uv run python exercise1_inference.py
# ... or via docker compose up (vLLM backend)
```

API keys come from the environment (`os.environ`) or `${VAR}` references in `docker-compose.yml`; `requirements.txt` mirrors the pyproject deps for the containerized vLLM backend.