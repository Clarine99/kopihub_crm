# KopiHub CRM Snapshot

## What’s in place
- **Django + DRF + JWT** already wired with a custom `users.User` model as `AUTH_USER_MODEL`, REST framework JWT authentication, and CRM app registration. 【F:config/settings.py†L1-L76】【F:users/models.py†L1-L8】
- **Membership + stamping domain** including `Customer`, `Membership` with status refresh helpers, `StampCycle`, `Stamp`, and global `ProgramSettings` for reward thresholds and mapping. 【F:crm/models.py†L1-L95】【F:crm/models.py†L97-L129】【F:crm/models.py†L131-L171】
- **Stamping services** for cycle management, awarding stamps based on thresholds, seeding the first cycle when a membership is created, and redeeming reward stamps. 【F:crm/services.py†L1-L73】
- **API surface** with DRF serializers and viewsets for customers, memberships (lookup/add-stamp/redeem actions), and program settings, routed under `/api/`. 【F:crm/serializers.py†L1-L73】【F:crm/views.py†L1-L88】【F:crm/urls.py†L1-L10】【F:config/urls.py†L17-L22】
- **Admin wiring** registers CRM models for quick inspection. 【F:crm/admin.py†L1-L8】

## How to configure
Create a `.env` file (or export env vars) before running the server:

```
SECRET_KEY=change-me
DEBUG=false
ALLOWED_HOSTS=localhost,127.0.0.1
DB_ENGINE=django.db.backends.postgresql
DB_NAME=kopihub
DB_USER=kopihub
DB_PASSWORD=kopihub
DB_HOST=localhost
DB_PORT=5432
```

## Next steps
- Add authentication endpoints (login/refresh) and role-aware permissions for cashier vs. admin flows.
- Document the expected Next.js client contract and scaffold pages for member registration, lookup, stamp awarding, reward redemption, and settings.
- Write automated tests for membership expiry refresh, stamp awarding thresholds, and reward redemption.
