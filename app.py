"""
KG Community Recovery Portal — app.py
======================================
Production-grade Flask back-end for the multi-college lost-and-found portal.

Architecture decisions:
  • Single-file layout keeps the demo self-contained but respects separation
    of concerns via clearly delineated section comments.
  • SQLite is appropriate for campus-scale; swap DATABASE_URI for Postgres
    in production without touching any application logic.
  • The Auto-Match Engine is stateless at call time and idempotent on re-run
    (UniqueConstraint prevents duplicate Match rows).
"""

import os
import uuid
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


# ═══════════════════════════════════════════════════════════════
#  APP CONFIGURATION
# ═══════════════════════════════════════════════════════════════
app = Flask(__name__)

app.config.update(
    SECRET_KEY           = os.environ.get('SECRET_KEY', 'kg-portal-dev-secret-2026'),
    SQLALCHEMY_DATABASE_URI      = 'sqlite:///kg_portal.db',
    SQLALCHEMY_TRACK_MODIFICATIONS = False,
    UPLOAD_FOLDER        = os.path.join(app.root_path, 'static', 'uploads'),
    # Hard server-side limit enforced by Werkzeug before any route logic runs
    MAX_CONTENT_LENGTH   = 2 * 1024 * 1024,   # 2 MB
)

os.makedirs(app.config['UPLOAD_FOLDER'], exist_ok=True)

db           = SQLAlchemy(app)
login_manager = LoginManager(app)
login_manager.login_view             = 'login'
login_manager.login_message          = 'Please sign in to continue.'
login_manager.login_message_category = 'info'


# ═══════════════════════════════════════════════════════════════
#  CONSTANTS
# ═══════════════════════════════════════════════════════════════

# Permitted upload extensions (whitelist approach)
ALLOWED_EXTENSIONS = {'png', 'jpg', 'jpeg', 'gif', 'webp'}

# Magic-byte signatures for server-side MIME verification.
# Prevents renamed-extension attacks (e.g. shell.php → shell.jpg).
IMAGE_MAGIC_BYTES: list[bytes] = [
    b'\xff\xd8\xff',        # JPEG
    b'\x89PNG\r\n',         # PNG
    b'GIF87a',              # GIF version 87a
    b'GIF89a',              # GIF version 89a
    b'RIFF',                # WEBP (4-byte RIFF header)
]

# Campus location zones — single source of truth for both model and templates
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
    'Other': [
        'Other / Unknown Location',
    ],
}


# ═══════════════════════════════════════════════════════════════
#  SECURE UPLOAD HELPERS
# ═══════════════════════════════════════════════════════════════

def allowed_file(filename: str) -> bool:
    """Check that the filename carries an allowed extension."""
    return ('.' in filename
            and filename.rsplit('.', 1)[1].lower() in ALLOWED_EXTENSIONS)


def is_valid_image(stream) -> bool:
    """
    Read the first 12 bytes of the stream and compare against known
    image magic bytes.  Always rewinds the stream before returning
    so the caller can still save the full file.
    """
    header = stream.read(12)
    stream.seek(0)
    return any(header.startswith(sig) for sig in IMAGE_MAGIC_BYTES)


def save_upload(file) -> tuple[str | None, bool]:
    """
    Validate and persist an uploaded image file.

    Returns:
        (filename, True)   — success; filename is the stored name.
        (None,    True)    — no file provided; not an error.
        (None,    False)   — validation failed; error already flashed.
    """
    if not file or not file.filename:
        return None, True                              # No file — acceptable

    if not allowed_file(file.filename):
        flash('Invalid file type. Accepted formats: PNG, JPG, GIF, WEBP.', 'error')
        return None, False

    if not is_valid_image(file.stream):
        flash('File content does not match a recognised image format.', 'error')
        return None, False

    # Build a collision-resistant, sanitised filename
    ext      = file.filename.rsplit('.', 1)[1].lower()
    raw_name = (f"{datetime.utcnow().strftime('%Y%m%d_%H%M%S')}"
                f"_{uuid.uuid4().hex[:10]}.{ext}")
    filename = secure_filename(raw_name)

    file.stream.seek(0)   # Ensure stream is at start before saving
    file.save(os.path.join(app.config['UPLOAD_FOLDER'], filename))
    return filename, True


