# AI Customer Operations Platform

An AI-powered customer support operations platform that automates ticket classification, knowledge retrieval, response drafting, team routing, and operational analytics while keeping humans in control of customer-facing decisions.

## Overview

Customer support teams receive requests through emails, chat applications, website forms, and third-party integrations. Processing these requests manually creates delays, inconsistent responses, incorrect assignments, and limited visibility into support performance.

The **AI Customer Operations Platform** provides a unified system for processing support tickets with the help of large language models (LLMs), retrieval-augmented generation (RAG), background workers, and configurable business workflows.

The platform classifies incoming tickets, retrieves relevant company documentation, generates evidence-backed response suggestions, routes tickets to appropriate teams, and requires authorized human approval before sending AI-generated responses.

It also provides multi-tenant organization management, role-based access control, conversation history, audit logs, and analytics.

> **Core principle:** AI assists the support workflow; deterministic business rules and authorized humans control consequential actions.

## Problem Statement

Traditional customer support operations often suffer from:

- Manual classification and assignment of incoming tickets.
- Repeated searches through policies, FAQs, and product documentation.
- Inconsistent responses across support agents.
- Slow escalation of urgent or sensitive issues.
- Limited visibility into ticket resolution and escalation trends.
- Poor traceability of changes, approvals, and customer communications.
- Difficulty separating customer data across multiple organizations.

This platform addresses these problems by combining AI-assisted decision support with conventional backend engineering and workflow automation.

## Objectives

- Centralize customer support tickets and conversations.
- Automatically classify tickets by intent, category, priority, and sentiment.
- Retrieve relevant knowledge using RAG.
- Generate response suggestions grounded in authorized documentation.
- Route tickets according to configurable business rules.
- Require human review before sending AI-generated replies.
- Support multiple organizations with isolated data and permissions.
- Track ticket lifecycle events and operational performance.
- Provide a maintainable, testable, containerized application.

## Key Features

### Ticket Management
- Create tickets through REST APIs and webhook adapters.
- Track ticket status, priority, category, ownership, and timestamps.
- Maintain conversation history and internal notes.
- Support assignment, escalation, resolution, and reopening.
- Handle duplicate external events through idempotency checks.

### AI-Powered Classification
- Identify ticket intent and category.
- Predict priority and customer sentiment.
- Return structured, validated model output.
- Use deterministic fallback rules when classification fails.
- Record model and prompt versions for evaluation.

### Retrieval-Augmented Generation
- Ingest supported knowledge documents.
- Extract, chunk, and embed document content.
- Store embeddings and metadata in PostgreSQL with pgvector.
- Retrieve relevant passages for individual tickets.
- Apply organization and document access filters.
- Generate suggested replies with source citations.
- Support uncertainty and escalation when evidence is insufficient.

### Human-in-the-Loop Workflow
- Review AI-generated drafts.
- Edit, approve, or reject suggestions.
- Require authorization before external delivery.
- Track the reviewer and approval timestamp.
- Prevent rejected or unapproved drafts from being sent.
- Preserve the distinction between a draft and an actual customer message.

### Team Routing
- Assign tickets using category, priority, organization settings, and team rules.
- Escalate sensitive or high-priority requests.
- Support configurable team ownership.
- Allow authorized managers to reassign tickets.

### Multi-Tenancy and RBAC
- Manage organizations, members, teams, and roles.
- Enforce organization-scoped data access.
- Restrict sensitive actions by role.
- Prevent cross-organization access through authorization checks.
- Maintain an audit trail for important operations.

### Background Processing and Caching
- Process expensive AI tasks asynchronously.
- Use Redis as a Celery task broker and cache.
- Retry eligible transient failures.
- Track task status and processing errors.
- Cache safe, reusable retrieval or computation results.
- Invalidate cached data when relevant source data changes.

### Analytics and Observability
- Track ticket volume and category distribution.
- Measure ticket processing and resolution durations.
- Monitor escalation and approval rates.
- Record AI latency, errors, and token usage when available.
- Inspect audit events and processing failures.
- Compare model quality against a labeled evaluation dataset.

## Technology Stack

