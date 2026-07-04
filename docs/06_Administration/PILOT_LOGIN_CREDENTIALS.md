# AQAA Pilot Login Credentials

**Classification:** Internal — Pilot Use Only  
**Version:** 1.0.0  
**Date:** 2026-07-02  
**Environment:** Local Development / Pilot

> All passwords below are the shared default set at seed time.
> Every user must change their password after first login before any real data is entered.
> Do NOT use these credentials in any shared, staging, or production environment.

---

## System Users

| Full Name | Role | Institution | Email | Password | Status |
|-----------|------|-------------|-------|----------|--------|
| System Admin | System Admin | All Institutions | `admin@test.com` | `ChangeMe123!` | Active |

---

## Tshwane University of Technology (TUT) — Pilot

| Full Name | Role | Email | Password | Status |
|-----------|------|-------|----------|--------|
| Ms. Nomsa Dlamini | QA Officer | `qa.officer@tut.ac.za` | `ChangeMe123!` | Active |
| Prof. Sipho Nkosi | Faculty Dean | `dean.ict@tut.ac.za` | `ChangeMe123!` | Active |
| Dr. Thabo Molefe | Head of Department | `hod.cs@tut.ac.za` | `ChangeMe123!` | Active |
| Mr. Bongani Zulu | Programme Coordinator | `coordinator.it@tut.ac.za` | `ChangeMe123!` | Active |
| Ms. Zanele Khumalo | Lecturer | `lecturer.cs@tut.ac.za` | `ChangeMe123!` | Active |
| Lerato Mokoena | Student | `student.cs@tut.ac.za` | `ChangeMe123!` | Active |

---

## University of Pretoria (UP) — Pilot

| Full Name | Role | Email | Password | Status |
|-----------|------|-------|----------|--------|
| Dr. Claudia van der Merwe | QA Officer | `qa.officer@up.ac.za` | `ChangeMe123!` | Active |
| Prof. Johan Pretorius | Faculty Dean | `dean.ebit@up.ac.za` | `ChangeMe123!` | Active |
| Dr. Anita Botha | Head of Department | `hod.cs@up.ac.za` | `ChangeMe123!` | Active |
| Mr. Pieter du Plessis | Programme Coordinator | `coordinator.bsccs@up.ac.za` | `ChangeMe123!` | Active |
| Ms. Liezel Steyn | Lecturer | `lecturer.cos@up.ac.za` | `ChangeMe123!` | Active |
| Amahle Ndlovu | Student | `student.cs@up.ac.za` | `ChangeMe123!` | Active |

---

## Archived Demo Institutions (Login Blocked)

GFU and RCT users exist in the database but have `is_active=False`. The
`authenticate_user()` service raises `AuthError("This account has been disabled.")`
before any token is issued. These users cannot log in.

| Institution | Users | Status |
|-------------|-------|--------|
| Greenfield University (GFU) | 40 users | Deactivated — `is_active=False` |
| Riverside College of Technology (RCT) | 42 users | Deactivated — `is_active=False` |

To re-deactivate if a seed re-run reactivates them:
```bash
python database/seed_data/deactivate_demo_users.py
```

---

## Seed Scripts Reference

| Script | Purpose |
|--------|---------|
| `database/seed_data/seed_pilot_users.py` | Creates TUT + UP pilot users (idempotent) |
| `database/seed_data/deactivate_demo_users.py` | Deactivates all GFU/RCT users (idempotent, supports --dry-run) |
| `database/seed_data/seed_tut.py` | Seeds TUT institutional hierarchy |
| `database/seed_data/seed_up.py` | Seeds UP institutional hierarchy |

---

## Security Notes

- Passwords are stored as bcrypt hashes (`$2b$12$...`). The plaintext above was
  set at seed time and is not stored anywhere in the codebase.
- `authenticate_user()` always runs the full bcrypt comparison even for unknown
  emails (timing-attack mitigation).
- The `is_active` gate is checked after password verification — a deactivated
  user with a correct password still receives `"This account has been disabled."`,
  not a token.
- JWTs are stored in `httpOnly` cookies only — never in `localStorage` or
  `sessionStorage`.