# ═══════════════════════════════════════════════════════════════
#  MODELS
# ═══════════════════════════════════════════════════════════════

class User(UserMixin, db.Model):
    """Portal user — can report items and receive match notifications."""
    __tablename__ = 'user'

    id            = db.Column(db.Integer, primary_key=True)
    username      = db.Column(db.String(80),  unique=True, nullable=False, index=True)
    email         = db.Column(db.String(120), unique=True, nullable=False, index=True)
    password_hash = db.Column(db.String(256), nullable=False)
    created_at    = db.Column(db.DateTime,    default=datetime.utcnow, nullable=False)

    items = db.relationship('Item', backref='reporter',
                            lazy='select', cascade='all, delete-orphan')

    def set_password(self, password: str) -> None:
        self.password_hash = generate_password_hash(password)

    def check_password(self, password: str) -> bool:
        return check_password_hash(self.password_hash, password)

    def __repr__(self) -> str:
        return f'<User {self.username!r}>'


class Item(db.Model):
    """
    Core entity. Represents a single lost or found item report.

    status       : 'LOST' | 'FOUND'
    category     : high-level grouping used by the match engine
    location     : one of the predefined LOCATION_ZONES values
    handover_*   : filled only for FOUND items that have been handed over
    """
    __tablename__ = 'item'

    id               = db.Column(db.Integer, primary_key=True)
    title            = db.Column(db.String(200), nullable=False)
    description      = db.Column(db.Text,        nullable=False)
    status           = db.Column(db.String(10),  nullable=False, default='LOST',  index=True)
    category         = db.Column(db.String(20),  nullable=False, default='OTHER', index=True)
    location         = db.Column(db.String(255), nullable=False,                  index=True)
    image_filename   = db.Column(db.String(255), nullable=True)

    # Handover / custody tracking
    handover_status  = db.Column(db.String(20),  nullable=True)   # LEFT_AT_LOCATION | WITH_FINDER | SECURITY
    handover_details = db.Column(db.Text,        nullable=True)
    receiver_name    = db.Column(db.String(100), nullable=True)
    receiver_contact = db.Column(db.String(100), nullable=True)

    # Audit timestamps
    date_reported    = db.Column(db.DateTime, default=datetime.utcnow, nullable=False, index=True)
    created_at       = db.Column(db.DateTime, default=datetime.utcnow, nullable=False)

    user_id          = db.Column(db.Integer, db.ForeignKey('user.id'), nullable=False)

    # ── Computed labels (used in templates) ────────────────────
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

    def __repr__(self) -> str:
        return f'<Item {self.id}: {self.title[:30]!r} [{self.status}]>'


