# aequatio
A better Expense overview

## Aequatio — Solution Design

Summary
- Aequatio is an event-driven CQRS system to gather expenses, assign them to users, and monthly split expenses across a group (Family).
- Tech: FastAPI, SQLAlchemy + Alembic, PostgreSQL, RabbitMQ, Pydantic, GitHub Actions → AWS.
- Goals: correctness, auditable events, easy evolution (schema/versioning), idempotent consumers, observable operations.

Principles
- Events are first-class: immutable, versioned, validated, stored (or referenced), and published.
- Single responsibility: command handlers produce events; projections/read models are derived from events.
- Keep domain logic in the write model; reads are optimized for queries.
- Tolerant consumers: additive changes only, explicit versioning for incompatible changes.
- Use correlation/trace ids for observability and idempotency keys for dedupe.

High-level architecture
- Clients -> HTTP API (FastAPI) -> Command handlers -> Persist authoritative state (Postgres) + publish domain events to RabbitMQ -> Consumers/Projections/Sagas listen -> Update read models, trigger side effects (invoices, notifications), or external integrations.
- Optional: event store (append-only) for full history; otherwise persist events in Postgres events table.

Components
1. API (FastAPI)
   - Receive commands (add_expense, amend_expense, create_group, request_split, create_invoice).
   - Validate and authorize requests.
   - Dispatch commands to domain/application service.

2. Write model (Domain + SQLAlchemy)
   - SQL tables for canonical aggregates (Expense, User, Group).
   - Transactions: apply change to aggregate, persist state, and persist domain events in same transaction (Outbox pattern if using separate broker).

3. Outbox + Message broker
   - Use Outbox table (Postgres) to store events atomically with aggregate changes.
   - A separate outbox dispatcher publishes events to RabbitMQ and marks them delivered.

4. Message broker (RabbitMQ)
   - Exchanges by purpose: domain-events (topic), commands (direct if needed), notifications.
   - Routing key: <bounded_context>.<aggregate>.<event> (e.g. expenses.expense.created).
   - Use headers for schema_id, event_version, correlation_id.

5. Projections / Read models (CQRS)
   - Lightweight services or workers that consume domain-events and update read-optimized tables (e.g., monthly balances, group-summary).
   - Read models stored in Postgres (separate schema) or in a read-optimized store (Elasticsearch, Redis) if needed.

6. Sagas / Process Managers
   - Long-running workflows (Split expenses, Create invoice) implemented as sagas reacting to multiple events, persisting saga state, emitting follow-up commands or events.
   - Implement idempotency & compensations for failures.

Data model (canonical)
- users (id, name, email, created_at, ...).
- groups (id, name, owner_id, created_at).
- group_members (group_id, user_id, role, joined_at).
- expenses (id, group_id, created_by, amount_cents, currency, description, created_at, amended_at, status).
- invoices (id, group_id, period_start, period_end, lines_json, total_cents, status).
- events_outbox (id, aggregate_type, aggregate_id, event_type, event_version, payload_json, occurred_at, published_at).
- events_store (optional append-only event store with same fields above).

Event design & schema guidelines
- Use an envelope containing metadata + payload.
- Metadata: event_id, event_type, aggregate_type, aggregate_id, version, occurred_at, correlation_id, trace_id, schema_id.
- Payload: strongly typed via Pydantic (or Avro/Protobuf for compact/strict schema).

Pydantic envelope example (use in codebase for schema generation and validation)

Example domain events to define and version
- expense.created v1 {expense_id, group_id, amount_cents, currency, created_by, description}
- expense.amended v1 {expense_id, changes, amended_by, amended_at}
- group.created v1 {group_id, name, owner_id, members[]}
- split.requested v1 {group_id, period_start, period_end, requested_by}
- split.completed v1 {group_id, period_start, period_end, per_user_amounts[]}
- invoice.created v1 {invoice_id, group_id, period_start, period_end, lines, total}

Event versioning policy
- Minor (non-breaking): add optional fields.
- Major (breaking): increment version and publish new schema_id; consumers need migration logic.
- Always include schema_id in metadata to allow lookup in registry.

RabbitMQ routing & topology
- Exchanges:
  - domain.events (topic): route by routing key: <context>.<aggregate>.<event> e.g. expenses.expense.created
  - commands (direct): for point-to-point commands
- Queues:
  - projection.<name> bound to domain.events with appropriate routing keys.
  - saga.<name> for long-running workflows.
- Message headers: schema_id, event_version, correlation_id, trace_id, idempotency_key.

Reliability patterns
- Outbox + transactional DB writes to avoid lost events.
- Retry with exponential backoff for publishing and consuming.
- Idempotency on consumers (store processed_event_ids).
- Poison queue handling for messages failing repeatedly.

Security & auth
- HTTP: OAuth2 / JWT with scopes. FastAPI dependencies for auth.
- Broker: TLS + user accounts, fine-grained vhost/queue permissions.
- DB: encrypted at rest, least-privilege DB users for services.

Observability
- Structured logs (JSON) including event ids and correlation ids.
- Tracing: OpenTelemetry (trace_id propagated via metadata and headers).
- Metrics: events published, consumed, processing latency, outbox lag.
- Dashboards/alerts in CloudWatch/Prometheus+Grafana.

Deployment & CI/CD
- GitHub Actions:
  - Lint, type-check, unit tests, integration tests (containerized Postgres + RabbitMQ).
  - Build container images; push to ECR.
  - Infrastructure via Terraform/CloudFormation (VPC, ECS/EKS, RDS Postgres, RabbitMQ via AWS MQ or self-managed).
  - Blue/green or rolling deploys; migrations (Alembic) run as pre-deploy job with migration safety checks.
- Environments: dev, staging, prod.

Testing strategy
- Unit tests for domain logic, Pydantic schemas, and command handlers.
- Integration tests with ephemeral Postgres + RabbitMQ (use pytest fixtures, testcontainers on CI).
- Contract tests for event schemas (producer publishes schema; consumer validates).
- End-to-end tests for core flows (add expense -> split -> invoice).

Developer workflows & repo layout (suggested)
- aequatio/app/
  - api/ (FastAPI routes)
  - domain/ (entities, services)
  - events/ (Pydantic event schemas)
  - persistence/ (sqlalchemy models, migrations)
  - projections/ (read model updaters)
  - sagas/ (process managers)
  - outbox/ (dispatcher)
  - tests/
- schemas/ (JSON schema artifacts, schema registry data)

Migration & backwards compatibility
- Keep fields optional where possible.
- Provide translation layers for older event versions (adapters).
- Maintain schemas/ directory and painless tooling to register schemas.

Next steps / priorities
1. Define canonical event list with payload schemas (Pydantic) and add to schemas/.
2. Implement Outbox pattern + transactional write in one service (add tests).
3. Implement basic API endpoints, command handlers for add/amend expense and group lifecycle.
4. Create projection for group monthly balance and a saga for splitting expenses.
5. Add CI for schema validation and integration tests.

References / further reading
- Outbox pattern / transactional messaging
- Event versioning patterns (semantic versioning for events)
- Sagas and process managers
- Pydantic / JSON Schema / schema registries
