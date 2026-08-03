# Context: AUTH-01 — JWT Authentication & Route Protection

## Background
The company's API is growing: endpoints serve data to the frontend, query the database, and process records. Right now, anyone who knows a URL can call any of them. Before the platform moves into its next phase, the CTO has made it clear: **no route that modifies or exposes sensitive data should be reachable without a valid session.**

### Ticket: AUTH-01 — Implement authentication and route protection
The API currently has no authentication layer. This task covers:
- A `users` module with full CRUD (create, read, update, delete).
- A login endpoint that validates credentials and returns a signed JWT token.
- A reusable `get_current_user` dependency that decodes the token and identifies the caller.
- Application of that dependency to all routes that should not be publicly accessible.

> **Note:** Once routes are protected, some frontend calls may stop working temporarily — that's expected. The frontend will be updated to send the token in subsequent work. For now, focus on securing the API to prevent data leaks and unauthorized access.

## Overview
The API currently has no authentication layer — any route can be called by anyone who knows the URL. This work adds stateless JWT-based authentication and protects all routes that modify or expose sensitive data.

**Important constraints:**
- Stateless JWT auth only. Do **not** use session-based or cookie-based authentication.
- Never store plain-text passwords. Use `passlib` with the `bcrypt` scheme for all password operations.
- Signing secret must live in `.env` — never hardcoded.

## Tech Stack
- FastAPI
- `OAuth2PasswordBearer` for token extraction
- `python-jose` for JWT signing/decoding
- `passlib` (bcrypt) for password hashing

## Data Model
`User` model with at minimum:
- `id`
- `email`
- `hashed_password`
- `is_active`
- `created_at`

## Service Layer
Implement functions for:
- create user
- get user by ID
- get user by email
- update user
- delete user

## Endpoints

### `/users`
| Method | Path | Access | Notes |
|---|---|---|---|
| POST | `/users` | public | Register a new user; hash password before storing |
| GET | `/users` | protected | List all users |
| GET | `/users/{id}` | protected | Get a single user |
| PUT | `/users/{id}` | protected | Only the user themselves or an admin |
| DELETE | `/users/{id}` | protected | Delete a user |

### `/auth`
| Method | Path | Access | Notes |
|---|---|---|---|
| POST | `/auth/login` | public | Accepts `email` and `password`, validates credentials, returns a JWT access token |
| POST | `/auth/register` | public | Creates a new user and returns a token so the caller is logged in immediately |
| GET | `/auth/me` | protected | Returns the profile of the currently authenticated user |

## How JWT Authentication Works (Mental Model)
When a user logs in, the server signs a small JSON payload (the "claims") using a secret key and returns the result as a token string. On subsequent requests, the client sends that token in the `Authorization` header. The server decodes it — if the signature is valid and the token hasn't expired, the request proceeds; if not, it gets a `401`.

In FastAPI, this flow is implemented as a dependency: a function that extracts the token from the request, validates it, and returns the user object. Any route that declares that function as a dependency automatically requires authentication.

## Token & Dependency
Implement a `get_current_user` dependency that:
1. Extracts the `Authorization: Bearer <token>` header.
2. Decodes and validates the JWT.
3. Retrieves the corresponding user from the database.
4. Raises `HTTPException(401)` if anything fails (missing header, invalid signature, expired token, user not found).

Token expiry must be configurable via an environment variable (e.g. `ACCESS_TOKEN_EXPIRE_MINUTES`).

## Route Protection
- Apply `get_current_user` as a dependency to every route that should not be publicly accessible.
- At minimum: all `/users` endpoints **except** `POST /users`, plus `/auth/me`.
- Return `401 Unauthorized` for unauthenticated requests.
- Return `403 Forbidden` when an authenticated user tries to access/modify a resource they don't own.

## Testing Checklist
- [ ] Manually verify the full flow via FastAPI's interactive docs (`/docs`): register → login → copy token → call a protected route with it.
- [ ] Confirm calling a protected route without a token returns `401`.
- [ ] Confirm calling a protected route with an expired or malformed token returns `401`.
