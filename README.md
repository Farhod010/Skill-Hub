# SkillHub MVP

SkillHub is a Django-based online learning platform with:

- email/password authentication
- student, instructor, moderator, and admin roles
- public course catalog and course detail pages
- free enrollment and paid demo checkout flows
- locked vs preview lesson access rules
- video lesson pages with progress saving
- student dashboard
- custom admin panel at `/panel/`
- REST API endpoints under `/api/`

## Stack

- Django
- Django REST Framework
- django-filter
- SQLite for quick local bootstrapping
- PostgreSQL-ready environment variables for production-like setups

## Apps

- `accounts`
- `courses`
- `payments`
- `dashboard`
- `site_settings`
- `api`
- `config`

## Quick Start

1. Create a virtual environment:

```powershell
python -m venv .venv
.venv\Scripts\Activate.ps1
```

2. Install dependencies:

```powershell
pip install -r requirements.txt
```

3. Create the environment file:

```powershell
Copy-Item .env.example .env
```

4. Run migrations:

```powershell
python manage.py migrate
```

5. Seed demo data:

```powershell
python manage.py seed_demo
```

6. Start the app:

```powershell
python manage.py runserver
```

Open:

- `/`
- `/courses/`
- `/dashboard/`
- `/panel/`
- `/api/`

## Demo Accounts

- `admin@skillhub.local` / `admin12345`
- `moderator@skillhub.local` / `moderator12345`
- `instructor@skillhub.local` / `instructor12345`
- `student@skillhub.local` / `student12345`
- `blocked@skillhub.local` / `blocked12345`

## Role Routing

- students land on `/dashboard/`
- moderators and admins land on `/panel/`
- users without panel access are redirected away from `/panel/`
- blocked users cannot log in

## Demo Flows

### Free course

Seed data includes a free course:

- `Learning Sprints for Busy Teams`

Behavior:

- guests can watch preview lessons only
- logged-in users can enroll instantly for free
- enrollment creates full lesson access and dashboard tracking

### Paid course

Paid courses use a demo checkout flow:

- click the paid course CTA
- get redirected to `/payments/checkout/<course-slug>/`
- complete the demo payment
- the course unlocks and redirects into the lesson flow

## Admin Panel

The custom panel at `/panel/` includes management screens for:

- users
- courses
- categories
- sections
- lessons
- reviews
- payments
- site settings

## API

Browsable API and endpoints live under `/api/`.

Important resources:

- `/api/users/`
- `/api/categories/`
- `/api/courses/`
- `/api/sections/`
- `/api/lessons/`
- `/api/enrollments/`
- `/api/wishlist/`
- `/api/reviews/`
- `/api/watch-progress/`
- `/api/payments/`
- `/api/site-settings/`

## Notes

- If `DB_NAME` is present in `.env`, the app uses PostgreSQL settings from environment variables.
- Without PostgreSQL variables, the app falls back to SQLite.
- Uploaded files go to `media/`.
- Static files live in `static/`.
- The paid checkout is intentionally a demo flow, not a real payment gateway.
