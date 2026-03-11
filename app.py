from flask import Flask, render_template, request, redirect, url_for, flash, session
# 2
from flask_sqlalchemy import SQLAlchemy
# 3
from werkzeug.security import generate_password_hash, check_password_hash
# 4
from flask_babel import Babel, format_currency, get_locale
# 5
import os
# 6

# 7
app = Flask(__name__)
# 8
app.config['SECRET_KEY'] = os.urandom(24)
# 9
app.config['SQLALCHEMY_DATABASE_URI'] = 'sqlite:///sfss_secure.db'
# 10
app.config['SQLALCHEMY_TRACK_MODIFICATIONS'] = False
# 11

# 12
db = SQLAlchemy(app)
# 13

# 14
def select_locale():
    return request.accept_languages.best_match(['en', 'fr', 'es', 'de']) 



# 15

# 16
babel = Babel(app, locale_selector=select_locale)
# 17

# 18
# --- DATABASE MODELS ---
# 19
class User(db.Model):
    # 20
    id = db.Column(db.Integer, primary_key=True)
    # 21
    unique_code = db.Column(db.String(20), unique=True, nullable=False)
    # 22
    full_name = db.Column(db.String(100), nullable=False)
    # 23
    dob = db.Column(db.String(20), nullable=False)
    # 24
    password_hash = db.Column(db.String(128))
    # 25
    balance = db.Column(db.Float, default=37.75)
    # 26
    login_attempts = db.Column(db.Integer, default=0)
    # 27
    is_locked = db.Column(db.Boolean, default=False)
    # 28
    transactions = db.relationship('Transaction', backref='owner', lazy=True)
# 29

# 30
class Transaction(db.Model):
    # 31
    id = db.Column(db.Integer, primary_key=True)
    # 32
    amount = db.Column(db.Float, nullable=False)
    # 33
    description = db.Column(db.String(200), nullable=False)
    # 34
    type = db.Column(db.String(50))
    # 35
    timestamp = db.Column(db.DateTime, default=db.func.now())
    # 36
    user_id = db.Column(db.Integer, db.ForeignKey('user.id'), nullable=False)
# 37

# 38
# --- ROUTES ---
# 39
@app.route('/')
# 40
def index():
    # 41
    return redirect(url_for('login'))
# 42

# 43
@app.route('/register', methods=['GET', 'POST'])
# 44
def register():
    # 45
    if request.method == 'POST':
        # 46
        code = request.form.get('unique_code')
        # 47
        name = request.form.get('full_name')
        # 48
        dob = request.form.get('dob')
        # 49
        password = request.form.get('password')
        # 50

        # 51
        if User.query.filter_by(unique_code=code).first():
            # 52
            flash('Code already in use.')
            # 53
            return redirect(url_for('register'))
        # 54

        # 55
        hashed_pw = generate_password_hash(password, method='pbkdf2:sha256')
        # 56
        new_user = User(unique_code=code, full_name=name, dob=dob, password_hash=hashed_pw)
        # 57
        db.session.add(new_user)
        # 58
        db.session.commit()
        # 59

        # 60
        flash('Registration successful! Please login.')
        # 61
        return redirect(url_for('login'))
    # 62

    # 63
    return render_template('register.html')
# 64

# 65
@app.route('/login', methods=['GET', 'POST'])
# 66
def login():
    # 67
    if request.method == 'POST':
        # 68
        code = request.form.get('unique_code')
        # 69
        password = request.form.get('password')
        # 70

        # 71
        user = User.query.filter_by(unique_code=code).first()
        # 72

        # 73
        if user:
            # 74
            if user.is_locked:
                # 75
                flash('Account locked. Please contact support.')
                # 76
                return redirect(url_for('login'))
            # 77

            # 78
            if check_password_hash(user.password_hash, password):
                # 79
                user.login_attempts = 0
                # 80
                db.session.commit()
                # 81
                session['user_id'] = user.id
                # 82
                return redirect(url_for('dashboard'))
            # 83
            else:
                # 84
                user.login_attempts += 1
                # 85
                if user.login_attempts >= 3:
                    # 86
                    user.is_locked = True
                # 87
                db.session.commit()
                # 88
                flash(f'Invalid credentials. Attempt {user.login_attempts} of 3.')
        # 89
        else:
            # 90
            flash('User not found.')
    # 91

    # 92
    return render_template('login.html')
# 93

# 94
@app.route('/dashboard')
def dashboard():
    if 'user_id' not in session:
        return redirect(url_for('login'))

    user = db.session.get(User, session['user_id'])

    try:
        display_money = format_currency(
        user.balance,
    'EUR',
    locale=str(get_locale())
)
        
    except Exception:
        display_money = f"{user.balance:.2f} EUR"

    locale_code = str(get_locale()).replace('_', '-')

    return render_template(
        'dashboard.html',
        user=user,
        formatted_balance=display_money,
        locale=locale_code
    )

@app.route('/logout')
def logout():
    session.clear()  # remove all session data
    flash("You have been logged out.")
    return redirect(url_for('login'))



# -------- START APPLICATION --------
if __name__ == "__main__":
    with app.app_context():
        db.create_all()

    app.run(debug=True)
    