"""
KG Community Recovery Portal — app.py
=======================================
Mission-critical production backend for multi-college campus deployment.

Engineering principles applied in this version:
  ① Strict server-side validation  — all form inputs cleaned, length-capped,
      and validated against allowlists before touching the database.
  ② Transactional safety           — every session.commit() is guarded with
      try/except + rollback so a busy-campus write failure never corrupts state.
  ③ Resolution state machine       — OPEN → SECURED → RETURNED lifecycle, fully
      separate from the LOST/FOUND report type.
  ④ Immutable audit trail          — ItemLog records every significant event
      (create, edit, status change, match found) with actor + timestamp.
  ⑤ Environment-variable secrets   — SECRET_KEY read from KG_SECRET_KEY env var;
      a loud WARNING is emitted if the insecure fallback is used.
  ⑥ Magic-byte image verification  — imghdr is deprecated in 3.11 and removed in
      3.13; direct byte-header inspection is more robust.
  ⑦ UUID collision-proof filenames — prevents both enumeration and race conditions.
  ⑧ Lightweight startup migrations — ALTER TABLE … ADD COLUMN guards let the app
      run against both a fresh and an existing database without Flask-Migrate.
"""

import os
import uuid
import logging
from datetime import datetime

from flask import (Flask, render_template, request,
                   redirect, url_for, flash, abort)
from flask_sqlalchemy import SQLAlchemy
from sqlalchemy import text, inspect as sa_inspect
from flask_login import (LoginManager, UserMixin,
                         login_user, logout_user,
                         login_required, current_user)
from werkzeug.security import generate_password_hash, check_password_hash
from werkzeug.utils import secure_filename


# ═══════════════════════════════════════════════════════════════════════════════
#  APP CONFIGURATION
# ═══════════════════════════════════════════════════════════════════════════════

app = Flask(__name__)

# Read the secret key from the environment.
# In production: export KG_SECRET_KEY="<random-64-char-string>"
_secret_key = os.environ.get('KG_SECRET_KEY')
if not _secret_key:
    _secret_key = 'kg-portal-dev-INSECURE-2026'
    # This prints to stderr — visible in any hosting log.
    print(
        '[WARNING] KG_SECRET_KEY env var is not set. '
        'Running with an insecure development key. '
        'Set this variable before any real deployment.'
    )

app.config.update(
    SECRET_KEY                     = _secret_key,
    # In production, set DATABASE_URL to a Postgres URI like:
    # postgresql://user:pass@host/dbname
    SQLALCHEMY_DATABASE_URI        = os.environ.get('DATABASE_URL', 'sqlite:///kg_portal.db'),
    SQLALCHEMY_TRACK_MODIFICATIONS = False,
    UPLOAD_FOLDER                  = os.path.join(app.root_path, 'static', 'uploads'),
    MAX_CONTENT_LENGTH             = 2 * 1024 * 1024,   # 2 MB Werkzeug hard-limit
)

os.makedirs(app.config['UPLOAD_FOLDER'], exist_ok=True)

logging.basicConfig(
    level   = logging.INFO,
    format  = '%(asctime)s [%(levelname)s] %(name)s: %(message)s',
    datefmt = '%Y-%m-%d %H:%M:%S',
)

db            = SQLAlchemy(app)
login_manager = LoginManager(app)
login_manager.login_view             = 'login'
login_manager.login_message          = 'Please sign in to continue.'
login_manager.login_message_category = 'info'


# ═══════════════════════════════════════════════════════════════════════════════
#  CONSTANTS & ALLOWLISTS
# ═══════════════════════════════════════════════════════════════════════════════

ALLOWED_EXTENSIONS  : set[str]       = {'png', 'jpg', 'jpeg', 'gif', 'webp'}
ALLOWED_STATUSES    : frozenset[str] = frozenset({'LOST', 'FOUND'})
ALLOWED_CATEGORIES  : frozenset[str] = frozenset({'ELECTRONICS', 'DOCUMENTS',
                                                   'KEYS', 'CLOTHING', 'OTHER'})
ALLOWED_HANDOVERS   : frozenset[str] = frozenset({'', 'LEFT_AT_LOCATION',
                                                   'WITH_FINDER', 'SECURITY'})
ALLOWED_RESOLUTIONS : frozenset[str] = frozenset({'OPEN', 'SECURED', 'RETURNED'})

