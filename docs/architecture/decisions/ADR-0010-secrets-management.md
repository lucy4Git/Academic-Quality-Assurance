# ADR-0010 — Secrets Management Approach

**Date:** 2026-07-17
**Status:** PROPOSED
**Author:** AQAA Engineering
**Deciders:** AQAA Engineering — Principal Systems Architect

---

## Context

Phase D stores all configuration (including secrets: `SECRET_KEY`, `DATABASE_URL`, AI provider API keys) in `backend/.env`. This file is excluded from git via `.gitignore`. In development this is acceptable, but for pilot and production deployment:

1. `.env` files are not suitable for secrets in a shared server environment (readable by all users with server access)
2. Secrets rotation requires editing a file on the server with no audit trail
3. No distinction between non-sensitive config (port numbers, feature flags) and sensitive secrets (credentials, keys)

The chosen approach must work within AQAA's Docker Compose deployment model and single-server pilot constraint.

---

## Options Considered

### Option A — Docker Secrets (Docker Compose `secrets:` syntax)

- Secrets mounted as files at `/run/secrets/{name}` inside the container
- Secrets files stored outside the image and compose file
- Supported natively by Docker Compose v3+
- Does not require third-party tooling
- Secrets not visible in `docker inspect` of running container
- Limitation: managing many secrets files manually requires discipline

### Option B — HashiCorp Vault

- Industry-standard secret store with audit log, dynamic secrets, rotation
- Overkill for a single-server pilot
- Requires a separate Vault server process
- Significant operational overhead for a small team

### Option C — AWS Secrets Manager / Azure Key Vault

- Managed SaaS, excellent audit trail, rotation support
- Requires cloud provider dependency
- Adds cost; incompatible with self-hosted single-server pilot model
- Could be adopted in Phase F if cloud deployment is chosen

### Option D — Continue using `.env` file (no change)

- Pilot blocker gap SEC-03 remains open
- Secrets visible in server filesystem to any user with read access

---

## Decision

**Option A — Docker Secrets** for production and pilot; `.env` file retained for development only.

### Rationale

1. **No new infrastructure**: Docker secrets are a native Docker Compose feature. No additional services, no cloud dependency.

2. **Pilot-appropriate**: For a single-server pilot, Docker secrets provide meaningful improvement over `.env` files without the complexity of Vault.

3. **Separation of sensitive and non-sensitive config**: Non-sensitive config (feature flags, URLs without credentials, log levels) remains in environment variables. Only credentials and keys use Docker secrets.

4. **Clear upgrade path**: In Phase F, if AQAA moves to Kubernetes, secrets become `k8s Secrets` with the same mount-as-file pattern. If cloud deployment is chosen, AWS Secrets Manager can replace Docker secrets with minimal code change (only the `read_secret()` helper in `config.py` needs updating).

### Implementation Pattern

`config.py` is updated with a `read_secret()` helper:

```python
def read_secret(name: str, env_var: str) -> str:
    secret_file = f"/run/secrets/{name}"
    if os.path.exists(secret_file):
        return Path(secret_file).read_text().strip()
    value = os.environ.get(env_var)
    if not value:
        raise ValueError(f"Secret '{name}' not found as file or env var '{env_var}'")
    return value
```

`docker-compose.prod.yml` declares secrets:
```yaml
secrets:
  secret_key:
    file: ./secrets/secret_key.txt
  database_url:
    file: ./secrets/database_url.txt
  ...
services:
  backend:
    secrets: [secret_key, database_url, ...]
```

The `secrets/` directory is:
- Created on the server by the deploy operator
- Listed in `.gitignore`
- Never committed to git
- Backed up separately from code

### Accepted Trade-offs

- Secrets files on disk are slightly less secure than in-memory Vault tokens; mitigated by strict file permissions (`chmod 400`)
- No automated rotation in Phase E; rotation is a manual operational procedure documented in the runbook
- If AQAA Engineering team grows, Vault or a managed KMS should be adopted in Phase F

---

**Decision recorded by:** AQAA Engineering — 2026-07-17