| Layer | Technology | Purpose |
|---|---|---|
| Backend | Python | Application logic and AI integration |
| API | FastAPI | REST endpoints, webhooks, validation, OpenAPI |
| Database | PostgreSQL | Persistent application data |
| Vector Search | pgvector | Semantic document retrieval |
| ORM | SQLAlchemy | Database access and models |
| Migrations | Alembic | Versioned database schema changes |
| Cache and Broker | Redis | Caching and background task transport |
| Background Jobs | Celery | Asynchronous ticket and document processing |
| AI Orchestration | LangChain, selectively | Model and retrieval integrations |
| Embeddings | Hugging Face-compatible embedding model | Document and query vectorization |
| LLM | Configurable provider adapter | Classification and response generation |
| Frontend | React + TypeScript | Support dashboard |
| Styling | Tailwind CSS | UI components and responsive layout |
| Testing | pytest | Unit, integration, and API tests |
| Frontend Testing | Vitest + React Testing Library | UI and component tests |
| Containers | Docker + Docker Compose | Reproducible development environment |
| CI | GitHub Actions | Automated tests and quality checks |
| Deployment | AWS or GCP | Hosted application infrastructure |

### Why this stack?

- **FastAPI** provides typed request validation and API documentation.
- **PostgreSQL** stores transactional business data reliably.
- **pgvector** avoids the operational complexity of introducing a separate vector database during the initial build.
- **Redis and Celery** separate expensive processing from user-facing requests.
- **React and TypeScript** support an interactive operations dashboard.
- **Docker Compose** simplifies local setup and service coordination.
- **Provider abstraction** prevents business logic from depending on one model vendor.

Use one LLM provider for the first working version. Add other providers behind the same interface when there is a concrete need.

## System Architecture

```mermaid
flowchart TD
    A[Customer Channels] --> B[FastAPI Application]
    B --> C[Authentication and Tenant Context]
    C --> D[Authorization and Validation]
    D --> E[Ticket Service]

    E --> F[(PostgreSQL + pgvector)]
    E --> G[Redis Task Broker]
    G --> H[Celery Workers]

    H --> I[Ticket Classification]
    H --> J[Knowledge Retrieval]
    I --> K[Routing Rules]
    J --> L[Grounded Response Generation]
    L --> M[Draft and Citation Validation]

    K --> N[Ticket State and Assignment]
    M --> O[Human Approval Queue]
    O --> P[Authorized Response Delivery]

    N --> F
    O --> F
    P --> F

    Q[React Dashboard] <--> B
    F --> R[Analytics and Audit Events]
```

### Architecture Responsibilities

**FastAPI application**
- Handles authentication and request validation.
- Exposes ticket, conversation, knowledge, approval, and analytics APIs.
- Enforces tenant-scoped authorization.
- Persists state transitions and enqueues background jobs.

**PostgreSQL**
- Stores organizations, users, memberships, teams, tickets, messages, documents, drafts, and audit events.
- Maintains relationships and transactional integrity.
- Stores document embeddings through pgvector.

**Redis and Celery**
- Execute AI processing outside the request-response cycle.
- Support retries and task monitoring.
- Cache selected reusable results.
- Prevent slow model calls from blocking ticket creation.

**AI processing layer**
- Classifies ticket content.
- Retrieves authorized knowledge passages.
- Generates grounded response drafts.
- Validates outputs and produces structured results.

**React dashboard**
- Displays ticket queues and conversation history.
- Provides draft review and approval controls.
- Shows team assignments and operational metrics.

## End-to-End Workflow

### 1. Ticket Ingestion

A customer submits a ticket through a web form, REST API, or supported webhook.

The API validates the payload, derives the organization from the authenticated integration or verified context, checks for duplicate events, and stores the ticket.

The ticket is assigned an initial processing state and a background task is queued.

### 2. Ticket Classification

A background worker sends the ticket content to the configured classifier.

Example output:

```json
{
  "category": "billing",
  "priority": "high",
  "sentiment": "frustrated",
  "intent": "duplicate_charge",
  "needs_human_review": true
}
```

This is illustrative output, not a measured model result.

The application validates the response against a predefined schema. Invalid or failed results enter a retry or fallback path instead of silently becoming trusted classifications.

### 3. Knowledge Ingestion

An authorized organization administrator uploads a supported document.

The ingestion pipeline:

1. Validates the file type and size.
2. Extracts its text.
3. Splits the content into manageable chunks.
4. Generates embeddings.
5. Stores the chunks, embeddings, and source metadata.
6. Associates the document with its organization and access scope.

Document ingestion should run asynchronously for larger files.