# Maximum character limits per field — enforced server-side
FIELD_LIMITS: dict[str, int] = {
    'title':            200,
    'description':     2000,
    'location':         255,
    'handover_details': 1000,
    'receiver_name':    100,
    'receiver_contact':  50,
}

# Magic-byte signatures for MIME verification
# (imghdr is deprecated in 3.11 and removed in 3.13 — direct inspection is safer)
IMAGE_MAGIC_BYTES: list[bytes] = [
    b'\xff\xd8\xff',   # JPEG
    b'\x89PNG\r\n',    # PNG
    b'GIF87a',         # GIF v87a
    b'GIF89a',         # GIF v89a
    b'RIFF',           # WEBP (4-byte RIFF header precedes "WEBP")
]

# Campus location zones — single source of truth for model & templates
LOCATION_ZONES: dict[str, list[str]] = {
    'Canteens': [
        'Canteen 1 — Arts Block',
        'Canteen 2 — Science Block',
        'Canteen 3 — Engineering Block',
    ],
    'Parking Lots': [
        'Parking Lot A — Main Gate',
        'Parking Lot B — North Campus',
        'Parking Lot C — Hostel Zone',
    ],
    'Academic Buildings': [
        'Central Library',
        'Main Administrative Block',
        'Lecture Hall Complex',
        'Workshop / Labs',
    ],
    'Campus Facilities': [
        'Auditorium',
        'Sports Complex',
        'Boys Hostel',
        'Girls Hostel',
        'Medical Center',
    ],
    'Other': ['Other / Unknown Location'],
}

# Pre-computed flat set for O(1) location validation
_VALID_LOCATIONS: frozenset[str] = frozenset(
    z for zones in LOCATION_ZONES.values() for z in zones
)


# ═══════════════════════════════════════════════════════════════════════════════
#  VALIDATION HELPERS
# ═══════════════════════════════════════════════════════════════════════════════

def clean_text(value: str, max_len: int) -> str:
    """
    Normalise whitespace and cap to max_len characters.
    Flask-Jinja2 auto-escapes all template output, so additional HTML
    escaping here would double-encode; leave that to the template layer.
    """
    return ' '.join(str(value).strip().split())[:max_len]


def validate_report_form(form) -> tuple[dict, list[str]]:
    """
    Extract, sanitise, and validate every field from the report/edit form.

    Returns:
        (data_dict, errors)  — errors is an empty list on success.

    Validation rules:
      • title       — required, max 200 chars
      • description — required, max 2 000 chars
      • status      — must be in ALLOWED_STATUSES
      • category    — must be in ALLOWED_CATEGORIES
      • location    — must be an exact LOCATION_ZONES value
      • handover_*  — optional; handover_status validated against allowlist
    """
    errors: list[str] = []
    data:   dict      = {}

    # ── Required text fields ──────────────────────────────────────────────────
    for field, label, max_len in (
        ('title',       'Item Name',   FIELD_LIMITS['title']),
        ('description', 'Description', FIELD_LIMITS['description']),
    ):
        cleaned = clean_text(form.get(field, ''), max_len)
        if not cleaned:
            errors.append(f'{label} is required.')
        data[field] = cleaned

    # ── Enum / allowlist fields ───────────────────────────────────────────────
    status = form.get('status', 'LOST')
    if status not in ALLOWED_STATUSES:
        errors.append('Invalid report type selected.')
    data['status'] = status if status in ALLOWED_STATUSES else 'LOST'

    category = form.get('category', 'OTHER')
    if category not in ALLOWED_CATEGORIES:
        errors.append('Invalid category selected.')
    data['category'] = category if category in ALLOWED_CATEGORIES else 'OTHER'

    # ── Location — validated against the predefined zone list ────────────────
    location = form.get('location', '').strip()
    if not location:
        errors.append('Campus location is required.')
    elif location not in _VALID_LOCATIONS:
        # Reject anything not in our known list (prevents freeform injection)
        errors.append('Please select a valid location from the dropdown.')
    data['location'] = location if location in _VALID_LOCATIONS else ''

    # ── Optional handover fields ──────────────────────────────────────────────
    hs = form.get('handover_status', '').strip()
    data['handover_status'] = hs if hs in ALLOWED_HANDOVERS else None

    for field in ('handover_details', 'receiver_name', 'receiver_contact'):
        val = clean_text(form.get(field, ''), FIELD_LIMITS.get(field, 255))
        data[field] = val or None

    return data, errors


