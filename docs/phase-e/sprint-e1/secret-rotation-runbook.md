# AQAA Sprint E1 — Secret Rotation & Revocation Runbook

## Secrets Managed by AQAA

| Secret | Location | Rotation Frequency |
|--------|----------|--------------------|
| `SECRET_KEY` (JWT signing) | `.env` / env var | Annually or on compromise |
| `METRICS_API_KEY` | `.env` / env var | Quarterly |
| `DATABASE_URL` password | `.env` / env var | On personnel change |
| `REDIS_URL` password | `.env` / env var | On personnel change |
| `QDRANT_API_KEY` | `.env` / env var | On personnel change |
| AI provider API keys | `.env` / env var | Provider-recommended schedule |

## Rotating SECRET_KEY

Rotating the JWT signing key **immediately invalidates all issued tokens** — all users will be logged out.

```bash
# 1. Generate new key
python3 -c "import secrets; print(secrets.token_hex(64))"

# 2. Update SECRET_KEY in .env (or secrets manager)
# 3. Restart backend and worker
docker compose restart backend worker

# 4. Verify liveness
curl http://localhost:8000/health
```

Token revocation via the deny-list (`POST /api/v1/auth/logout`) remains valid for
the TTL of each token after the key is rotated, since old tokens can no longer be
decoded at all.

## Revoking a Single JWT (without key rotation)

Use the logout endpoint from the affected session:

```bash
curl -X POST http://localhost:8000/api/v1/auth/logout \
  -H "Authorization: Bearer <token>"
```

The `jti` claim is written to Redis with TTL = remaining token lifetime.

## Rotating Database Password

```bash
# 1. Update password in PostgreSQL
docker compose exec postgres psql -U aqaa -c \
  "ALTER USER aqaa PASSWORD 'new-password';"

# 2. Update DATABASE_URL in .env
# 3. Restart backend and worker
docker compose restart backend worker
```

## Rotating AI Provider API Keys

1. Revoke the old key in the provider's dashboard.
2. Update the relevant env var (e.g. `OPENAI_API_KEY`, `ANTHROPIC_API_KEY`) in `.env`.
3. Restart backend: `docker compose restart backend worker`.
4. Verify that the AI assistant endpoint responds correctly.

## Security Incident — Full Credential Rotation

If credentials are suspected to be compromised:

```bash
# 1. Immediately rotate SECRET_KEY (invalidates all sessions)
# 2. Rotate database password
# 3. Rotate Redis password
# 4. Rotate all AI provider keys
# 5. Rotate METRICS_API_KEY
# 6. Review logs for unauthorised access
# 7. Notify institution security officer

# After rotation, verify no old credentials remain in:
grep -r "ChangeMe\|your-secret\|change-me" --include="*.env*" .
```

## What Must Never Be Committed

- Any `.env` file with real values
- Database passwords in docker-compose YAML
- API keys in Python source or test files
- Secrets in log output or screenshots

The CI pipeline checks for known-default patterns and fails the build if found.