### 4. Retrieval-Augmented Generation

The system converts the ticket into a retrieval query and searches for relevant passages.

Retrieval filters are applied to ensure that results belong to the correct organization and are accessible to the requesting workflow.

The application sends the ticket, relevant passages, and response instructions to the configured LLM.

The model returns a draft response and references to supporting evidence.

The backend verifies that the references correspond to real retrieved sources before displaying them as citations.

### 5. Team Routing

A routing service applies organization-specific rules.

Example rules:

- Billing-related tickets → Billing Support.
- High-priority technical failures → Technical Support.
- Security-related issues → Security queue and mandatory escalation.
- Uncertain classifications → Manual triage.

Routing should be deterministic wherever possible. An LLM may suggest a category, but it should not have unrestricted authority to assign arbitrary teams or perform privileged actions.

### 6. Human Review

The support dashboard displays the ticket, conversation history, classification, suggested reply, and citations.

An authorized agent may:

- Edit the draft.
- Approve the draft.
- Reject the draft.
- Escalate the ticket.
- Request another draft.

Approval and delivery are separate operations. Only an approved draft may be sent through an implemented and authorized delivery adapter.

### 7. Analytics and Auditing

The platform records ticket transitions, assignment changes, draft generation, approval decisions, delivery outcomes, and errors.

Analytics are calculated from persisted data and timestamps, not fabricated by the LLM.

## Data Model

The initial relational model includes the following entities.

| Entity | Important fields | Responsibility |
|---|---|---|
| Organization | id, name, settings | Tenant configuration |
| User | id, email, status | User identity |
| Membership | organization_id, user_id, role | Organization-specific permissions |
| Team | id, organization_id, name | Support team configuration |
| Ticket | id, organization_id, status, priority, category, team_id | Main support record |
| Message | id, ticket_id, sender_type, body, created_at | Conversation history |
| KnowledgeDocument | id, organization_id, title, version, status | Uploaded knowledge sources |
| DocumentChunk | id, document_id, content, embedding, metadata | Searchable passages |
| ResponseDraft | id, ticket_id, body, status, created_by_model | AI-generated suggestions |
| Citation | id, draft_id, chunk_id | Evidence supporting a draft |
| AuditEvent | id, organization_id, actor_id, action, timestamp | Traceability |
| ProcessingJob | id, ticket_id, status, error_code | Processing status and diagnostics |

Use UUIDs or another consistent identifier strategy, foreign keys, appropriate indexes, and UTC timestamps.

Important implementation rules:

- Tenant-owned records must be scoped by organization.
- Messages and drafts must retain their parent ticket relationship.
- Document chunks must retain their source document and version.
- Approval decisions must identify the acting user.
- Audit records should not be silently rewritten through ordinary application operations.

## Ticket Lifecycle

An example lifecycle is:

```text
received
   |
   v
processing
   |
   +----> needs_triage
   |
   v
awaiting_review
   |
   +----> rejected / revised
   |
   v
approved
   |
   v
sending
   |
   +----> send_failed
   |
   v
sent
   |
   v
resolved
```

Use explicit allowed state transitions and validate them in the backend. Exact states may be refined during implementation.

A worker retry must not create duplicate customer replies. Delivery should use an idempotency key where supported and reconcile uncertain outcomes with the delivery provider.

## API Design

All routes below are proposed application contracts. They become available only when implemented.

### Authentication and Organization

| Method | Endpoint | Purpose |
|---|---|---|
| POST | `/api/v1/auth/login` | Authenticate a user |
| GET | `/api/v1/auth/me` | Retrieve current identity and memberships |
| GET | `/api/v1/organizations` | List authorized organizations |
| GET | `/api/v1/organizations/{org_id}/members` | List authorized members |
| POST | `/api/v1/organizations/{org_id}/members` | Add a member, subject to permissions |

### Tickets and Conversations

| Method | Endpoint | Purpose |
|---|---|---|
| POST | `/api/v1/tickets` | Create a ticket |
| GET | `/api/v1/tickets` | List tickets with authorized filters |
| GET | `/api/v1/tickets/{ticket_id}` | Retrieve ticket details |
| PATCH | `/api/v1/tickets/{ticket_id}` | Update permitted ticket fields |
| GET | `/api/v1/tickets/{ticket_id}/messages` | Retrieve conversation history |
| POST | `/api/v1/tickets/{ticket_id}/messages` | Add a message |
| POST | `/api/v1/tickets/{ticket_id}/classify` | Request classification |
| POST | `/api/v1/tickets/{ticket_id}/escalate` | Escalate a ticket |