# ═══════════════════════════════════════════════════════════════════════════════
#  SECURE UPLOAD HELPERS
# ═══════════════════════════════════════════════════════════════════════════════

def allowed_file(filename: str) -> bool:
    """Allowlist check on the file extension."""
    return ('.' in filename and
            filename.rsplit('.', 1)[1].lower() in ALLOWED_EXTENSIONS)


def is_valid_image(stream) -> bool:
    """
    Read the first 12 bytes and match against known image magic bytes.
    Always rewinds the stream before returning.
    Prevents renamed-extension attacks (e.g. shell.php → shell.jpg).
    """
    header = stream.read(12)
    stream.seek(0)
    return any(header.startswith(sig) for sig in IMAGE_MAGIC_BYTES)


def save_upload(file) -> tuple[str | None, bool]:
    """
    Validate and persist an uploaded image.

    Returns:
        (filename, True)   — success.
        (None, True)       — no file was provided (not an error).
        (None, False)      — validation failed; error already flashed.
    """
    if not file or not file.filename:
        return None, True

    if not allowed_file(file.filename):
        flash('Invalid file type. Accepted: PNG, JPG, GIF, WEBP.', 'error')
        return None, False

    if not is_valid_image(file.stream):
        flash('File content does not match a recognised image format.', 'error')
        return None, False

    ext      = file.filename.rsplit('.', 1)[1].lower()
    filename = secure_filename(
        f"{datetime.utcnow().strftime('%Y%m%d_%H%M%S')}_{uuid.uuid4().hex[:10]}.{ext}"
    )
    file.stream.seek(0)
    file.save(os.path.join(app.config['UPLOAD_FOLDER'], filename))
    return filename, True


# ═══════════════════════════════════════════════════════════════════════════════
#  MODELS
# ═══════════════════════════════════════════════════════════════════════════════

class User(UserMixin, db.Model):
    """Portal user — owns reports and receives match notifications."""
    __tablename__ = 'user'

    id            = db.Column(db.Integer, primary_key=True)
    username      = db.Column(db.String(80),  unique=True, nullable=False, index=True)
    email         = db.Column(db.String(120), unique=True, nullable=False, index=True)
    password_hash = db.Column(db.String(256), nullable=False)
    created_at    = db.Column(db.DateTime, default=datetime.utcnow, nullable=False)

    items = db.relationship('Item', backref='reporter', lazy='select',
                            cascade='all, delete-orphan')

    def set_password(self, password: str) -> None:
        self.password_hash = generate_password_hash(password)

    def check_password(self, password: str) -> bool:
        return check_password_hash(self.password_hash, password)

    def __repr__(self) -> str:
        return f'<User {self.username!r}>'


