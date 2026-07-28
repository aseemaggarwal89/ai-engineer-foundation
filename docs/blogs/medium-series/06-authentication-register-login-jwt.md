# 06 - Authentication in FastAPI: Register, Login, JWT, and Protected Routes

📌 GitHub Repository: [AI Engineer Foundation](https://github.com/aseemaggarwal89/ai-engineer-foundation)

Authentication is one of the most important parts of backend development.

Before adding advanced AI features, I wanted to understand how users register, log in, receive access tokens, and access protected routes.

This project currently implements:

- user registration
- password hashing
- login
- JWT access-token generation
- bearer-token validation
- current-user loading
- protected routes
- role-based authorization
- lightweight audit events for successful registration and login

It does not yet implement refresh tokens, logout, token revocation, token rotation, or password-change invalidation.

Those are separate authentication lifecycle features.

## Authentication And Authorization

I used to mix these two words together.

They are related, but they are not the same.

Authentication answers:

```text
Who is making the request?
```

Authorization answers:

```text
What is that identity allowed to do?
```

Examples from this project:

- login is authentication
- JWT validation is authentication
- current-user resolution is authentication
- admin-role checking is authorization

That distinction helped me understand why protected routes need both identity and permission checks.

## Authentication Structure

The main authentication and authorization files are:

```text
app/routers/routes/auth.py
app/routers/routes/admin.py
app/domain/use_cases/user/register_user.py
app/domain/use_cases/user/login_user.py
app/domain/use_cases/user/get_current_user.py
app/security/password.py
app/security/jwt.py
app/security/security.py
app/security/dependencies.py
app/security/authorization.py
app/security/email.py
```

The auth routes live in:

```text
app/routers/routes/auth.py
```

Security helpers live in:

```text
app/security/
```

The route layer stays focused on HTTP concerns, while use cases handle application-level authentication behavior.

## Authentication Route Inventory

The current authentication-related routes are:

```text
POST /auth/register
POST /auth/login
GET  /auth/me
GET  /auth/users
GET  /admin/dashboard
```

Access levels:

```text
POST /auth/register    public
POST /auth/login       public
GET  /auth/me          authenticated
GET  /auth/users       ADMIN only
GET  /admin/dashboard  ADMIN only
```

There is no `/api/v1` prefix in the current project.

## Registration Flow

The registration endpoint is:

```http
POST /auth/register
```

The request model is:

```text
UserRegisterRequest
```

It accepts:

```json
{
  "email": "user@example.com",
  "password": "strong-password"
}
```

The password field currently requires:

```text
minimum length: 8
maximum length: 72
```

The route calls:

```text
RegisterUserUseCase
```

The verified registration flow is:

```text
request validation
-> normalize email
-> check whether email already exists
-> hash password
-> create User entity
-> persist user through repository
-> commit transaction
-> schedule registration audit event
-> return safe UserResponse
```

Email normalization is intentionally simple:

```python
email.strip().lower()
```

That behavior lives in:

```text
app/security/email.py
```

The default registered user has:

```text
role = USER
is_active = True
```

## Duplicate Email Protection

The registration use case performs an application-level duplicate check:

```text
get_by_email(normalized_email)
```

That gives a clean domain error when the email already exists.

The database also enforces uniqueness.

The `users.email` field is unique in the ORM model:

```text
app/db/models/user_orm.py
```

and the Alembic migration creates a unique email index.

This two-layer protection matters:

```text
application duplicate check
-> readable conflict error

database unique constraint
-> protection against concurrent duplicate requests
```

The repository maps database unique conflicts to a controlled `UserAlreadyExistsError`.

## Safe Registration Response

The route returns:

```text
UserResponse
```

The response contains:

```text
id
email
is_active
role
```

It does not return:

- plaintext password
- password hash
- JWT signing metadata
- audit data
- ORM internals

This is important because the ORM model contains `password_hash`, but the API response schema does not expose it.

## Password Hashing

Password utilities live in:

```text
app/security/password.py
```

The project uses:

```text
passlib CryptContext
bcrypt
```

Passwords are hashed, not encrypted.

That means the original password should not be recoverable.

The project uses:

```python
hash_password(password)
verify_password(password, password_hash)
```

Password verification uses passlib's verification function instead of custom comparison logic.

Plaintext passwords are not persisted.

Password hashes are stored in the database, but not returned through public API response schemas.

## Login Flow

The login endpoint is:

```http
POST /auth/login
```

The request model is:

```text
LoginRequest
```

It accepts:

```json
{
  "email": "user@example.com",
  "password": "strong-password"
}
```

The route calls:

```text
LoginUserUseCase
```

The verified login flow is:

```text
request validation
-> normalize email
-> load user by email
-> verify password hash
-> verify account is active
-> create JWT access token
-> schedule successful-login audit event
-> return TokenResponse
```

Token issuance now happens inside the login use case, so the route does not sign JWTs directly.

The route maps the application result to:

```text
TokenResponse
```

The response contains:

```json
{
  "access_token": "<jwt-access-token>",
  "token_type": "bearer"
}
```

## Login Error Behavior

The login flow uses a common public error for:

- unknown email
- wrong password

The client receives:

```text
Invalid email or password
```

This helps avoid unnecessary account enumeration during login.

Registration still returns a conflict when an email already exists. That is a product decision and should be reviewed depending on the application.

The login and registration routes currently use SlowAPI rate limiting through:

```text
settings.login_rate_limit
```

The project does not yet implement account lockout, progressive delays, failed-login audit records, or credential-stuffing detection.

Those are production hardening topics.

## JWT Access Tokens

JWT code lives in:

```text
app/security/jwt.py
```

The project currently uses:

```text
algorithm: HS256
expiration: settings.jwt_access_token_expire_minutes
default expiration: 30 minutes
```

The signing secret and algorithm come from settings:

```text
app/core/config.py
```

The token payload currently contains:

```json
{
  "sub": "user-id",
  "role": "USER",
  "exp": "<future-unix-timestamp>"
}
```

The `sub` claim stores the user identifier.

The `role` claim is included, but the protected route authorization flow does not rely only on this role claim.

The `exp` claim controls expiration.

The token does not currently include:

- `iat`
- `iss`
- `aud`
- `jti`
- `token_type`
- authorization version

## Signed Does Not Mean Encrypted

A normal JWT access token is signed, not encrypted.

The signature protects token integrity.

It prevents someone from modifying claims without the signing secret.

But the payload may still be readable by anyone who has the token.

That means JWT claims should not contain:

- passwords
- secrets
- API keys
- private profiles
- provider credentials
- confidential personal information

Keep token claims minimal.

## JWT Validation

The project validates tokens in:

```text
app/security/jwt.py
```

The current validation checks:

- cryptographic signature
- configured algorithm allow-list
- expiration
- presence of `exp`

The subject claim is checked later in:

```text
app/security/dependencies.py
```

If `sub` is missing, authentication fails.

Issuer and audience validation are not currently implemented because the project does not configure `iss` or `aud` claims yet.

Invalid, malformed, expired, or missing tokens are mapped to a controlled `401` response.

## Bearer Token Transport

Clients send the token using:

```http
Authorization: Bearer <token>
```

The project uses FastAPI's:

```text
HTTPBearer
```

from:

```text
app/security/security.py
```

The project does not currently use cookies for auth, so browser cookie concerns such as `HttpOnly`, `Secure`, `SameSite`, and CSRF are outside this implementation phase.

## Protected Route Flow

Protected routes use dependencies from:

```text
app/security/dependencies.py
```

The verified flow is:

```text
extract bearer token
-> decode and validate JWT
-> read sub claim
-> load user from database
-> verify user exists
-> verify user is active
-> return current User
```

The current user is loaded from the database for protected routes.

That has a useful security benefit:

```text
role and active status are checked against current database state
```

The trade-off is that protected requests perform a database lookup.

For this learning project, that is a good trade-off because it avoids trusting stale token claims for authorization.

## Current User Endpoint

The endpoint:

```http
GET /auth/me
```

requires authentication.

It returns:

```text
UserResponse
```

That response schema excludes:

- password hash
- raw JWT
- token metadata
- audit records
- ORM internals

## Role-Based Authorization

Authorization logic lives in:

```text
app/security/authorization.py
```

The project defines roles in:

```text
app/domain/entities/user_role.py
```

Current roles:

```text
USER
ADMIN
```

Admin-only routes use:

```python
Depends(require_role(UserRole.ADMIN))
```

Current admin-protected routes:

```text
GET /auth/users
GET /admin/dashboard
```

Authorization runs against the current database-loaded user, not only against the role claim inside the JWT.

That reduces stale-role risk.

For example:

```text
token says ADMIN
database user is now USER
authorization sees USER
request is rejected
```

The project does not yet implement resource ownership, tenant membership, permission policies, or object-level authorization.

Role checks provide broad access control. Resource-level operations may still require ownership, tenant, or permission checks.

## `401` Versus `403`

This project uses the normal distinction:

```text
401 Unauthorized
-> authentication is missing, invalid, expired, or inactive

403 Forbidden
-> identity is valid, but permission is insufficient
```

Examples:

```text
missing bearer token -> 401
invalid token -> 401
non-admin user calling admin route -> 403
```

One production improvement would be adding a `WWW-Authenticate: Bearer` header consistently for `401` responses.

## Audit Logging

Registration and successful login schedule audit records using FastAPI background tasks.

The route adds tasks like:

```text
audit_service.log_event(...)
audit_service.log_login(...)
```

Audit records are stored through:

```text
AuditService
AuditRepository
AuditORM
```

Current authentication audit behavior:

```text
successful registration -> audited
successful login -> audited
failed login -> logged, but not stored as an audit event
```

The current implementation uses lightweight in-process background tasks.

That is useful for learning and local development, but it is not compliance-grade durable audit infrastructure.

A stronger production design would need:

- durable queue
- retries
- monitoring
- dead-letter handling
- delivery guarantees
- explicit retention policy

Audit records should never include:

- plaintext passwords
- password hashes
- full bearer tokens
- JWT signing secrets
- provider API keys
- raw authorization headers

For future AI audit logging, safer metadata could include:

- request ID
- user ID
- operation
- provider
- model
- status
- latency
- token usage
- safety outcome
- prompt-template version

Raw prompts and responses may contain personal or confidential data.

They should be stored only with explicit redaction, encryption, access control, retention, and compliance policies.

## AI Endpoint Security

As explained in Blog 05, the summarization endpoint is currently public:

```http
POST /ai/summarize
```

That is acceptable for local learning and development.

For production, an AI endpoint usually needs stronger controls:

- authentication
- rate limits
- quotas
- request-size limits
- provider budget controls
- timeout handling
- concurrency limits
- abuse monitoring

Authentication gives identity and attribution, but it is only one part of production AI access control.

## What I Learned

Authentication is not separate from AI engineering.

For enterprise AI applications, authentication becomes the foundation for:

- controlled access
- user-level usage tracking
- auditability
- provider-cost management
- role-based administration
- future billing or quota systems

The biggest lesson for me was:

```text
Do not put all security logic in the route.
Keep routes as HTTP boundaries.
Move authentication workflow into use cases and security utilities.
Use safe response schemas.
Never expose passwords, hashes, secrets, or full tokens in logs.
```

## Next

After authentication, the next topic is dependency injection and how FastAPI wires routes, use cases, repositories, services, and AI infrastructure together.