### Knowledge and AI Suggestions

| Method | Endpoint | Purpose |
|---|---|---|
| POST | `/api/v1/knowledge/documents` | Upload a knowledge document |
| GET | `/api/v1/knowledge/documents` | List authorized documents |
| GET | `/api/v1/knowledge/documents/{document_id}` | Retrieve document processing status |
| POST | `/api/v1/tickets/{ticket_id}/drafts` | Generate a response suggestion |
| GET | `/api/v1/tickets/{ticket_id}/drafts` | List ticket drafts |
| POST | `/api/v1/drafts/{draft_id}/approve` | Approve a draft |
| POST | `/api/v1/drafts/{draft_id}/reject` | Reject a draft |
| POST | `/api/v1/drafts/{draft_id}/send` | Deliver an approved draft |

### Operations

| Method | Endpoint | Purpose |
|---|---|---|
| GET | `/api/v1/analytics/overview` | Retrieve operational metrics |
| GET | `/api/v1/analytics/tickets` | Retrieve ticket trends |
| GET | `/api/v1/audit-events` | Retrieve authorized audit events |
| POST | `/api/v1/webhooks/tickets` | Receive supported external ticket events |
| GET | `/health/live` | Check process liveness |
| GET | `/health/ready` | Check application dependency readiness |

Protect every endpoint with appropriate authentication, authorization, tenant filtering, validation, and rate limits.

### Example: Create a Ticket

Request:

```http
POST /api/v1/tickets
Authorization: Bearer <access-token>
Content-Type: application/json
```

```json
{
  "subject": "Duplicate subscription charge",
  "description": "I was charged twice for my subscription.",
  "source": "web",
  "external_id": "support-form-12345"
}
```

Example response:

```json
{
  "id": "ticket-uuid",
  "status": "processing",
  "priority": "normal",
  "category": null,
  "created_at": "2026-10-25T08:00:00Z"
}
```

The identifiers and timestamps are illustrative. The actual implementation should use real database-generated values.

## Repository Structure

```text
ai-customer-operations-platform/
├── backend/
│   ├── app/
│   │   ├── api/
│   │   │   ├── routes/
│   │   │   └── dependencies.py
│   │   ├── core/
│   │   │   ├── config.py
│   │   │   ├── security.py
│   │   │   └── logging.py
│   │   ├── db/
│   │   │   ├── session.py
│   │   │   └── base.py
│   │   ├── models/
│   │   ├── schemas/
│   │   ├── repositories/
│   │   ├── services/
│   │   │   ├── ticket_service.py
│   │   │   ├── routing_service.py
│   │   │   ├── approval_service.py
│   │   │   └── analytics_service.py
│   │   ├── ai/
│   │   │   ├── classifier.py
│   │   │   ├── embeddings.py
│   │   │   ├── retriever.py
│   │   │   ├── generator.py
│   │   │   ├── prompts.py
│   │   │   └── evaluation.py
│   │   ├── workers/
│   │   │   ├── celery_app.py
│   │   │   └── tasks.py
│   │   └── main.py
│   ├── alembic/
│   ├── tests/
│   │   ├── unit/
│   │   ├── integration/
│   │   └── api/
│   ├── pyproject.toml
│   └── Dockerfile
├── frontend/
│   ├── src/
│   │   ├── api/
│   │   ├── components/
│   │   ├── features/
│   │   │   ├── tickets/
│   │   │   ├── knowledge/
│   │   │   ├── approvals/
│   │   │   └── analytics/
│   │   ├── hooks/
│   │   ├── layouts/
│   │   ├── pages/
│   │   ├── types/
│   │   └── main.tsx
│   ├── package.json
│   └── Dockerfile
├── knowledge/
│   └── sample-policies/
├── evaluation/
│   ├── classification_cases.jsonl
│   └── rag_cases.jsonl
├── infra/
│   └── deployment-notes.md
├── .github/
│   └── workflows/
│       └── ci.yml
├── .env.example
├── .gitignore
├── compose.yaml
├── Makefile
└── README.md
```

This is a target structure. Add files as the implementation requires them; do not create empty modules merely to match the diagram.