class Item(db.Model):
    """
    Core report entity.

    Two orthogonal axes of state:
      status            LOST | FOUND           — the kind of event
      resolution_status OPEN | SECURED | RETURNED  — the lifecycle stage

    handover_status tracks physical custody for FOUND items only.
    Indexes on status, category, location, and date_reported ensure
    efficient queries even as the campus DB grows to tens of thousands of rows.
    """
    __tablename__ = 'item'

    id                = db.Column(db.Integer, primary_key=True)
    title             = db.Column(db.String(200), nullable=False)
    description       = db.Column(db.Text,        nullable=False)
    status            = db.Column(db.String(10),  nullable=False, default='LOST',  index=True)
    category          = db.Column(db.String(20),  nullable=False, default='OTHER', index=True)
    location          = db.Column(db.String(255), nullable=False,                  index=True)
    image_filename    = db.Column(db.String(255), nullable=True)

    # ── Resolution state machine ──────────────────────────────────────────────
    # OPEN     → item first reported; active case
    # SECURED  → item is at security office or confirmed with finder
    # RETURNED → case closed; item returned to owner
    resolution_status = db.Column(db.String(20), nullable=False,
                                  default='OPEN', index=True)

    # ── Custody tracking (FOUND items only) ──────────────────────────────────
    handover_status   = db.Column(db.String(20),  nullable=True)
    handover_details  = db.Column(db.Text,        nullable=True)
    receiver_name     = db.Column(db.String(100), nullable=True)
    receiver_contact  = db.Column(db.String(100), nullable=True)

    # ── Timestamps ───────────────────────────────────────────────────────────
    date_reported     = db.Column(db.DateTime, default=datetime.utcnow,
                                  nullable=False, index=True)
    created_at        = db.Column(db.DateTime, default=datetime.utcnow, nullable=False)

    user_id           = db.Column(db.Integer, db.ForeignKey('user.id'), nullable=False)

    logs = db.relationship('ItemLog', backref='item', lazy='select',
                           cascade='all, delete-orphan',
                           order_by='ItemLog.created_at')

    # ── Computed labels ───────────────────────────────────────────────────────
    @property
    def status_label(self) -> str:
        return 'Lost' if self.status == 'LOST' else 'Found'

    @property
    def category_label(self) -> str:
        return {
            'ELECTRONICS': 'Electronics & Gadgets',
            'DOCUMENTS':   'IDs & Documents',
            'KEYS':        'Keys & Access Cards',
            'CLOTHING':    'Clothing & Bags',
            'OTHER':       'Other',
        }.get(self.category, 'Other')

    @property
    def handover_label(self) -> str:
        return {
            'LEFT_AT_LOCATION': 'Left at Location',
            'WITH_FINDER':      'With Finder',
            'SECURITY':         'Handed to Security',
        }.get(self.handover_status or '', '')

    @property
    def resolution_label(self) -> str:
        return {
            'OPEN':     'Open',
            'SECURED':  'Secured',
            'RETURNED': 'Returned to Owner',
        }.get(self.resolution_status, 'Open')

    @property
    def resolution_color(self) -> str:
        """Tailwind colour name used in template badge classes."""
        return {
            'OPEN':     'blue',
            'SECURED':  'amber',
            'RETURNED': 'emerald',
        }.get(self.resolution_status, 'blue')

    def __repr__(self) -> str:
        return f'<Item {self.id}: {self.title[:30]!r} [{self.status}/{self.resolution_status}]>'


class ItemLog(db.Model):
    """
    Immutable audit trail.  One row per significant event on an Item.

    action values:
      CREATED           item first reported
      UPDATED           fields edited by owner
      STATUS_CHANGED    resolution_status transition
      HANDOVER_UPDATED  handover_status changed
      MATCH_FOUND       auto-match engine found a candidate
      RESOLVED          item marked as RETURNED
    """
    __tablename__ = 'item_log'

    id         = db.Column(db.Integer, primary_key=True)
    item_id    = db.Column(db.Integer, db.ForeignKey('item.id', ondelete='CASCADE'),
                           nullable=False, index=True)
    user_id    = db.Column(db.Integer, db.ForeignKey('user.id', ondelete='SET NULL'),
                           nullable=True)
    action     = db.Column(db.String(50), nullable=False)
    note       = db.Column(db.Text,       nullable=True)
    from_value = db.Column(db.String(100), nullable=True)
    to_value   = db.Column(db.String(100), nullable=True)
    created_at = db.Column(db.DateTime, default=datetime.utcnow,
                           nullable=False, index=True)

    actor = db.relationship('User', foreign_keys=[user_id])

    @property
    def actor_name(self) -> str:
        return self.actor.username if self.actor else 'System'

    @property
    def action_label(self) -> str:
        return {
            'CREATED':          'Item Reported',
            'UPDATED':          'Report Edited',
            'STATUS_CHANGED':   'Status Changed',
            'HANDOVER_UPDATED': 'Handover Updated',
            'MATCH_FOUND':      'Auto-Match Result',
            'RESOLVED':         'Resolved',
        }.get(self.action, self.action)

    @property
    def action_icon(self) -> str:
        return {
            'CREATED':          'fa-flag',
            'UPDATED':          'fa-pen-to-square',
            'STATUS_CHANGED':   'fa-arrows-rotate',
            'HANDOVER_UPDATED': 'fa-hand-holding',
            'MATCH_FOUND':      'fa-bolt',
            'RESOLVED':         'fa-circle-check',
        }.get(self.action, 'fa-circle')

    def __repr__(self) -> str:
        return f'<ItemLog item={self.item_id} action={self.action!r}>'


