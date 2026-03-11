import os
from datetime import datetime
from flask import Flask, render_template, request, redirect, url_for, flash, session
from flask_sqlalchemy import SQLAlchemy
from flask_login import LoginManager, UserMixin, login_user, logout_user, login_required, current_user
from werkzeug.security import generate_password_hash, check_password_hash
from werkzeug.utils import secure_filename

# ── App Configuration ────────────────────────────────────────────
app = Flask(__name__)
app.config['SECRET_KEY'] = 'kg-portal-secret-key-2026'
app.config['SQLALCHEMY_DATABASE_URI'] = 'sqlite:///kg_portal.db'
app.config['SQLALCHEMY_TRACK_MODIFICATIONS'] = False
app.config['UPLOAD_FOLDER'] = os.path.join(app.root_path, 'static', 'uploads')
app.config['MAX_CONTENT_LENGTH'] = 5 * 1024 * 1024  # 5MB max upload

os.makedirs(app.config['UPLOAD_FOLDER'], exist_ok=True)

db = SQLAlchemy(app)
login_manager = LoginManager(app)
login_manager.login_view = 'login'
login_manager.login_message = 'Please sign in to access this page.'
login_manager.login_message_category = 'info'

ALLOWED_EXTENSIONS = {'png', 'jpg', 'jpeg', 'gif', 'webp'}

def allowed_file(filename):
    return '.' in filename and filename.rsplit('.', 1)[1].lower() in ALLOWED_EXTENSIONS


# ── Models ───────────────────────────────────────────────────────
class User(UserMixin, db.Model):
    id = db.Column(db.Integer, primary_key=True)
    username = db.Column(db.String(80), unique=True, nullable=False)
    email = db.Column(db.String(120), unique=True, nullable=False)
    password_hash = db.Column(db.String(256), nullable=False)
    created_at = db.Column(db.DateTime, default=datetime.utcnow)
    items = db.relationship('Item', backref='reporter', lazy=True)

    def set_password(self, password):
        self.password_hash = generate_password_hash(password)

    def check_password(self, password):
        return check_password_hash(self.password_hash, password)


