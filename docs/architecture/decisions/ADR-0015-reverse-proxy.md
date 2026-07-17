# ADR-0015 — Reverse Proxy for TLS Termination

**Date:** 2026-07-17
**Status:** PROPOSED
**Author:** AQAA Engineering
**Deciders:** AQAA Engineering — Principal Systems Architect

---

## Context

Phase D has no TLS termination. The FastAPI backend is accessed directly on HTTP :8000 and the Next.js frontend on HTTP :3000. Phase E requires HTTPS for all production and pilot traffic (SEC-02, E-SEC-001).

---

## Options Considered

### Option A — Caddy

- Automatic HTTPS via Let's Encrypt (zero-config TLS certificate provisioning)
- Single `Caddyfile` for routing configuration
- Native Docker Compose integration
- Automatic certificate renewal
- Lighter than nginx for simple reverse proxy use cases
- Smaller community than nginx; fewer StackOverflow answers

### Option B — nginx

- Industry standard; largest community
- Manual certificate management via Certbot + cron job
- More configuration to achieve what Caddy does automatically
- `nginx.conf` more verbose than `Caddyfile` for the same outcome
- Excellent for complex routing, rate limiting at proxy layer, custom headers

### Option C — Traefik

- Docker-native; discovers services via container labels
- Automatic HTTPS via Let's Encrypt
- More complex configuration than Caddy for simple setups
- Overhead at pilot scale is unnecessary

---

## Decision

**Caddy (Option A).**

### Rationale

1. **Zero-config TLS**: Caddy provisions and renews Let's Encrypt certificates automatically. nginx + Certbot requires a cron job and periodic manual verification. For a small team running a pilot, the operational simplicity of Caddy is significant.

2. **Single file configuration**: The Caddyfile for AQAA's two upstreams (frontend :3000, backend :8000) is ~20 lines. Equivalent nginx config with SSL is significantly more verbose.

3. **HTTPS by default**: Caddy enforces HTTPS and redirects HTTP to HTTPS automatically. nginx requires explicit `return 301 https://$host$request_uri` configuration.

4. **Security headers**: Caddy's `header` directive cleanly sets HSTS, X-Frame-Options, CSP, and X-Content-Type-Options.

### Caddyfile (target)

```
{
  email admin@aqaa.example
}

aqaa.example {
  header Strict-Transport-Security "max-age=31536000; includeSubDomains"
  header X-Frame-Options "SAMEORIGIN"
  header X-Content-Type-Options "nosniff"
  header Content-Security-Policy "default-src 'self'; script-src 'self'; style-src 'self' 'unsafe-inline';"

  # API requests → FastAPI backend
  handle /api/* {
    reverse_proxy backend:8000
  }

  # Prometheus metrics (internal only — restrict by IP if needed)
  handle /metrics {
    reverse_proxy backend:8000
  }

  # Frontend → Next.js
  reverse_proxy frontend:3000
}
```

### Accepted Trade-offs

- Caddy's rate limiting plugin is a third-party module; rate limiting is implemented in FastAPI (`slowapi`) rather than at the proxy layer
- If AQAA moves to Kubernetes in Phase F, nginx Ingress Controller is the standard choice; Caddy would be replaced there

---

**Decision recorded by:** AQAA Engineering — 2026-07-17