## Local Development Setup

### Prerequisites

Install:

- Python 3.11 or a compatible version supported by the chosen dependencies.
- Node.js LTS and npm.
- Docker Desktop with Docker Compose.
- Git.
- An API key for the selected LLM provider, if using a hosted model.

### 1. Clone the repository

```bash
git clone <your-repository-url>
cd ai-customer-operations-platform
```

### 2. Configure environment variables

Create a local `.env` from `.env.example`.

```bash
cp .env.example .env
```

On Windows PowerShell:

```powershell
Copy-Item .env.example .env
```

Update the values locally. Never commit secrets or production credentials.

### 3. Start infrastructure

```bash
docker compose up -d postgres redis
```

Ensure that the PostgreSQL image has the pgvector extension available.

### 4. Set up the backend

```bash
cd backend
python -m venv .venv
```

Activate the virtual environment.

Windows PowerShell:

```powershell
.\.venv\Scripts\Activate.ps1
```

macOS/Linux:

```bash
source .venv/bin/activate
```

Install dependencies according to the project's chosen dependency manager. For example, if the repository uses pip:

```bash
pip install -e ".[dev]"
```

Apply database migrations:

```bash
alembic upgrade head
```

Start the API:

```bash
uvicorn app.main:app --reload
```

API documentation is available at `/docs` when the development server is running.

### 5. Start the background worker

In a separate terminal, activate the same backend environment and run:

```bash
celery -A app.workers.celery_app:celery_app worker --loglevel=info
```

The Celery application path must match the actual application object in the repository.

### 6. Start the frontend

In another terminal:

```bash
cd frontend
npm install
npm run dev
```

Configure the frontend API base URL to point to the running backend.

### 7. Run the complete environment

Once the Docker Compose configuration includes all required services, the complete development environment can be started with:

```bash
docker compose up --build
```

The exact service names, ports, and commands should match the committed Compose file.

## Environment Variables

Example `.env.example`:

```dotenv
APP_ENV=development
APP_NAME=AI Customer Operations Platform
API_PREFIX=/api/v1

DATABASE_URL=postgresql+psycopg://app:app@localhost:5432/customer_ops
REDIS_URL=redis://localhost:6379/0

JWT_SECRET_KEY=replace-with-a-long-random-local-secret
ACCESS_TOKEN_EXPIRE_MINUTES=30

LLM_PROVIDER=your_provider
LLM_API_KEY=
LLM_MODEL=your-model-name

EMBEDDING_MODEL=sentence-transformers/all-MiniLM-L6-v2
EMBEDDING_DIMENSION=384

CACHE_TTL_SECONDS=300
LOG_LEVEL=INFO

FRONTEND_ORIGIN=http://localhost:5173
```

These are configuration examples, not a complete production configuration.

Important notes:

- Use a real secret-management system for deployed environments.
- The embedding dimension must match the selected embedding model and database schema.
- Model names and API keys depend on the selected provider.
- The database URL and hostnames must match the execution environment. Containers generally use Compose service names instead of `localhost` to reach other containers.
- Add a dedicated webhook signing secret and external integration credentials when those integrations are implemented.
- Never use the sample JWT secret or sample credentials in production.

## Security Considerations

Security is part of the core architecture, not a future cosmetic feature.

### Tenant Isolation
- Derive organization context from authenticated identity and verified integration credentials.
- Scope database queries by organization.
- Validate resource ownership before every read or mutation.
- Consider PostgreSQL row-level security as defense in depth.
- Test cross-tenant access attempts.

### Authentication and Authorization
- Hash passwords using a suitable password-hashing algorithm.
- Validate token signatures, expiration, issuer, and audience where applicable.
- Apply RBAC checks on privileged operations.
- Protect administrative and approval endpoints.
- Never treat an organization ID in a request as proof of authorization.

### Knowledge Security
- Restrict retrieval to authorized documents and chunks.
- Recheck source access when showing citations.
- Prevent documents from one organization entering another organization's context.
- Treat retrieved content as untrusted input.
- Do not let document instructions override system policy or application permissions.

### AI Safety
- Validate structured model output.
- Treat model classifications as suggestions rather than authorization decisions.
- Require human approval before customer-facing delivery.
- Escalate high-risk or insufficiently supported requests.
- Detect prompt injection where feasible, while relying primarily on access controls and constrained tools.
- Avoid sending unnecessary personal data to external model providers.

