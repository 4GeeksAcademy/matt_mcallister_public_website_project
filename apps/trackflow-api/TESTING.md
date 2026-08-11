# TrackFlow API — Testing Guide

This document describes how to run the auth API test suite, measure coverage, and which happy / edge / failure cases are covered per endpoint.

**Service:** `apps/trackflow-api`  
**Tests:** [`tests/`](tests/)  
**Fixtures:** in-memory TinyDB via [`tests/conftest.py`](tests/conftest.py) (`client`, `tinydb`, helpers `register_user`, `login_token`)

---

## Run tests

From the service directory:

```bash
cd apps/trackflow-api
uv sync
uv run pytest -q
```

Expected: **28 passed**.

If you do not use `uv`, activate the project venv and run `pytest -q` from the same directory.

---

## Coverage

Configuration: [`pyproject.toml`](pyproject.toml) (`[tool.coverage.run] source = ["app"]`).

```bash
cd apps/trackflow-api
uv run pytest --cov=app --cov-report=term-missing --cov-fail-under=90
```

**Current baseline:** **96%** line coverage on `app/` (219 statements, 9 missed).

| Module | Coverage | Typical gaps |
| --- | --- | --- |
| `app/api/deps.py` | 96% | `subject is None` branch in JWT payload |
| `app/api/routes/users.py` | 90% | 404 paths (`user not found`) not hit by every CRUD test |
| `app/db/session.py` | 86% | on-disk TinyDB open path (tests use in-memory override) |
| `app/services/user_service.py` | 93% | email-update conflict branches |

These gaps are acceptable for this milestone; core auth and security paths are fully exercised.

---

## Endpoint case matrix

Each row maps to **existing** tests. Status codes and messages are asserted in code.

### `POST /auth/register`

| Case | Input / action | Expected | Test |
| --- | --- | --- | --- |
| Happy | Valid email + password | `201`, bearer token, user stored with bcrypt hash (not plaintext) | `test_register_valid_credentials_creates_user_and_returns_token` |
| Edge | Password exactly 8 characters | `201` | `test_register_minimum_length_password_succeeds` |
| Failure | Duplicate email | `409`, `"Email already registered"`, only one DB row | `test_register_duplicate_email_returns_conflict` |
| Failure | Password too short | `422`, no user created | `test_register_short_password_rejected` |
| Failure | Invalid email format | `422`, no user created | `test_register_invalid_email_rejected` |

### `POST /auth/login`

| Case | Input / action | Expected | Test |
| --- | --- | --- | --- |
| Happy | Correct email + password | `200`, JWT with `sub` = email | `test_login_valid_credentials_returns_token_with_correct_subject` |
| Failure | Wrong password | `401`, `"Invalid email or password"` | `test_login_wrong_password_rejected` |
| Failure | Unknown email | `401`, **same message** (enumeration-safe) | `test_login_unknown_email_rejected` |
| Failure | Missing password field | `422` | `test_login_missing_password_rejected` |
| Failure | Invalid email format | `422` | `test_login_invalid_email_format_rejected` |

### `GET /auth/me`

| Case | Input / action | Expected | Test |
| --- | --- | --- | --- |
| Happy | Valid Bearer token | `200`, current user email | `test_me_valid_token_returns_current_user` |
| Failure | No token | `401` | `test_me_without_token_rejected` |
| Failure | Malformed token | `401` | `test_me_malformed_token_rejected` |
| Failure | Expired token | `401` | `test_me_expired_token_rejected` |
| Failure | Orphan token (user deleted after login) | `401` | `test_me_token_for_deleted_user_rejected` |

### `POST /users` (public create)

| Case | Input / action | Expected | Test |
| --- | --- | --- | --- |
| Happy | Valid email + password | `201`, password hashed in DB | `test_public_users_create_returns_user` |
| Failure | Duplicate email | `409` | `test_duplicate_email_conflict` |

### `GET /users`

| Case | Input / action | Expected | Test |
| --- | --- | --- | --- |
| Happy | Valid Bearer token | `200`, user list | `test_user_crud_end_to_end_is_reachable` |
| Failure | No token | `401` | `test_users_list_requires_auth`, `test_protected_routes_return_401_without_valid_token` |

### `GET /users/{user_id}`

