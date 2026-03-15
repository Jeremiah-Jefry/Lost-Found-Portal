# KG Recovery Portal

A multi-college campus **Lost & Found management web application** built with a decoupled
Django REST Framework backend and a React + Vite frontend.
Students report lost or found items, staff manage cases end-to-end, and the built-in
auto-match engine surfaces likely item pairs automatically.

---

## Features

| Area | Detail |
|---|---|
| **3-tier RBAC** | `USER` · `STAFF` · `ADMIN` — each role has a distinct portal view and permission set |
| **Report items** | Submit Lost or Found reports with category, location, description, and an optional photo |
| **Auto-Match Engine** | Scores open Lost/Found pairs by category (+3) and location (+2); minimum threshold 2 |
| **Resolution state machine** | Every item moves through `OPEN → SECURED → RETURNED` independently of its Lost/Found type |
| **Immutable audit trail** | Every significant event (created, edited, status change, match found) recorded in `ItemLog` with actor, role, and timestamp |
| **Secure file uploads** | 2 MB hard limit · UUID-prefixed filenames · Pillow resize to ≤ 1024 px at quality 70 |
| **30-day image expiry** | Management command deletes physical files for items > 30 days old; DB text records are preserved |
| **JWT authentication** | SimpleJWT — 8 h access token, 7-day refresh token; auto-refresh on 401 in the frontend |
| **Admin analytics** | Full dashboard: same-day retrieval rate, handover breakdown, staff roster, live audit log |
| **Feed filters** | Filter by status, category, and free-text search; results are paginated |

---

## Tech Stack

| Layer | Technology |
|---|---|
| Backend | Python 3.11, Django 5.0.3, Django REST Framework 3.15 |
| Auth | djangorestframework-simplejwt 5.3 (Bearer JWT) |
| Database | SQLite (`backend/kg_portal.db`) via Django ORM |
| Image processing | Pillow 10.2 — resize + re-encode on model save |
| CORS | django-cors-headers 4.3 |
| Frontend | React 18, Vite 5, React Router v6 |
| Styling | Tailwind CSS 3, FontAwesome 6 (CDN) |
| HTTP client | Axios with JWT interceptors + auto-refresh |

---

## Project Structure

```
Lost-Found-Portal/
├── backend/
│   ├── manage.py
│   ├── requirements.txt
│   ├── kg_portal.db                  # SQLite database (git-ignored)
│   ├── core/
│   │   ├── settings.py               # Django settings, JWT config, CORS
│   │   ├── urls.py                   # Root URL conf
│   │   └── wsgi.py
│   ├── users/
│   │   ├── models.py                 # Custom User — role: USER / STAFF / ADMIN
│   │   ├── serializers.py            # Register, Login, UserBrief serializers
│   │   ├── views.py                  # RegisterView, LoginView, MeView
│   │   └── urls.py                   # /api/auth/register|login|me|refresh/
│   └── items/
│       ├── models.py                 # Item, ItemLog, Match + Pillow hook
│       ├── permissions.py            # IsStaffOrAdmin, IsAdminRole, IsOwnerOrStaff
│       ├── serializers.py            # Item, ItemList, ItemLog, Match serializers
│       ├── views.py                  # All item views with RBAC, dashboard, analytics
│       ├── urls.py                   # All item/match/analytics endpoints
│       └── management/commands/
│           └── cleanup_images.py     # 30-day image expiry command
└── frontend/
    ├── package.json
    ├── vite.config.js                # Proxies /api and /media to localhost:8000
    ├── tailwind.config.js
    └── src/
        ├── App.jsx                   # Routes with role-based redirect
        ├── api/axios.js              # Axios + JWT interceptors
        ├── context/AuthContext.jsx   # login / register / logout
        ├── components/
        │   ├── Layout.jsx            # Sidebar + header wrapper
        │   ├── Sidebar.jsx           # Role-aware nav links
        │   ├── ItemCard.jsx          # Card for feed/list views
        │   └── ProtectedRoute.jsx    # Auth + role guard
        └── pages/
            ├── LandingPage.jsx       # Login / register toggle
            ├── Dashboard.jsx         # STAFF/ADMIN: stat cards + dual-lane feed
            ├── ReportCenter.jsx      # USER: my reports, active/resolved split
            ├── Feed.jsx              # Public item feed with filters
            ├── ItemDetail.jsx        # Full item view + resolve form + audit log
            ├── ReportItem.jsx        # Create report form
            ├── EditItem.jsx          # Edit report form
            └── AdminAnalytics.jsx    # ADMIN: full analytics dashboard
```

---

## Setup

### 1. Clone and create a virtual environment

