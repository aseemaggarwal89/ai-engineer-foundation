# Authentication in FastAPI: Register, Login, JWT, and Protected Routes

Authentication is one of the most important parts of backend development.

Before adding advanced AI features, I wanted to understand how users register, log in, and access protected routes.

This project implements:

- user registration
- password hashing
- login
- JWT token generation
- current user loading
- protected routes
- role-based authorization

## Registration Flow

The registration endpoint is:

```http
POST /auth/register
```

The user sends:

```json
{
  "email": "user@example.com",
  "password": "strong-password"
}
```

The route calls:

```text
RegisterUserUseCase
```

The use case:

```text
checks if email already exists
-> hashes password
-> creates user entity
-> saves user through repository
-> schedules audit log
```

## Password Hashing

Passwords should never be stored directly.

The project stores password hashes.

Password utilities live in:

```text
app/security/password.py
```

This teaches an important backend rule:

> Store password hashes, not passwords.

## Login Flow

The login endpoint is:

```http
POST /auth/login
```

The user sends:

```json
{
  "email": "user@example.com",
  "password": "strong-password"
}
```

The login use case:

```text
loads user by email
-> verifies password
-> checks account is active
-> returns user
```

Then the route creates a JWT access token.

## JWT Token

JWT code lives in:

```text
app/security/jwt.py
```

The token contains:

```json
{
  "sub": "user-id",
  "role": "user",
  "exp": 1760000000
}
```

The `sub` claim stores the user identifier.

The `role` claim helps with authorization.

The `exp` claim controls expiration.

## Protected Route Flow

For protected routes, the client sends:

```http
Authorization: Bearer <token>
```

Security dependencies:

```text
decode token
-> read user id from sub
-> load current user
-> check user is active
```

These dependencies live in:

```text
app/security/dependencies.py
app/security/security.py
```

## Current User Endpoint

The endpoint:

```http
GET /auth/me
```

returns the authenticated user's profile.

This is a common endpoint in real applications.

## Role-Based Authorization

Admin routes require an admin role.

Authorization logic lives in:

```text
app/security/authorization.py
```

Example:

```python
Depends(require_role(UserRole.ADMIN))
```

This protects endpoints such as:

```text
GET /admin/dashboard
GET /auth/users
```

## Audit Logging

Registration and login schedule background audit events.

Audit logging is useful for:

- security
- debugging
- compliance
- user activity history

In enterprise AI systems, audit logging can later be extended to track:

- AI prompts
- model usage
- provider selection
- errors
- user-level usage

## Why Authentication Matters For AI Backends

AI features often cost money.

If an AI endpoint is public, anyone can use provider tokens and compute.

Authentication helps with:

- access control
- user-level rate limits
- usage tracking
- billing
- auditability
- abuse prevention

## What I Learned

Authentication is not separate from AI engineering.

For enterprise AI applications, authentication becomes the foundation for secure and controlled model usage.

## Next

After authentication, the next topic is dependency injection and how the project wires routes, use cases, repositories, and AI services.