class Match(db.Model):
    """
    Auto-Match Engine result table.

    Each row links a FOUND item to a LOST item with a relevance score.
    Scoring:
      +3  exact category match
      +2  exact location match
      ──
       5  maximum (both match — "Strong Match")

    A score of 0 is never stored; minimum persisted score is 2.
    The UniqueConstraint prevents the engine from creating duplicate pairs
    even if run_auto_match() is called multiple times on the same item.
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

    # Convenient accessors
    found_item = db.relationship('Item', foreign_keys=[found_item_id])
    lost_item  = db.relationship('Item', foreign_keys=[lost_item_id])

    @property
    def strength_label(self) -> str:
        if self.score >= 5: return 'Strong Match'
        if self.score >= 3: return 'Good Match'
        return 'Possible Match'

    @property
    def strength_color(self) -> str:
        """Returns a Tailwind colour token for the badge."""
        if self.score >= 5: return 'emerald'
        if self.score >= 3: return 'amber'
        return 'blue'

    def __repr__(self) -> str:
        return f'<Match found={self.found_item_id} lost={self.lost_item_id} score={self.score}>'


@login_manager.user_loader
def load_user(user_id: str):
    return db.session.get(User, int(user_id))


# ═══════════════════════════════════════════════════════════════
#  AUTO-MATCH ENGINE
# ═══════════════════════════════════════════════════════════════

def run_auto_match(found_item: Item) -> int:
    """
    Scan all open LOST items and create Match records for relevant pairs.

    Called automatically whenever a new FOUND item is reported.
    Idempotent — safe to call multiple times; duplicates are suppressed
    by the UniqueConstraint on (found_item_id, lost_item_id).

    Algorithm:
      For each open LOST item:
        score = 0
        if category matches  → score += 3
        if location matches  → score += 2
        if score > 0         → persist Match(score=score)

    Returns:
        int — number of new Match records created in this run.
    """
    if found_item.status != 'FOUND':
        return 0

    open_lost = Item.query.filter(
        Item.status == 'LOST',
        Item.id     != found_item.id,
    ).all()

    new_count = 0
    for lost in open_lost:
        score = 0
        if lost.category == found_item.category:
            score += 3
        if lost.location == found_item.location:
            score += 2

        if score == 0:
            continue   # Not relevant — skip

        # Idempotency guard
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
            new_count += 1

    if new_count:
        db.session.commit()
    return new_count


# ═══════════════════════════════════════════════════════════════
#  ROUTES — PUBLIC
# ═══════════════════════════════════════════════════════════════

@app.route('/')
def dashboard():
    total_lost   = Item.query.filter_by(status='LOST').count()
    total_found  = Item.query.filter_by(status='FOUND').count()
    total_items  = total_lost + total_found
    recent_items = (Item.query
                    .order_by(Item.date_reported.desc())
                    .limit(6).all())

    my_items        = []
    pending_matches = []

    if current_user.is_authenticated:
        my_items = (Item.query
                    .filter_by(user_id=current_user.id)
                    .order_by(Item.date_reported.desc())
                    .all())

        # Surface pending auto-match results for the user's LOST items
        pending_matches = (
            Match.query
            .join(Item, Match.lost_item_id == Item.id)
            .filter(
                Item.user_id    == current_user.id,
                Item.status     == 'LOST',
                Match.is_reviewed == False,
            )
            .order_by(Match.score.desc(), Match.created_at.desc())
            .limit(4)
            .all()
        )

    return render_template('dashboard.html',
        total_lost=total_lost,
        total_found=total_found,
        total_items=total_items,
        recent_items=recent_items,
        my_items=my_items,
        pending_matches=pending_matches,
    )


@app.route('/feed')
def feed():
    query           = request.args.get('q', '').strip()
    status_filter   = request.args.get('status', '')
    category_filter = request.args.get('category', '')

    items = Item.query.order_by(Item.date_reported.desc())

    if query:
        items = items.filter(db.or_(
            Item.title.ilike(f'%{query}%'),
            Item.description.ilike(f'%{query}%'),
            Item.location.ilike(f'%{query}%'),
        ))
    if status_filter in ('LOST', 'FOUND'):
        items = items.filter_by(status=status_filter)
    if category_filter in ('ELECTRONICS', 'DOCUMENTS', 'KEYS', 'CLOTHING', 'OTHER'):
        items = items.filter_by(category=category_filter)

    return render_template('feed.html',
        items=items.all(),
        query=query,
        current_status=status_filter,
        current_category=category_filter,
    )


@app.route('/item/<int:item_id>')
def item_detail(item_id):
    item = db.get_or_404(Item, item_id)

    # Retrieve unreviewed matches so the detail page can render the timeline
    matches = (Match.query
               .filter_by(lost_item_id=item.id, is_reviewed=False)
               .order_by(Match.score.desc())
               .limit(3)
               .all()) if item.status == 'LOST' else []

    return render_template('detail.html', item=item, matches=matches)


# ═══════════════════════════════════════════════════════════════
#  ROUTES — AUTHENTICATED ACTIONS
# ═══════════════════════════════════════════════════════════════

@app.route('/report', methods=['GET', 'POST'])
@login_required
def report():
    if request.method == 'POST':
        title            = request.form.get('title',       '').strip()
        description      = request.form.get('description', '').strip()
        status           = request.form.get('status',      'LOST')
        category         = request.form.get('category',    'OTHER')
        location         = request.form.get('location',    '').strip()
        handover_status  = request.form.get('handover_status',  '').strip() or None
        handover_details = request.form.get('handover_details', '').strip() or None
        receiver_name    = request.form.get('receiver_name',    '').strip() or None
        receiver_contact = request.form.get('receiver_contact', '').strip() or None

        if not title or not description or not location:
            flash('Please fill in all required fields.', 'error')
            return render_template('report.html', location_zones=LOCATION_ZONES)

        # ── Secure file upload ──────────────────────────────────
        image_filename, upload_ok = save_upload(request.files.get('image'))
        if not upload_ok:
            return render_template('report.html', location_zones=LOCATION_ZONES)

        # ── Persist item ────────────────────────────────────────
        item = Item(
            title=title, description=description,
            status=status, category=category, location=location,
            image_filename=image_filename,
            handover_status=handover_status, handover_details=handover_details,
            receiver_name=receiver_name, receiver_contact=receiver_contact,
            user_id=current_user.id,
        )
        db.session.add(item)
        db.session.commit()

        # ── Auto-Match Engine ───────────────────────────────────
        if item.status == 'FOUND':
            n = run_auto_match(item)
            if n:
                flash(
                    f'Found item reported! The Auto-Match Engine detected '
                    f'{n} potential match{"es" if n != 1 else ""} '
                    f'with open Lost reports.', 'success',
                )
            else:
                flash('Found item reported. No matching Lost reports at this time.', 'success')
        else:
            flash('Lost item reported. You will be notified when a match is found.', 'success')

        return redirect(url_for('feed'))

    return render_template('report.html', location_zones=LOCATION_ZONES)


@app.route('/item/<int:item_id>/edit', methods=['GET', 'POST'])
@login_required
def edit_item(item_id):
    item = db.get_or_404(Item, item_id)
    if item.user_id != current_user.id:
        abort(403)

    if request.method == 'POST':
        item.title           = request.form.get('title',       item.title).strip()
        item.description     = request.form.get('description', item.description).strip()
        item.status          = request.form.get('status',      item.status)
        item.category        = request.form.get('category',    item.category)
        item.location        = request.form.get('location',    item.location).strip()
        item.handover_status = request.form.get('handover_status',  '').strip() or None
        item.handover_details= request.form.get('handover_details', '').strip() or None
        item.receiver_name   = request.form.get('receiver_name',    '').strip() or None
        item.receiver_contact= request.form.get('receiver_contact', '').strip() or None

        image_filename, upload_ok = save_upload(request.files.get('image'))
        if not upload_ok:
            return render_template('edit.html', item=item, location_zones=LOCATION_ZONES)
        if image_filename:
            item.image_filename = image_filename

        db.session.commit()
        flash('Report updated successfully.', 'success')
        return redirect(url_for('item_detail', item_id=item.id))

    return render_template('edit.html', item=item, location_zones=LOCATION_ZONES)


@app.route('/item/<int:item_id>/delete', methods=['POST'])
@login_required
def delete_item(item_id):
    item = db.get_or_404(Item, item_id)
    if item.user_id != current_user.id:
        abort(403)
    db.session.delete(item)
    db.session.commit()
    flash('Report deleted.', 'success')
    return redirect(url_for('feed'))


@app.route('/match/<int:match_id>/dismiss', methods=['POST'])
@login_required
def dismiss_match(match_id):
    """
    Allow the owner of a Lost item to dismiss an auto-match suggestion.
    The match record is soft-deleted (is_reviewed = True) rather than
    physically removed, preserving audit history.
    """
    match = db.get_or_404(Match, match_id)
    if match.lost_item.user_id != current_user.id:
        abort(403)
    match.is_reviewed = True
    db.session.commit()
    flash('Match dismissed.', 'info')
    return redirect(url_for('dashboard'))


# ═══════════════════════════════════════════════════════════════
#  ROUTES — AUTHENTICATION
# ═══════════════════════════════════════════════════════════════

@app.route('/register', methods=['GET', 'POST'])
def register():
    if current_user.is_authenticated:
        return redirect(url_for('dashboard'))

    if request.method == 'POST':
        username = request.form.get('username', '').strip()
        email    = request.form.get('email',    '').strip()
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
            for e in errors:
                flash(e, 'error')
            return render_template('register.html', username=username, email=email)

        user = User(username=username, email=email)
        user.set_password(password)
        db.session.add(user)
        db.session.commit()
        login_user(user)
        flash('Account created — welcome to the KG Recovery Portal!', 'success')
        return redirect(url_for('dashboard'))

    return render_template('register.html')


@app.route('/login', methods=['GET', 'POST'])
def login():
    if current_user.is_authenticated:
        return redirect(url_for('dashboard'))

    if request.method == 'POST':
        username = request.form.get('username', '').strip()
        password = request.form.get('password', '')
        user = User.query.filter_by(username=username).first()
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


# ═══════════════════════════════════════════════════════════════
#  ERROR HANDLERS
# ═══════════════════════════════════════════════════════════════

@app.errorhandler(403)
def forbidden(e):
    return render_template('errors/403.html'), 403


@app.errorhandler(404)
def not_found(e):
    return render_template('errors/404.html'), 404


@app.errorhandler(413)
def payload_too_large(e):
    flash('Upload rejected: file exceeds the 2 MB size limit.', 'error')
    return redirect(request.referrer or url_for('dashboard'))


@app.errorhandler(500)
def internal_error(e):
    db.session.rollback()   # Reset any broken transaction
    return render_template('errors/500.html'), 500


# ═══════════════════════════════════════════════════════════════
#  JINJA2 FILTERS
# ═══════════════════════════════════════════════════════════════

@app.template_filter('timesince')
def timesince_filter(dt: datetime) -> str:
    diff    = datetime.utcnow() - dt
    seconds = diff.total_seconds()
    if seconds < 60:
        return 'just now'
    if seconds < 3600:
        m = int(seconds // 60);   return f'{m} min{"s" if m != 1 else ""} ago'
    if seconds < 86400:
        h = int(seconds // 3600); return f'{h} hour{"s" if h != 1 else ""} ago'
    d = int(seconds // 86400);    return f'{d} day{"s" if d != 1 else ""} ago'


# ═══════════════════════════════════════════════════════════════
#  BOOTSTRAP & RUN
# ═══════════════════════════════════════════════════════════════

with app.app_context():
    # 1. Create any brand-new tables (Match, etc.)
    db.create_all()

    # 2. Lightweight schema migrations
    #    db.create_all() never adds columns to *existing* tables.
    #    We use PRAGMA table_info + ALTER TABLE so the app works
    #    against both a fresh DB and an existing one without Flask-Migrate.
    def _column_exists(inspector, table: str, column: str) -> bool:
        return any(c['name'] == column
                   for c in inspector.get_columns(table))

    inspector = sa_inspect(db.engine)

    with db.engine.begin() as conn:
        # item.created_at  ── back-filled from date_reported
        if not _column_exists(inspector, 'item', 'created_at'):
            conn.execute(text(
                "ALTER TABLE item ADD COLUMN created_at DATETIME"
            ))
            conn.execute(text(
                "UPDATE item SET created_at = date_reported"
            ))

        # user.created_at  ── back-filled to current time
        if not _column_exists(inspector, 'user', 'created_at'):
            conn.execute(text(
                "ALTER TABLE user ADD COLUMN created_at DATETIME"
            ))
            conn.execute(text(
                "UPDATE user SET created_at = CURRENT_TIMESTAMP"
            ))

if __name__ == '__main__':
    app.run(debug=True, port=5000)