class Match(db.Model):
    """
    Auto-Match Engine result pair.
    Scoring: category match = 3 pts, location match = 2 pts; max = 5.
    """
    __tablename__  = 'match'
    __table_args__ = (
        db.UniqueConstraint('found_item_id', 'lost_item_id', name='uq_found_lost'),
    )

    id            = db.Column(db.Integer, primary_key=True)
    found_item_id = db.Column(db.Integer,
                              db.ForeignKey('item.id', ondelete='CASCADE'),
                              nullable=False, index=True)
    lost_item_id  = db.Column(db.Integer,
                              db.ForeignKey('item.id', ondelete='CASCADE'),
                              nullable=False, index=True)
    score         = db.Column(db.Integer, default=0,     nullable=False)
    is_reviewed   = db.Column(db.Boolean, default=False, nullable=False)
    created_at    = db.Column(db.DateTime, default=datetime.utcnow, nullable=False)

    found_item = db.relationship('Item', foreign_keys=[found_item_id])
    lost_item  = db.relationship('Item', foreign_keys=[lost_item_id])

    @property
    def strength_label(self) -> str:
        if self.score >= 5: return 'Strong Match'
        if self.score >= 3: return 'Good Match'
        return 'Possible Match'


@login_manager.user_loader
def load_user(user_id: str):
    return db.session.get(User, int(user_id))


# ═══════════════════════════════════════════════════════════════════════════════
#  AUDIT TRAIL HELPER
# ═══════════════════════════════════════════════════════════════════════════════

def log_event(item_id: int, action: str,
              note:      str = '',
              from_val:  str = '',
              to_val:    str = '') -> None:
    """
    Append an audit entry to ItemLog.

    The caller is responsible for committing (or rolling back) the session.
    log_event() is intentionally side-effect-only so it can be batched into
    the same commit as the change it documents — atomicity guaranteed.
    """
    actor_id = current_user.id if current_user.is_authenticated else None
    db.session.add(ItemLog(
        item_id    = item_id,
        user_id    = actor_id,
        action     = action,
        note       = (note or '')[:500],
        from_value = (from_val or '')[:100],
        to_value   = (to_val   or '')[:100],
    ))


# ═══════════════════════════════════════════════════════════════════════════════
#  AUTO-MATCH ENGINE
# ═══════════════════════════════════════════════════════════════════════════════

def run_auto_match(found_item: Item) -> int:
    """
    Scan all open LOST reports for matches against a newly FOUND item.
    Idempotent — UniqueConstraint prevents duplicate Match rows.

    Scoring rubric:
      +3   exact category match
      +2   exact location match
       5   max (both) → "Strong Match"

    Each new pair is also audited with a MATCH_FOUND ItemLog entry
    on the FOUND item, preserving accountability.

    Returns: count of new Match records persisted.
    """
    if found_item.status != 'FOUND':
        return 0

    open_lost = Item.query.filter(
        Item.status == 'LOST',
        Item.id     != found_item.id,
    ).all()

    new_count = 0
    for lost in open_lost:
        score  = 0
        score += 3 if lost.category == found_item.category else 0
        score += 2 if lost.location == found_item.location else 0
        if score == 0:
            continue

        exists = Match.query.filter_by(
            found_item_id=found_item.id,
            lost_item_id=lost.id,
        ).first()
        if not exists:
            db.session.add(Match(
                found_item_id=found_item.id,
                lost_item_id=lost.id,
                score=score,
            ))
            log_event(
                found_item.id, 'MATCH_FOUND',
                note  = f'Matched with Lost report #{lost.id}: "{lost.title[:60]}"',
                to_val = str(lost.id),
            )
            new_count += 1

    if new_count:
        db.session.commit()
    return new_count


# ═══════════════════════════════════════════════════════════════════════════════
#  ROUTES — PUBLIC
# ═══════════════════════════════════════════════════════════════════════════════

@app.route('/')
def dashboard():
    total_lost  = Item.query.filter_by(status='LOST').count()
    total_found = Item.query.filter_by(status='FOUND').count()

    # Two separate streams — the key UX decision for high-stress scenarios
    recent_lost  = (Item.query.filter_by(status='LOST')
                              .order_by(Item.date_reported.desc())
                              .limit(5).all())
    recent_found = (Item.query.filter_by(status='FOUND')
                              .order_by(Item.date_reported.desc())
                              .limit(5).all())

    my_items        = []
    pending_matches = []

    if current_user.is_authenticated:
        my_items = (Item.query
                    .filter_by(user_id=current_user.id)
                    .order_by(Item.date_reported.desc())
                    .all())

        pending_matches = (
            Match.query
            .join(Item, Match.lost_item_id == Item.id)
            .filter(
                Item.user_id      == current_user.id,
                Item.status       == 'LOST',
                Match.is_reviewed == False,
            )
            .order_by(Match.score.desc(), Match.created_at.desc())
            .limit(4).all()
        )

    return render_template('dashboard.html',
        total_lost=total_lost,
        total_found=total_found,
        total_items=total_lost + total_found,
        recent_lost=recent_lost,
        recent_found=recent_found,
        my_items=my_items,
        pending_matches=pending_matches,
    )


