# Infrastructure & Production Deployment Notes

## Overview
This platform is designed to be hosted on AWS (ECS + RDS PostgreSQL + ElastiCache Redis) or GCP (Cloud Run + Cloud SQL PostgreSQL + Memorystore).

---

## 1. Managed Infrastructure Requirements

### PostgreSQL with pgvector
- **Engine:** PostgreSQL 16+
- **Extension:** `CREATE EXTENSION IF NOT EXISTS vector;`
- **Configuration:** Ensure `shared_preload_libraries = 'vector'` is enabled in parameter groups.
- **Connection pooling:** Configure RDS Proxy or PgBouncer with a max pool size proportional to active FastAPI workers and Celery task concurrency.

### Redis Cache and Celery Task Broker
- **AWS:** Amazon ElastiCache for Redis (Cluster mode disabled for standard setups, with in-transit and at-rest encryption enabled).
- **GCP:** Memorystore for Redis with private VPC peering.
- **Eviction Policy:** `allkeys-lru` with TTL configured per cache key.

### Document Storage
- Store uploaded PDF, Markdown, and DOCX files in private S3 or Google Cloud Storage buckets.
- Enforce SSE-KMS encryption and IAM least-privilege role policies.

---

## 2. Containerized Orchestration

### Multi-Service Docker Compose (Local Dev & Staging)
```bash
docker compose up -d
```
Starts:
1. `postgres` (pgvector:pg16) on port `5432`
2. `redis` (redis:7-alpine) on port `6379`
3. `backend` (FastAPI REST & Webhook API) on port `8000`
4. `worker` (Celery Async Worker)
5. `frontend` (React + TypeScript Dashboard) on port `5173`

### Production ECS / Cloud Run
- Separate API containers (`uvicorn app.main:app --workers 4`) from asynchronous workers (`celery -A app.workers.celery_app worker -c 4`).
- Set environment variables via AWS Secrets Manager or GCP Secret Manager.
- Enforce HTTPS termination at the Application Load Balancer / Cloud Load Balancer with strict TLS 1.3 ciphers.

---

## 3. Database Migration Strategy
Run Alembic migrations before dispatching new container versions:
```bash
alembic upgrade head
```
Zero-downtime guidelines:
- Never rename or drop columns in the same release that removes application references.
- Use additive migrations (add nullable column -> deploy code reading/writing column -> backfill -> add not-null constraint).

---

## 4. Operational Monitoring & Health Checks
- **Liveness Probe:** `GET /health/live` (checks process health)
- **Readiness Probe:** `GET /health/ready` (validates database and cache connectivity)
- **Error Tracking:** Integrate Sentry or Datadog for exception alerting and latency tracing.