### Operational Security
- Validate and limit upload sizes and supported file types.
- Use parameterized database operations.
- Apply rate limiting and request-size limits.
- Keep secrets out of logs.
- Redact sensitive information from observability events.
- Record privileged actions in an audit trail.

## Caching and Background Processing

### What should be cached?

Potential candidates include:

- Repeated embedding calculations for identical, versioned content.
- Safe, reusable document retrieval results.
- Non-sensitive reference data and dashboard aggregates.

Avoid caching personalized or permission-sensitive results without including all relevant tenant, authorization, and version dimensions in the cache key.

Do not blindly cache full generated responses. A cache entry must not bypass current access checks or return stale policy information.

### Background tasks

Examples include:

- Ticket classification.
- Document parsing and embedding generation.
- Response draft generation.
- Large analytics aggregations.
- Retryable external integration calls.

Tasks should be idempotent where possible, have bounded retries, and record failures. Use exponential backoff for appropriate transient errors and distinguish retryable failures from invalid requests.

A database transaction and a separate Redis enqueue are not automatically atomic. If reliable dispatch becomes important, consider a transactional outbox pattern so committed work is not silently lost between the database write and queue publication.

## Testing Strategy

### Unit Tests
- Classification output validation.
- Routing rules and priority escalation.
- Allowed ticket state transitions.
- Citation validation.
- Permission checks.
- Cache-key construction and invalidation logic.

### Integration Tests
- PostgreSQL persistence and migrations.
- pgvector retrieval and metadata filtering.
- Redis and Celery task execution.
- Document ingestion.
- Approval and delivery state transitions.

### API Tests
- Ticket creation and retrieval.
- Authentication and RBAC.
- Cross-tenant isolation.
- Duplicate webhook handling.
- Invalid payload rejection.
- Approval requirements.
- Unauthorized access to drafts and citations.

### AI Evaluation
Maintain a labeled evaluation dataset rather than relying on a few successful demonstrations.

Measure:

- Classification precision, recall, and macro F1.
- Retrieval Recall@k and, where useful, ranking metrics such as MRR.
- Citation validity and source relevance.
- Answer faithfulness and completeness.
- Escalation accuracy.
- End-to-end latency and model cost.

Use deterministic test doubles for routine application tests. Run separate evaluation tests against actual models so provider availability and model variability do not make the entire CI pipeline unreliable.

## Analytics Definitions

Define every metric before displaying it on the dashboard.

| Metric | Definition |
|---|---|
| Ticket volume | Number of tickets created in a selected period |
| First-response time | Time from ticket creation to the first qualifying agent response |
| Resolution time | Time from creation to resolution, with reopening rules explicitly defined |
| Escalation rate | Escalated tickets divided by the eligible ticket population |
| Draft approval rate | Approved AI drafts divided by drafts submitted for review |
| Classification macro F1 | Average F1 across the defined ticket categories |
| Processing latency | Elapsed time for a defined processing stage or end-to-end workflow |
| AI failure rate | Failed AI processing attempts divided by eligible attempts |

Specify time windows, filters, exclusions, and denominators. Do not present draft approval as proof that the generated answer is factually correct.

## Deployment

### Initial Deployment

For the first hosted version, deploy:

- React frontend.
- FastAPI backend.
- Celery worker.
- Managed PostgreSQL with pgvector support.
- Managed Redis.
- Centralized application logs and error monitoring.

Docker Compose is suitable for local development. It is not, by itself, a production orchestration strategy.

### AWS Option

A possible deployment architecture is:

- ECS or another suitable container runtime for the API and worker.
- RDS PostgreSQL with a compatible pgvector extension.
- ElastiCache for Redis.
- S3 for uploaded source documents.
- Secrets Manager for application secrets.
- CloudWatch for logs, metrics, and alerts.
- An HTTPS load balancer and appropriate network restrictions.

### GCP Option

A possible deployment architecture is:

- Cloud Run or another suitable container runtime for the API and worker deployment model.
- Cloud SQL for PostgreSQL, after verifying the required pgvector support.
- Memorystore for Redis.
- Cloud Storage for uploaded documents.
- Secret Manager for credentials.
- Cloud Logging and Cloud Monitoring.

Choose one cloud provider for the initial deployment rather than implementing both simultaneously.

