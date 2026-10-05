# AI Enabled Recruitment Screening and Interview Intelligence Portal

This Django 5 prototype ingests campus candidate files, validates and cleans records, creates rule and NLP screening scores, tracks asynchronous batch progress, schedules interview data, and exposes role-protected APIs. The project is PostgreSQL-first and uses Redis for Celery and cache. Its Django Template interface uses locally vendored Bootstrap 5.3.8 assets, and it contains standalone training programs for two scikit-learn models and one TensorFlow/Keras ANN.

## What is included

- CSV/XLSX ingestion with accepted and rejected CSV output files, validation, duplicate removal, safe failures, and row-level Celery progress.
- Bootstrap 5 Django templates for the dashboard, upload flow, candidate list/detail/edit, screening status, authentication, static styling, file/image fields, cookies, sessions, AJAX, and CSRF. Bootstrap is served locally from `static/vendor`, so the UI does not depend on a CDN.
- Models for users, roles, candidates, batches, screening results, interview slots, and feedback; migrations and customized admin pages are included.
- JWT access/refresh authentication, logout blacklisting, verified-HR and interviewer permissions, CRUD serializers, a hyperlinked role serializer, Swagger UI, and a Postman collection.
- PostgreSQL query examples, ORM analytics, Redis caching hooks, NLTK resume analysis, scikit-learn training/evaluation, Matplotlib output, and a minimal Keras model.

## Prerequisites

- Python 3.11 or 3.12
- PostgreSQL 14 or later
- Redis 6 or later
- A virtual environment is strongly recommended. TensorFlow platform support varies; use a Python release supported by the TensorFlow version installed from `requirements.txt`.

## Setup

1. Create and activate a virtual environment.

   ```bash
   python3 -m venv .venv
   source .venv/bin/activate
   pip install -r requirements.txt
   ```

2. Create a local PostgreSQL database.

   ```sql
   CREATE DATABASE recruitment_portal;
   CREATE USER recruitment_user WITH PASSWORD 'change-this-password';
   GRANT ALL PRIVILEGES ON DATABASE recruitment_portal TO recruitment_user;
   ```

3. Copy `.env.example` to the private `.env` file. Set a strong `DJANGO_SECRET_KEY` and replace the PostgreSQL password with the real credential for the local server. The project loads simple `KEY=VALUE` entries from `.env` automatically, while variables explicitly exported by the operating system still take precedence.

   ```bash
   cp .env.example .env
   ```

   Edit `.env`, then restrict access:

   ```bash
   chmod 600 .env
   ```

4. Run migrations and seed the evaluator accounts and `PY-DJ` role.

   ```bash
   python manage.py migrate
   python manage.py seed_demo
   ```

5. Download NLTK data once. The upload path has a regex fallback if these resources are unavailable.

   ```bash
   python -m nltk.downloader punkt averaged_perceptron_tagger_eng
   ```

## Start all local services

Use separate terminals after activating the virtual environment and exporting `.env`.

```bash
redis-server
```

```bash
celery -A recruitment_portal worker --loglevel=info --pool=solo
```

The `solo` pool is the supported local macOS configuration. It avoids the `billiard` prefork `fast_trace_task` initialization error on Python 3.12 while keeping uploads asynchronous from Django's HTTP process. Stop and restart an existing worker after changing this setting.

```bash
python manage.py runserver
```

Open the portal at `http://127.0.0.1:8000/`, admin at `http://127.0.0.1:8000/admin/`, and Swagger at `http://127.0.0.1:8000/api/docs/`.

## Evaluator accounts

`python manage.py seed_demo` creates the following local-only accounts. Change all passwords outside assessment use.

| Username | Password | Role | Verified |
|---|---|---|---|
| `admin` | `Assessment@123` | Admin and superuser | Yes |
| `hr` | `Assessment@123` | HR | Yes |
| `interviewer` | `Assessment@123` | Interviewer | Yes |