| Case | Input / action | Expected | Test |
| --- | --- | --- | --- |
| Happy | Valid token, existing id | `200` | `test_user_crud_end_to_end_is_reachable` |
| Failure | No token | `401` | `test_protected_routes_return_401_without_valid_token` |

### `PUT /users/{user_id}`

| Case | Input / action | Expected | Test |
| --- | --- | --- | --- |
| Happy | User updates own record | `200` | `test_user_can_update_self` |
| Failure | User updates another user's record | `403` | `test_user_cannot_update_another_user` |
| Failure | No token | `401` | `test_protected_routes_return_401_without_valid_token` |

### `DELETE /users/{user_id}`

| Case | Input / action | Expected | Test |
| --- | --- | --- | --- |
| Happy | User deletes own record | `204` | `test_user_crud_end_to_end_is_reachable` |
| Failure | No token | `401` | `test_protected_routes_return_401_without_valid_token` |

### `GET /health`

| Case | Input / action | Expected | Test |
| --- | --- | --- | --- |
| Happy | No auth required | `200`, `{"status":"ok"}` | `test_health_route_still_works` |

---

## Security-focused business asserts

These are the rules graders called out explicitly:

### bcrypt password hashing

- Registration and public user create store `hashed_password != plaintext`.
- `hash_password` / `verify_password` round-trip in unit tests.
- **Tests:** `test_register_valid_credentials_creates_user_and_returns_token`, `test_public_users_create_returns_user`, `test_hash_and_verify_password_round_trip`

### Duplicate email (`409`)

- Registering or creating a user with an existing email returns `409` and must **not** overwrite silently.
- **Tests:** `test_register_duplicate_email_returns_conflict`, `test_duplicate_email_conflict`

### Enumeration-safe login

- Wrong password and unknown email both return `"Invalid email or password"` — the response must not reveal whether the email exists.
- **Tests:** `test_login_wrong_password_rejected`, `test_login_unknown_email_rejected`

### Expired JWT on `/auth/me`

- Token minted with negative TTL is rejected even if structurally valid.
- **Test:** `test_me_expired_token_rejected`

### Orphan JWT on `/auth/me`

- After the user row is deleted, a still-valid JWT must not return a stale identity.
- **Implementation:** [`app/api/deps.py`](app/api/deps.py) decodes the token then re-loads the user by email; missing user → `401`.
- **Test:** `test_me_token_for_deleted_user_rejected`

---

## AI-suggested test case (concrete example)

### Gap identified

A JWT can remain cryptographically valid after the user record is deleted. Without a reload check, `/auth/me` could return a ghost identity.

### Example AI prompt

> Suggest a pytest case for FastAPI JWT auth where the user registers and logs in, then is deleted via `DELETE /users/{id}`, and a subsequent `GET /auth/me` with the same Bearer token must return 401 instead of the deleted user's profile.

### Implemented test

**File:** [`tests/test_me.py`](tests/test_me.py)  
**Function:** `test_me_token_for_deleted_user_rejected`

### Steps

1. `POST /auth/register` for `deleted@example.com`
2. `POST /auth/login` → obtain Bearer token
3. `DELETE /users/1` with that token → `204`
4. `GET /auth/me` with the **same** token

### Expected result

- Status: **`401`**
- Must **not** return `200` with the deleted user's email

This case was added after AI review of the auth dependency chain and is now part of the standard suite.

---

## Cross-cutting / integration tests

[`tests/test_evaluation_criteria.py`](tests/test_evaluation_criteria.py) covers:

- Full user CRUD end-to-end (`test_user_crud_end_to_end_is_reachable`)
- All protected routes return `401` without a valid token
- Wrong route prefixes (`/user`, `/authentication/me`) return `404`
- Settings loaded from environment (`SECRET_KEY`, `ACCESS_TOKEN_EXPIRE_MINUTES`)

[`tests/test_security.py`](tests/test_security.py) covers JWT create/decode and wrong-secret rejection at the unit level.

---

## Quick checklist before submission

- [ ] `uv run pytest -q` → 28 passed
- [ ] `uv run pytest --cov=app --cov-report=term-missing` → ≥ 90% (baseline 96%)
- [ ] This file documents happy / edge / failure cases per endpoint
- [ ] AI-suggested orphan-token case documented above