```bash
git clone <repo-url>
cd Lost-Found-Portal
python -m venv venv
source venv/Scripts/activate   # Windows
source venv/bin/activate        # macOS / Linux
```

### 2. Install backend dependencies

```bash
pip install -r backend/requirements.txt
```

### 3. Configure environment variables

Create `backend/.env` (never committed):

```env
DJANGO_SECRET_KEY=your-random-64-char-secret-key
DEBUG=True
```

Generate a secret key:

```bash
python -c "import secrets; print(secrets.token_hex(32))"
```

> The server starts without `.env` but uses an insecure fallback key and prints a warning.
> **Never deploy without setting `DJANGO_SECRET_KEY`.**

### 4. Run database migrations

```bash
cd backend
python manage.py migrate
```

### 5. Create a superuser (ADMIN account)

```bash
python manage.py createsuperuser
```

Then in the Django admin (`http://localhost:8000/admin/`) set the user's **role** to `ADMIN`.

### 6. Install frontend dependencies

```bash
cd ../frontend
npm install
```

---

## Running the Project

Two terminals are required — one for each server.

**Terminal 1 — Django backend:**

```bash
cd Lost-Found-Portal
source venv/Scripts/activate   # Windows
cd backend && python manage.py runserver
# → http://127.0.0.1:8000
```

**Terminal 2 — React frontend:**

```bash
cd Lost-Found-Portal/frontend
npm run dev
# → http://localhost:5173
```

Open **`http://localhost:5173`** in your browser.
Vite proxies all `/api` and `/media` requests to the Django server — no CORS issues during development.

---

## Role-Based Access

| Role | Home | Permissions |
|---|---|---|
| `USER` | `/report-center` | Create/edit/delete own reports; resolve own items (if not Security-held) |
| `STAFF` | `/dashboard` | All USER permissions + resolve any item including Security-held; manage handover and status |
| `ADMIN` | `/dashboard` | All STAFF permissions + access analytics; bypasses all RBAC gates |

### Resolve gate (exact logic)

```
ADMIN           → always allowed
STAFF           → allowed for any item, any handover state
USER (owner)    → allowed only if handover_status ≠ 'SECURITY'
USER (non-owner)→ denied
```

---

## API Endpoints

| Method | Endpoint | Auth | Description |
|---|---|---|---|
| POST | `/api/auth/register/` | public | Register + receive JWT pair |
| POST | `/api/auth/login/` | public | Login + receive JWT pair |
| GET/PATCH | `/api/auth/me/` | auth | Current user profile |
| POST | `/api/auth/refresh/` | public | Refresh access token |
| GET | `/api/items/` | public | Item feed (search, filter, paginate) |
| POST | `/api/items/` | auth | Create a report |
| GET/PATCH/DELETE | `/api/items/:id/` | varies | Item detail |
| POST | `/api/items/:id/resolve/` | auth + RBAC | Mark item returned |
| PATCH | `/api/items/:id/handover/` | STAFF/ADMIN | Update handover status |
| PATCH | `/api/items/:id/status/` | STAFF/ADMIN | Change resolution status |
| GET | `/api/items/mine/` | auth | Current user's own reports |
| GET | `/api/matches/` | STAFF/ADMIN | Unreviewed auto-matches |
| POST | `/api/matches/:id/review/` | STAFF/ADMIN | Mark a match reviewed |
| GET | `/api/dashboard/` | STAFF/ADMIN | Live counts + recent items |
| GET | `/api/analytics/` | ADMIN | Full analytics payload |

---

## Auto-Match Engine

When a Lost or Found item is saved, `run_auto_match()` runs immediately:

- Scans all open reports of the opposite type
- Scores each pair: **+3** exact category · **+2** exact location
- Minimum score **2** required to create a `Match` row
- Persists matches idempotently via `unique_together`
- Writes a `MATCH_FOUND` entry to `ItemLog` on both items

---

## Resolution State Machine

```
OPEN  ──►  SECURED  ──►  RETURNED
```

Every transition is recorded in `ItemLog` with `from_value`, `to_value`, actor, and role.
DB records are never deleted — the full text archive remains searchable indefinitely.

---

## Management Commands

```bash
# Purge image files for items reported more than 30 days ago
python manage.py cleanup_images
```

Schedule this with cron or a task scheduler for automatic expiry.

---

## Image Pipeline

1. **Upload** — UUID-prefixed filename prevents enumeration and collisions
2. **Compress** — Pillow resizes to ≤ 1024 px wide and re-encodes on model save:
   - JPEG / WEBP → `quality=70`, RGB normalised
   - PNG → lossless resize, transparency preserved
   - GIF → skipped (animation frames would break)
3. **Expiry** — physical file deleted after 30 days; `image` field set to `null`