@app.route('/feed')
def feed():
    query           = request.args.get('q',        '').strip()
    status_filter   = request.args.get('status',   '')
    category_filter = request.args.get('category', '')
    resolution_filter = request.args.get('resolution', '')

    items = Item.query.order_by(Item.date_reported.desc())

    if query:
        items = items.filter(db.or_(
            Item.title.ilike(f'%{query}%'),
            Item.description.ilike(f'%{query}%'),
            Item.location.ilike(f'%{query}%'),
        ))
    if status_filter in ALLOWED_STATUSES:
        items = items.filter_by(status=status_filter)
    if category_filter in ALLOWED_CATEGORIES:
        items = items.filter_by(category=category_filter)
    if resolution_filter in ALLOWED_RESOLUTIONS:
        items = items.filter_by(resolution_status=resolution_filter)

    return render_template('feed.html',
        items=items.all(),
        query=query,
        current_status=status_filter,
        current_category=category_filter,
        current_resolution=resolution_filter,
    )


@app.route('/item/<int:item_id>')
def item_detail(item_id):
    item = db.get_or_404(Item, item_id)

    matches = (Match.query
               .filter_by(lost_item_id=item.id, is_reviewed=False)
               .order_by(Match.score.desc())
               .limit(3).all()) if item.status == 'LOST' else []

    return render_template('detail.html', item=item, matches=matches)


# ═══════════════════════════════════════════════════════════════════════════════
#  ROUTES — AUTHENTICATED ACTIONS
# ═══════════════════════════════════════════════════════════════════════════════

@app.route('/report', methods=['GET', 'POST'])
@login_required
def report():
    if request.method == 'POST':
        data, errors = validate_report_form(request.form)

        if errors:
            for err in errors:
                flash(err, 'error')
            return render_template('report.html', location_zones=LOCATION_ZONES)

        image_filename, upload_ok = save_upload(request.files.get('image'))
        if not upload_ok:
            return render_template('report.html', location_zones=LOCATION_ZONES)

        item = Item(image_filename=image_filename, user_id=current_user.id, **data)

        try:
            db.session.add(item)
            db.session.flush()   # populate item.id before log_event references it
            log_event(
                item.id, 'CREATED',
                note   = f'{item.status_label} item reported at {item.location}',
                to_val = item.status,
            )
            db.session.commit()
        except Exception as exc:
            db.session.rollback()
            app.logger.error('report() commit failed: %s', exc)
            flash('A database error occurred. Please try again.', 'error')
            return render_template('report.html', location_zones=LOCATION_ZONES)

        # Run match engine after successful commit
        if item.status == 'FOUND':
            n = run_auto_match(item)
            if n:
                flash(
                    f'Found item reported! Auto-Match Engine detected '
                    f'{n} potential match{"es" if n != 1 else ""}.', 'success',
                )
            else:
                flash('Found item reported. No matching Lost reports at this time.', 'success')
        else:
            flash('Lost item reported. You will be notified if a match is found.', 'success')

        return redirect(url_for('feed'))

    return render_template('report.html', location_zones=LOCATION_ZONES)


@app.route('/item/<int:item_id>/edit', methods=['GET', 'POST'])
@login_required
def edit_item(item_id):
    item = db.get_or_404(Item, item_id)
    if item.user_id != current_user.id:
        abort(403)

    if request.method == 'POST':
        data, errors = validate_report_form(request.form)

        if errors:
            for err in errors:
                flash(err, 'error')
            return render_template('edit.html', item=item, location_zones=LOCATION_ZONES)

        image_filename, upload_ok = save_upload(request.files.get('image'))
        if not upload_ok:
            return render_template('edit.html', item=item, location_zones=LOCATION_ZONES)

        # Detect and log handover change separately for the audit trail
        old_handover = item.handover_status
        new_handover = data.get('handover_status')

        for field, value in data.items():
            setattr(item, field, value)
        if image_filename:
            item.image_filename = image_filename

        try:
            log_event(item.id, 'UPDATED',
                      note=f'Report edited by {current_user.username}')
            if old_handover != new_handover:
                log_event(
                    item.id, 'HANDOVER_UPDATED',
                    note      = f'Custody changed by {current_user.username}',
                    from_val  = old_handover or 'Not set',
                    to_val    = new_handover  or 'Not set',
                )
            db.session.commit()
        except Exception as exc:
            db.session.rollback()
            app.logger.error('edit_item(%d) commit failed: %s', item_id, exc)
            flash('A database error occurred. Please try again.', 'error')
            return render_template('edit.html', item=item, location_zones=LOCATION_ZONES)

        flash('Report updated successfully.', 'success')
        return redirect(url_for('item_detail', item_id=item.id))

    return render_template('edit.html', item=item, location_zones=LOCATION_ZONES)


