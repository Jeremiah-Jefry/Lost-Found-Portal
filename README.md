# KG Recovery Portal

A multi-college campus **Lost & Found management web application** built with Flask.
Students and staff report lost or found items, track their lifecycle through a resolution
state machine, and let the built-in auto-match engine surface candidates automatically.

---

## Features

| Area | Detail |
|---|---|
| **Report items** | Submit Lost or Found reports with category, campus location zone, description, and an optional photo |
| **Auto-Match Engine** | When a Found item is submitted, the engine scans all open Lost reports and scores matches by category (+3) and location (+2) |
| **Resolution state machine** | Every item moves through `OPEN → SECURED → RETURNED` independently of its Lost/Found type |
| **Immutable audit trail** | Every significant event (created, edited, status change, match found) is recorded in `ItemLog` with actor and timestamp |
| **Secure file uploads** | 2 MB hard limit · extension allowlist · magic-byte MIME verification · UUID-prefixed filenames |
| **Pillow compression** | Every uploaded image is resized to ≤ 1024 px wide and re-encoded at quality 85 on save |
| **30-day image expiry** | `cleanup_old_images()` deletes physical files for items > 30 days old; DB records are preserved so the text archive stays searchable |
| **Server-side validation** | All inputs cleaned, length-capped, and validated against frozenset allowlists |
| **Transactional safety** | Every `db.session.commit()` wrapped in `try/except` with `rollback()` |
| **Today's Activity snapshot** | Dashboard shows a live banner of Lost / Found / Total counts since UTC midnight |
| **Two-lane dashboard** | Lost and Found activity streams rendered in strictly separate columns |
| **Custom error pages** | Branded 404, 403, and 500 pages; 413 redirects with a flash message |
| **Feed filters** | Filter by status, category, and case state (`OPEN / SECURED / RETURNED`) simultaneously |
| **Contact for verification** | Detail page shows reporter info and a `KGP-XXXXX` reference ID for security-desk handovers |

---

## Tech Stack

| Layer | Technology |
|---|---|
| Backend | Python 3.11+, Flask 3.1.0 |
| ORM | Flask-SQLAlchemy 3.1.1 (SQLite in development) |
| Auth | Flask-Login 0.6.3 |
| Security | Werkzeug 3.1.3 |
| Image processing | Pillow 11.1.0 |
| Frontend | Tailwind CSS (CDN), FontAwesome 6 Free (CDN), Vanilla JS |
| Database | SQLite (file: `instance/kg_portal.db`) |

---

## Project Structure

```
Lost-Found-Portal/
├── app.py                        # Single-file Flask application
├── requirements.txt
├── instance/
│   └── kg_portal.db              # SQLite database (git-ignored)
├── static/
│   ├── css/
│   │   └── style.css             # Custom CSS — slide animations, stat cards, timeline
│   ├── js/
│   │   └── main.js               # Global JS — mobile sidebar, countUp, handover toggle
│   └── uploads/                  # User-uploaded images (git-ignored, .gitkeep tracked)
│       └── .gitkeep
└── templates/
    ├── base.html                 # Master layout — links style.css and main.js
    ├── dashboard.html            # Today snapshot · Two-lane streams · Match alerts
    ├── feed.html                 # Searchable grid with Status / Category / Case filters
    ├── detail.html               # Timeline · Audit trail · Resolution controls
    ├── report.html               # Drag-drop upload · Handover section (animated)
    ├── edit.html                 # Edit form — synced handover section
    ├── login.html
    ├── register.html
    └── errors/
        ├── 403.html
        ├── 404.html
        └── 500.html
```

---

## Setup

### 1. Clone and create a virtual environment

```bash
git clone <repo-url>
cd Lost-Found-Portal
python -m venv venv
source venv/bin/activate        # Windows: venv\Scripts\activate
```

### 2. Install dependencies

```bash
pip install -r requirements.txt
```

### 3. Set environment variables

| Variable | Required | Description |
|---|---|---|
| `KG_SECRET_KEY` | **Yes (production)** | Flask session signing key — use a random 64-char string |
| `DATABASE_URL` | No | SQLAlchemy URI; defaults to `sqlite:///kg_portal.db` |

```bash
# bash / zsh
export KG_SECRET_KEY="$(python -c 'import secrets; print(secrets.token_hex(32))')"

# Windows PowerShell
$env:KG_SECRET_KEY = python -c "import secrets; print(secrets.token_hex(32))"
```

> The app starts without `KG_SECRET_KEY` but prints `[WARNING]` to stderr and uses an
> insecure hardcoded fallback. **Never deploy without setting this variable.**

### 4. Run

```bash
python app.py
```

The server starts at `http://127.0.0.1:5000`.

The database, schema migrations, and image expiry all run automatically at startup —
no manual `flask db upgrade` required.

---

## CLI Commands

```bash
# Manually purge expired images (also runs automatically on every startup)
flask cleanup-images
```

---

## Image Pipeline

Every uploaded image goes through a two-stage pipeline:

1. **Validation** — extension allowlist + magic-byte MIME check + 2 MB Werkzeug limit
2. **Compression** — Pillow resizes to ≤ 1024 px wide and re-encodes:
   - JPEG / WEBP → `quality=85`, RGB normalised
   - PNG → lossless resize, transparency preserved
   - GIF → skipped (animation frames would break)

After 30 days the physical file is deleted and `image_filename` is set to `None`.
The database record itself is never deleted — the text archive remains fully searchable.

---

## Database Migrations

No Flask-Migrate. New columns are applied at startup via idempotent `ALTER TABLE` guards:

```python
if not _col_exists(insp, 'item', 'resolution_status'):
    conn.execute(text("ALTER TABLE item ADD COLUMN resolution_status ..."))
```

Safe to run against both a fresh and an existing database.

---

## Resolution State Machine

```
OPEN  ──►  SECURED  ──►  RETURNED
  ▲            │
  └────────────┘  (reopen if custody is lost or return was incorrect)
```

The item owner controls transitions from the detail page. Every transition is recorded
in `ItemLog` with `from_value` and `to_value`.

---

## Auto-Match Engine

When a **Found** item is reported, `run_auto_match()` runs immediately after commit:

- Scans all open **Lost** reports
- Scores each pair: **+3** exact category · **+2** exact location (max 5 — "Strong Match")
- Persists `Match` rows idempotently via `UniqueConstraint`
- Records a `MATCH_FOUND` entry in `ItemLog`

Pending alerts appear on the dashboard for the owner of the matched Lost report.

---

## Security Notes

- All form input sanitised via `clean_text()` and validated against frozenset allowlists
- File uploads: extension allowlist → magic-byte MIME check → UUID-prefixed `secure_filename`
- `MAX_CONTENT_LENGTH = 2 MB` enforced at the Werkzeug level (413 handler redirects gracefully)
- `SECRET_KEY` sourced from `KG_SECRET_KEY` env var with loud fallback warning
- Ownership checks (`item.user_id != current_user.id`) guard all mutating routes; violations return 403