class Item(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    title = db.Column(db.String(200), nullable=False)
    description = db.Column(db.Text, nullable=False)
    status = db.Column(db.String(10), nullable=False, default='LOST')        # LOST or FOUND
    category = db.Column(db.String(20), nullable=False, default='OTHER')     # ELECTRONICS, DOCUMENTS, KEYS, CLOTHING, OTHER
    location = db.Column(db.String(255), nullable=False)
    image_filename = db.Column(db.String(255), nullable=True)
    # Handover Logic
    handover_status = db.Column(db.String(20), nullable=True)                # LEFT_AT_LOCATION, WITH_FINDER, SECURITY
    handover_details = db.Column(db.Text, nullable=True)
    receiver_name = db.Column(db.String(100), nullable=True)
    receiver_contact = db.Column(db.String(20), nullable=True)
    # Meta
    date_reported = db.Column(db.DateTime, default=datetime.utcnow)
    user_id = db.Column(db.Integer, db.ForeignKey('user.id'), nullable=False)

    @property
    def status_label(self):
        return 'Lost' if self.status == 'LOST' else 'Found'

    @property
    def category_label(self):
        labels = {
            'ELECTRONICS': 'Electronics & Gadgets',
            'DOCUMENTS': 'IDs & Documents',
            'KEYS': 'Keys & Access Cards',
            'CLOTHING': 'Clothing & Bags',
            'OTHER': 'Other',
        }
        return labels.get(self.category, 'Other')

    @property
    def handover_label(self):
        labels = {
            'LEFT_AT_LOCATION': 'Left at Location',
            'WITH_FINDER': 'With Finder',
            'SECURITY': 'Handed to Security/Staff',
        }
        return labels.get(self.handover_status, '')


@login_manager.user_loader
def load_user(user_id):
    return User.query.get(int(user_id))


# ── Routes ───────────────────────────────────────────────────────

# Dashboard
@app.route('/')
def dashboard():
    total_lost = Item.query.filter_by(status='LOST').count()
    total_found = Item.query.filter_by(status='FOUND').count()
    recent_items = Item.query.order_by(Item.date_reported.desc()).limit(6).all()

    my_items = []
    if current_user.is_authenticated:
        my_items = Item.query.filter_by(user_id=current_user.id).order_by(Item.date_reported.desc()).all()

    return render_template('dashboard.html',
        total_lost=total_lost,
        total_found=total_found,
        recent_items=recent_items,
        my_items=my_items
    )


# Item Feed
@app.route('/feed')
def feed():
    query = request.args.get('q', '').strip()
    status_filter = request.args.get('status', '')

    items = Item.query.order_by(Item.date_reported.desc())

    if query:
        items = items.filter(
            db.or_(
                Item.title.ilike(f'%{query}%'),
                Item.description.ilike(f'%{query}%'),
                Item.location.ilike(f'%{query}%')
            )
        )
    if status_filter in ('LOST', 'FOUND'):
        items = items.filter_by(status=status_filter)

    return render_template('feed.html', items=items.all(), query=query, current_status=status_filter)


# Item Detail
@app.route('/item/<int:item_id>')
def item_detail(item_id):
    item = Item.query.get_or_404(item_id)
    return render_template('detail.html', item=item)


# Report Item
@app.route('/report', methods=['GET', 'POST'])
@login_required
def report():
    if request.method == 'POST':
        title = request.form.get('title', '').strip()
        description = request.form.get('description', '').strip()
        status = request.form.get('status', 'LOST')
        category = request.form.get('category', 'OTHER')
        location = request.form.get('location', '').strip()
        handover_status = request.form.get('handover_status', '').strip() or None
        handover_details = request.form.get('handover_details', '').strip() or None
        receiver_name = request.form.get('receiver_name', '').strip() or None
        receiver_contact = request.form.get('receiver_contact', '').strip() or None

        if not title or not description or not location:
            flash('Please fill in all required fields.', 'error')
            return redirect(url_for('report'))

        image_filename = None
        if 'image' in request.files:
            file = request.files['image']
            if file and file.filename and allowed_file(file.filename):
                filename = secure_filename(f"{datetime.utcnow().strftime('%Y%m%d%H%M%S')}_{file.filename}")
                file.save(os.path.join(app.config['UPLOAD_FOLDER'], filename))
                image_filename = filename

        item = Item(
            title=title, description=description, status=status,
            category=category, location=location, image_filename=image_filename,
            handover_status=handover_status, handover_details=handover_details,
            receiver_name=receiver_name, receiver_contact=receiver_contact,
            user_id=current_user.id
        )
        db.session.add(item)
        db.session.commit()

        flash(f'Your {item.status_label.lower()} item report was submitted successfully!', 'success')
        return redirect(url_for('feed'))

    return render_template('report.html')


# Edit Item
@app.route('/item/<int:item_id>/edit', methods=['GET', 'POST'])
@login_required
def edit_item(item_id):
    item = Item.query.get_or_404(item_id)
    if item.user_id != current_user.id:
        flash('Permission denied.', 'error')
        return redirect(url_for('item_detail', item_id=item.id))

    if request.method == 'POST':
        item.title = request.form.get('title', item.title).strip()
        item.description = request.form.get('description', item.description).strip()
        item.status = request.form.get('status', item.status)
        item.category = request.form.get('category', item.category)
        item.location = request.form.get('location', item.location).strip()
        item.handover_status = request.form.get('handover_status', '').strip() or None
        item.handover_details = request.form.get('handover_details', '').strip() or None
        item.receiver_name = request.form.get('receiver_name', '').strip() or None
        item.receiver_contact = request.form.get('receiver_contact', '').strip() or None

        if 'image' in request.files:
            file = request.files['image']
            if file and file.filename and allowed_file(file.filename):
                filename = secure_filename(f"{datetime.utcnow().strftime('%Y%m%d%H%M%S')}_{file.filename}")
                file.save(os.path.join(app.config['UPLOAD_FOLDER'], filename))
                item.image_filename = filename

        db.session.commit()
        flash('Item updated successfully.', 'success')
        return redirect(url_for('item_detail', item_id=item.id))

    return render_template('edit.html', item=item)


# Delete Item
@app.route('/item/<int:item_id>/delete', methods=['POST'])
@login_required
def delete_item(item_id):
    item = Item.query.get_or_404(item_id)
    if item.user_id != current_user.id:
        flash('Permission denied.', 'error')
        return redirect(url_for('item_detail', item_id=item.id))

    db.session.delete(item)
    db.session.commit()
    flash('Item deleted successfully.', 'success')
    return redirect(url_for('feed'))


# Auth: Register
@app.route('/register', methods=['GET', 'POST'])
def register():
    if current_user.is_authenticated:
        return redirect(url_for('dashboard'))

    if request.method == 'POST':
        username = request.form.get('username', '').strip()
        email = request.form.get('email', '').strip()
        password = request.form.get('password', '')
        confirm = request.form.get('confirm', '')

        errors = []
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
        flash('Registration successful. Welcome!', 'success')
        return redirect(url_for('dashboard'))

    return render_template('register.html')


# Auth: Login
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
            next_page = request.args.get('next')
            return redirect(next_page or url_for('dashboard'))

        flash('Invalid username or password.', 'error')

    return render_template('login.html')


# Auth: Logout
@app.route('/logout')
@login_required
def logout():
    logout_user()
    flash('You have been logged out.', 'info')
    return redirect(url_for('dashboard'))


# ── Jinja Filters ────────────────────────────────────────────────
@app.template_filter('timesince')
def timesince_filter(dt):
    now = datetime.utcnow()
    diff = now - dt
    seconds = diff.total_seconds()
    if seconds < 60:
        return 'just now'
    elif seconds < 3600:
        mins = int(seconds // 60)
        return f'{mins} min{"s" if mins != 1 else ""}'
    elif seconds < 86400:
        hrs = int(seconds // 3600)
        return f'{hrs} hour{"s" if hrs != 1 else ""}'
    else:
        days = int(seconds // 86400)
        return f'{days} day{"s" if days != 1 else ""}'


# ── DB Initialization & Run ──────────────────────────────────────
with app.app_context():
    db.create_all()

if __name__ == '__main__':
    app.run(debug=True, port=5000)