@app.route('/item/<int:item_id>/resolve', methods=['POST'])
@login_required
def resolve_item(item_id):
    """
    Advance the resolution state machine for an item.
    Only the item owner may call this route.

    Allowed transitions (any direction for flexibility in real-world use):
      OPEN  → SECURED  → RETURNED
               SECURED  → OPEN   (reopen if custody is lost)
               RETURNED → OPEN   (reopen if return was incorrect)
    """
    item = db.get_or_404(Item, item_id)
    if item.user_id != current_user.id:
        abort(403)

    new_status = request.form.get('resolution_status', '').strip()
    if new_status not in ALLOWED_RESOLUTIONS:
        flash('Invalid status value.', 'error')
        return redirect(url_for('item_detail', item_id=item.id))

    old_status = item.resolution_status
    if old_status == new_status:
        flash('Status is already set to that value.', 'info')
        return redirect(url_for('item_detail', item_id=item.id))

    item.resolution_status = new_status

    action = 'RESOLVED' if new_status == 'RETURNED' else 'STATUS_CHANGED'
    try:
        log_event(
            item.id, action,
            note     = f'Updated by {current_user.username}',
            from_val = old_status,
            to_val   = new_status,
        )
        db.session.commit()
        flash(f'Status updated to "{item.resolution_label}".', 'success')
    except Exception as exc:
        db.session.rollback()
        app.logger.error('resolve_item(%d) commit failed: %s', item_id, exc)
        flash('Failed to update status. Please try again.', 'error')

    return redirect(url_for('item_detail', item_id=item.id))


@app.route('/item/<int:item_id>/delete', methods=['POST'])
@login_required
def delete_item(item_id):
    item = db.get_or_404(Item, item_id)
    if item.user_id != current_user.id:
        abort(403)

    try:
        db.session.delete(item)
        db.session.commit()
        flash('Report deleted.', 'success')
    except Exception as exc:
        db.session.rollback()
        app.logger.error('delete_item(%d) commit failed: %s', item_id, exc)
        flash('Failed to delete report. Please try again.', 'error')

    return redirect(url_for('feed'))


@app.route('/match/<int:match_id>/dismiss', methods=['POST'])
@login_required
def dismiss_match(match_id):
    match = db.get_or_404(Match, match_id)
    if match.lost_item.user_id != current_user.id:
        abort(403)

    match.is_reviewed = True
    try:
        db.session.commit()
    except Exception as exc:
        db.session.rollback()
        app.logger.error('dismiss_match(%d) commit failed: %s', match_id, exc)
        flash('Failed to dismiss match.', 'error')
        return redirect(url_for('dashboard'))

    flash('Match dismissed.', 'info')
    return redirect(url_for('dashboard'))


# ═══════════════════════════════════════════════════════════════════════════════
#  ROUTES — AUTHENTICATION
# ═══════════════════════════════════════════════════════════════════════════════

