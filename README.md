# Hercules — backend

REST API for a fitness and nutrition tracker: workout sessions and exercise
progress, meal logging with food search (local database plus Open Food Facts),
barcode lookup, recipes, a social feed with follows/likes/comments, and
in-app notifications.

The React frontend is in a separate repo (hercules_frontend). There is no
public deployment.

## Stack

- Python 3.12, Django, Django REST Framework, Simple JWT, django-filter
- PostgreSQL 16, Redis 7 (Django cache, Celery broker)
- drf-spectacular for the OpenAPI schema and Swagger/ReDoc docs
- Open Food Facts API for food search and barcode lookup
- Docker Compose for local development

## Architecture

`docker-compose.yml` runs four services:

| Service | Role |
|---|---|
| `db` | postgres:16-alpine, port 5432 |
| `redis` | redis:7-alpine, port 6379 |
| `web` | Django dev server on port 8000 (runs `migrate` on start) |
| `celery` | Celery worker (`celery -A config worker`) |

The Celery app is configured in `config/celery.py`, but no tasks are defined
yet. Redis caches Open Food Facts search results for 24 hours.

Django apps:

| App | Endpoints under | Purpose |
|---|---|---|
| `users` | `/api/auth/` | Register, JWT login/refresh, own profile and TDEE estimate, public profiles, follow/unfollow, password reset, staff stats |
| `workouts` | `/api/workouts/` | Muscle groups, exercises and muscle activations, workout sessions, per-exercise progress, stats, diet/workout correlation |
| `nutrition` | `/api/nutrition/` | Food search, barcode lookup, user-submitted foods with staff verification, recipes (save/unsave), meal logs and daily summary |
| `social` | `/api/social/` | Feed, posts, likes, comments |
| `notifications` | `/api/notifications/` | Notifications created by signals on likes, comments and follows; unread count, mark read |

API docs are served at `/api/docs/` (Swagger UI) and `/api/redoc/`; the raw
schema is at `/api/schema/`.

## Running locally

Create a `.env` file in the repo root (never commit it). Variables read in
`config/settings.py` (all have development defaults):

`SECRET_KEY`, `DEBUG`, `ALLOWED_HOSTS`, `DB_NAME`, `DB_USER`, `DB_PASSWORD`,
`DB_HOST`, `DB_PORT`, `REDIS_URL`

Inside Compose, point `DB_HOST` at `db` and `REDIS_URL` at
`redis://redis:6379/1`, and use the database name, user and password set for
the `db` service in `docker-compose.yml`.

```sh
docker compose up --build
docker compose exec web python manage.py createsuperuser
docker compose exec web python manage.py seed_exercises
docker compose exec web python manage.py seed_greek_foods
```

The API is at http://localhost:8000/api/ and the docs at
http://localhost:8000/api/docs/. Email (password reset) uses Django's console
backend, so messages are printed in the `web` logs.

## Tests

```sh
docker compose exec web python manage.py test
```

43 test methods across `users`, `workouts`, `nutrition` and `social`.