Production readiness additionally requires backups, recovery procedures, resource limits, database migrations, monitoring alerts, and a documented rollback process.

## Implementation Roadmap

### Phase 1 — Backend Foundation
- Configure FastAPI, PostgreSQL, SQLAlchemy, and Alembic.
- Implement organizations, users, memberships, teams, and tickets.
- Add authentication and tenant-scoped authorization.
- Build basic ticket and conversation APIs.

**Deliverable:** A secure, testable ticket management API.

### Phase 2 — Ticket Workflow
- Add ticket statuses and allowed transitions.
- Implement team routing and escalation rules.
- Add audit events.
- Support idempotent ticket ingestion.
- Build initial ticket dashboard screens.

**Deliverable:** A functioning support workflow without AI dependencies.

### Phase 3 — Knowledge and RAG
- Implement document upload and processing.
- Add text extraction, chunking, embeddings, and pgvector search.
- Enforce document access filters.
- Generate cited response drafts.
- Validate citations and add uncertainty handling.

**Deliverable:** An evidence-backed AI response assistant.

### Phase 4 — Asynchronous Processing
- Integrate Redis and Celery.
- Move expensive AI and ingestion tasks into background workers.
- Add retries, task status tracking, and caching.
- Handle duplicate events and processing failures.

**Deliverable:** An asynchronous workflow that remains responsive during slow model calls.

### Phase 5 — Human Approval
- Add draft review and editing.
- Implement approval and rejection endpoints.
- Add an authorized delivery adapter.
- Prevent unapproved replies from being sent.
- Audit approval and delivery outcomes.

**Deliverable:** A controlled AI-assisted support workflow.

### Phase 6 — Analytics and Evaluation
- Build dashboard metrics.
- Create labeled classification and retrieval test datasets.
- Evaluate model outputs and citation quality.
- Add latency, error, and cost tracking.
- Add regression tests.

**Deliverable:** A measurable system rather than a demo that only works on hand-picked examples.

### Phase 7 — Deployment
- Containerize the application.
- Add GitHub Actions for tests and quality checks.
- Deploy the API, worker, frontend, and managed dependencies.
- Configure secrets, monitoring, backups, and health checks.
- Document operational procedures.

**Deliverable:** A deployed portfolio project with reproducible setup and evidence of testing.

## Limitations

The initial version has intentionally limited scope.

- Model output can be incorrect even when it sounds confident.
- Classification quality depends on the taxonomy and evaluation data.
- Retrieval quality depends on document quality, chunking, and embedding selection.
- Human review introduces additional operational latency.
- A single relational database may not suit every high-scale deployment.
- Email, chat, and CRM integration behavior varies across external providers.
- Production use requires stronger privacy, compliance, access control, and reliability reviews than a portfolio demo.
- No performance or cost improvements should be claimed until they have been measured.

## Future Improvements

- Hybrid keyword and vector retrieval.
- Reranking for improved retrieval relevance.
- Provider-specific email and chat integrations.
- Streaming draft generation.
- SLA-aware routing and assignment.
- More granular document access policies.
- Organization-specific model and prompt configuration.
- Automated evaluation and prompt/model regression tracking.
- Dead-letter queues and transactional outbox processing.
- Advanced analytics and tenant usage limits.
- Deployment automation, load testing, and recovery testing.

## Portfolio Demonstration

A strong demonstration should show:

1. Two organizations with different teams and policies.
2. A customer ticket arriving through an API.
3. Classification and automatic team routing.
4. Relevant policy passages retrieved from the correct organization.
5. A response draft with verifiable citations.
6. An agent editing and approving the draft.
7. A recorded delivery outcome and audit event.
8. An analytics dashboard reflecting the workflow.
9. Automated tests proving that cross-tenant access is rejected.
10. Evaluation results reporting classification, retrieval, citation, and latency performance.

Use synthetic customer data and clearly identify demo integrations.

## Contributing

1. Fork the repository.
2. Create a feature branch.
3. Add or update tests.
4. Run backend and frontend checks.
5. Submit a pull request with a clear description of the change.

Keep credentials, customer data, generated secrets, and local environment files out of version control.

## License

Choose an appropriate open-source license before publishing the repository. If the project is not yet licensed, do not imply that others have permission to reuse it under a specific license.

---

**AI Customer Operations Platform** — combining LLMs, RAG, backend engineering, and human-controlled workflow automation to improve customer support operations.