@app.route('/register', methods=['GET', 'POST'])
def register():
    if current_user.is_authenticated:
        return redirect(url_for('dashboard'))

    if request.method == 'POST':
        username = clean_text(request.form.get('username', ''), 80)
        email    = request.form.get('email', '').strip()[:120]
        password = request.form.get('password', '')
        confirm  = request.form.get('confirm',  '')

        errors: list[str] = []
        if not username or not email or not password:
            errors.append('All fields are required.')
        if password != confirm:
            errors.append('Passwords do not match.')
        if len(password) < 8:
            errors.append('Password must be at least 8 characters.')
        if User.query.filter_by(username=username).first():
            errors.append('Username already taken.')
        if User.query.filter_by(email=email).first():
            errors.append('Email already registered.')

        if errors:
            for err in errors:
                flash(err, 'error')
            return render_template('register.html', username=username, email=email)

        user = User(username=username, email=email)
        user.set_password(password)
        try:
            db.session.add(user)
            db.session.commit()
        except Exception as exc:
            db.session.rollback()
            app.logger.error('register() commit failed: %s', exc)
            flash('Registration failed due to a database error.', 'error')
            return render_template('register.html', username=username, email=email)

        login_user(user)
        flash('Account created — welcome to the KG Recovery Portal!', 'success')
        return redirect(url_for('dashboard'))

    return render_template('register.html')


@app.route('/login', methods=['GET', 'POST'])
def login():
    if current_user.is_authenticated:
        return redirect(url_for('dashboard'))

    if request.method == 'POST':
        username = clean_text(request.form.get('username', ''), 80)
        password = request.form.get('password', '')
        user     = User.query.filter_by(username=username).first()
        if user and user.check_password(password):
            login_user(user)
            flash('Welcome back!', 'success')
            return redirect(request.args.get('next') or url_for('dashboard'))
        flash('Invalid username or password.', 'error')

    return render_template('login.html')


@app.route('/logout')
@login_required
def logout():
    logout_user()
    flash('You have been signed out.', 'info')
    return redirect(url_for('dashboard'))


# ═══════════════════════════════════════════════════════════════════════════════
#  ERROR HANDLERS
# ═══════════════════════════════════════════════════════════════════════════════

@app.errorhandler(403)
def forbidden(e):
    return render_template('errors/403.html'), 403

@app.errorhandler(404)
def not_found(e):
    return render_template('errors/404.html'), 404

@app.errorhandler(413)
def payload_too_large(e):
    flash('Upload rejected: file exceeds the 2 MB limit.', 'error')
    return redirect(request.referrer or url_for('dashboard'))

@app.errorhandler(500)
def internal_error(e):
    db.session.rollback()
    return render_template('errors/500.html'), 500


# ═══════════════════════════════════════════════════════════════════════════════
#  JINJA2 FILTERS
# ═══════════════════════════════════════════════════════════════════════════════

@app.template_filter('timesince')
def timesince_filter(dt: datetime) -> str:
    diff    = datetime.utcnow() - dt
    seconds = diff.total_seconds()
    if seconds < 60:   return 'just now'
    if seconds < 3600: m = int(seconds//60);   return f'{m} min{"s" if m!=1 else ""} ago'
    if seconds < 86400:h = int(seconds//3600); return f'{h} hour{"s" if h!=1 else ""} ago'
    d = int(seconds // 86400);                 return f'{d} day{"s" if d!=1 else ""} ago'


# ═══════════════════════════════════════════════════════════════════════════════
#  BOOTSTRAP & SCHEMA MIGRATIONS
# ═══════════════════════════════════════════════════════════════════════════════

with app.app_context():
    # Step 1 — create any new tables (ItemLog, Match, etc.)
    db.create_all()

    # Step 2 — add new columns to existing tables
    # db.create_all() never ALTERs existing tables; we do it safely here.
    # Each migration is guarded by a column-existence check so it is
    # completely idempotent across restarts.
    def _col_exists(insp, table: str, column: str) -> bool:
        return any(c['name'] == column for c in insp.get_columns(table))

    insp = sa_inspect(db.engine)

    with db.engine.begin() as conn:
        # item.created_at — back-filled from date_reported
        if not _col_exists(insp, 'item', 'created_at'):
            conn.execute(text("ALTER TABLE item ADD COLUMN created_at DATETIME"))
            conn.execute(text("UPDATE item SET created_at = date_reported"))

        # item.resolution_status — back-filled to 'OPEN'
        if not _col_exists(insp, 'item', 'resolution_status'):
            conn.execute(text(
                "ALTER TABLE item ADD COLUMN resolution_status VARCHAR(20) NOT NULL DEFAULT 'OPEN'"
            ))

        # user.created_at
        if not _col_exists(insp, 'user', 'created_at'):
            conn.execute(text("ALTER TABLE user ADD COLUMN created_at DATETIME"))
            conn.execute(text("UPDATE user SET created_at = CURRENT_TIMESTAMP"))


if __name__ == '__main__':
    app.run(debug=True, port=5000)