Self-registration creates an HR account that can log in and use HR APIs immediately. No OTP or email-verification step is required.

## Candidate upload

Upload `sample_data/candidates.csv` through **Upload**. It expects these exact headers:

`candidate_name, email, phone, college, applied_role, skills, experience_months, notice_period_days, expected_salary, resume_text, portfolio_url, historical_selection_status`

The sample data uses role code `PY-DJ`, which `seed_demo` creates. The request saves the batch ID in the HR session and queues processing. The batch page reports pending, processing, completed, or failed state and exposes generated accepted/rejected CSV files.

## API testing

Import `postman/Recruitment_Intelligence.postman_collection.json` into Postman. Run login first, copy `access` and `refresh` from the response into the collection variables, and then execute the remaining requests. Invalid or expired JWTs return structured 401 errors. The collection demonstrates six API requests.

Useful endpoints:

| Method | Endpoint | Access |
|---|---|---|
| POST | `/api/auth/register/` | Public |
| POST | `/api/auth/login/` | Public |
| POST | `/api/auth/refresh/` | Refresh token |
| POST | `/api/auth/logout/` | Authenticated |
| GET/POST/PUT/PATCH/DELETE | `/api/candidates/` | Verified HR or Admin |
| GET | `/api/roles/` | Authenticated, hyperlinked serializer |
| GET | `/api/batches/{id}/` | Verified HR or Admin |
| GET | `/api/screening-results/` | Verified HR or Admin |
| POST | `/api/feedback/` | Interviewer or Admin |
| POST | `/api/ml/predict/` | Verified HR or Admin |

## Train the machine learning models

The sample dataset includes the required upload columns plus `skill_match_score`, which the ingestion path safely ignores and the training scripts use. A realistic deployment should replace it with a larger representative dataset containing both selected and rejected examples.

```bash
python screening/ml/train_model.py sample_data/candidates.csv --output-dir artifacts
python screening/ml/train_ann.py sample_data/candidates.csv --output artifacts/shortlist_ann.keras --epochs 20
```

The scikit-learn program removes duplicates and identity columns, imputes missing values, caps IQR outliers, scales/selects features, compares Logistic Regression and Random Forest, reports accuracy/classification/ROC-AUC, and persists the best model plus an ROC curve. The endpoint loads `artifacts/shortlist_model.joblib`; until that file exists it returns a clearly labelled deterministic fallback score.

## Verification commands

For a lightweight test without PostgreSQL, use the explicit test-only SQLite switch. Normal application setup remains PostgreSQL-first.

```bash
DB_ENGINE=sqlite python manage.py check
DB_ENGINE=sqlite python manage.py test
```

Run PostgreSQL integration checks with the normal `.env` loaded:

```bash
python manage.py migrate --check
python manage.py test
```

## Viva guide

- **GET and POST:** GET retrieves/filter data without changing state. POST creates uploads, users, feedback, tokens, and predictions with request bodies and CSRF protection on browser forms.
- **MVT upload flow:** the URL routes to `upload_batch`; the view validates `BatchUploadForm`, saves `ApplicationBatch`, stores its ID in the session, starts a Celery task, and redirects to the batch template.
- **JWT and permissions:** login issues short-lived access and longer-lived refresh tokens. Refresh rotates access credentials; logout blacklists refresh tokens. DRF permission classes combine authentication with Admin, HR, and Interviewer roles.
- **Why Celery:** file parsing and scoring can outlive an HTTP timeout. The worker makes the request fast, records progress/failure, and permits retries without corrupting candidate records because writes use `update_or_create`.
- **Features and text:** the baseline uses experience, notice period, salary, and skill-match score. NLTK tokenizes/POS-tags resume text and converts it into token frequencies plus required-keyword overlap.

Important assumptions and limitations are recorded in `notes.txt`; required PostgreSQL examples are in `sql_queries.sql`.
