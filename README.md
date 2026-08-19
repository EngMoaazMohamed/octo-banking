# Octo Banking

Training project: a banking backend split into two Django microservices.

## Architecture

| Service | Port | Responsibility |
|---|---|---|
| `auth_service` | 8000 | User signup/login, issues JWT tokens |
| `transactions_service` | 8001 | Bank accounts, loans, installments, payments |

The transactions service verifies JWTs **statelessly** using a signing key
shared with the auth service — no user database duplication, no
service-to-service calls.

## Features

- Bank account CRUD (scoped to the authenticated user via JWT)
- Loan creation with two auto-generated installments (atomic)
- Installment payment with balance checks
- Thread-safe payments: `select_for_update` + `transaction.atomic`
  prevent double-spending under concurrent requests
- Swagger docs at `/api/docs/` on both services
- 18 unit tests, including auth tests (401 without/invalid token)
  and a threaded concurrency test

## Run locally

```bash
# Auth service
cd auth_service
poetry install
poetry run python manage.py migrate
poetry run python manage.py runserver 8000

# Transactions service (second terminal)
cd transactions_service
poetry install
poetry run python manage.py migrate
poetry run python manage.py runserver 8001
```

## Tests

```bash
poetry run python manage.py test   # inside each service
```

## Notes

- Signing keys are hardcoded for simplicity; in production they would
  be environment variables (or RS256 key pairs).
- SQLite is used for development/tests; production would use PostgreSQL,
  where `select_for_update` performs true row-level locking.
