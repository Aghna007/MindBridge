import json
from datetime import datetime
from flask import Flask, render_template, request, redirect, url_for, session, flash
from flask_sqlalchemy import SQLAlchemy
from werkzeug.security import generate_password_hash, check_password_hash

# Local Modules
from ml_model import predict_wellbeing
from recom import generate_recommendation

app = Flask(__name__)
app.secret_key = 'mindbridge_secret_key_123'

# SQLite Database Setup
app.config['SQLALCHEMY_DATABASE_URI'] = 'sqlite:///mindbridge.db'
app.config['SQLALCHEMY_TRACK_MODIFICATIONS'] = False

db = SQLAlchemy(app)

# ---------------------------------------------------------
# 1. DATABASE MODELS (Users & Assessments)
# ---------------------------------------------------------

class User(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    name = db.Column(db.String(100), nullable=False)
    email = db.Column(db.String(100), unique=True, nullable=False)
    password_hash = db.Column(db.String(200), nullable=False)
    
    assessments = db.relationship('Assessment', backref='user', lazy=True, cascade="all, delete-orphan")

    def __repr__(self):
        return f'<User {self.name}>'


class Assessment(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    user_id = db.Column(db.Integer, db.ForeignKey('user.id'), nullable=False)
    date = db.Column(db.DateTime, default=datetime.utcnow)
    
    responses = db.Column(db.Text, nullable=False) 
    risk_score = db.Column(db.Float, nullable=False)
    risk_level = db.Column(db.String(50), nullable=False)
    top_factors = db.Column(db.String(255), nullable=True)
    recommendations = db.Column(db.Text, nullable=True)

    def __repr__(self):
        return f'<Assessment {self.id} - Risk: {self.risk_level}>'


with app.app_context():
    db.create_all()


# ---------------------------------------------------------
# 2. AUTHENTICATION ROUTES (Register, Login, Logout)
# ---------------------------------------------------------

@app.route('/')
def home():
    user_name = session.get('user_name')
    return render_template('index.html', user_name=user_name)


@app.route('/register', methods=['GET', 'POST'])
def register():
    if request.method == 'POST':
        name = request.form.get('name', '').strip()
        email = request.form.get('email', '').strip().lower()
        password = request.form.get('password', '').strip()

        if not name or not email or not password:
            flash("All fields are required!", "danger")
            return render_template('register.html')

        existing_user = User.query.filter_by(email=email).first()
        if existing_user:
            flash("Email is already registered! Please log in.", "warning")
            return render_template('register.html')

        hashed_password = generate_password_hash(password, method='scrypt')

        new_user = User(name=name, email=email, password_hash=hashed_password)
        db.session.add(new_user)
        db.session.commit()

        session['user_id'] = new_user.id
        session['user_name'] = new_user.name

        flash("Account created successfully! Welcome to MindBridge.", "success")
        return redirect(url_for('dashboard'))

    return render_template('register.html')


@app.route('/login', methods=['GET', 'POST'])
def login():
    if request.method == 'POST':
        email = request.form.get('email', '').strip().lower()
        password = request.form.get('password', '').strip()

        if not email or not password:
            flash("Please enter both email and password.", "danger")
            return render_template('login.html')

        user = User.query.filter_by(email=email).first()

        if user and check_password_hash(user.password_hash, password):
            session['user_id'] = user.id
            session['user_name'] = user.name
            flash("Logged in successfully!", "success")
            return redirect(url_for('dashboard'))
        else:
            flash("Invalid email or password. Please try again.", "danger")
            return render_template('login.html')

    return render_template('login.html')


@app.route('/logout')
def logout():
    session.clear()
    flash("You have been logged out.", "info")
    return redirect(url_for('home'))


# ---------------------------------------------------------
# 3. CORE APP ROUTES (Dashboard, Assessment, Result, Support)
# ---------------------------------------------------------

@app.route('/dashboard')
def dashboard():
    if 'user_id' not in session:
        flash("Please log in to access your dashboard.", "warning")
        return redirect(url_for('login'))

    user = User.query.get(session['user_id'])
    user_assessments = Assessment.query.filter_by(user_id=user.id).order_by(Assessment.date.desc()).all()

    return render_template('dashboard.html', user=user, assessments=user_assessments)


@app.route('/assessment', methods=['GET', 'POST'])
def assessment():
    if 'user_id' not in session:
        flash("Please log in to take an assessment.", "warning")
        return redirect(url_for('login'))

    if request.method == 'POST':
        try:
            # 1. Collect 11 Form Responses for ML Model
            responses_data = {
                'Gender': request.form.get('gender'),
                'Age': int(request.form.get('Age', 0)),
                'Academic Pressure': int(request.form.get('Academic Pressure', 0)),
                'CGPA': float(request.form.get('CGPA', 0.0)),
                'Study Satisfaction': int(request.form.get('Study Satisfaction', 0)),
                'Sleep Duration': request.form.get('Sleep Duration'),
                'Dietary Habits': request.form.get('Dietary Habits'),
                'Degree': request.form.get('Degree'),
                'Work/Study Hours': int(request.form.get('Work/Study Hours', 0)),
                'Financial Stress': int(request.form.get('Financial Stress', 0)),
                'Family History of Mental Illness': request.form.get('Family History of Mental Illness')
            }

            # 2. Predict using ML Model
            prediction = predict_wellbeing(responses_data)

            # Handle top_factors
            factors = prediction.get('important_factors') or prediction.get('top_factors', [])
            if isinstance(factors, list):
                factors_str = ", ".join(factors)
            else:
                factors_str = str(factors)

            # 3. Generate Gemini AI Recommendation using recom.py
            ai_rec = generate_recommendation(
                risk_score=prediction['risk_score'],
                risk_level=prediction['risk_level'],
                important_factors=factors
            )

            # 4. Store Assessment in DB (including AI recommendations)
            new_assessment = Assessment(
                user_id=session['user_id'],
                responses=json.dumps(responses_data),
                risk_score=prediction['risk_score'],
                risk_level=prediction['risk_level'],
                top_factors=factors_str,
                recommendations=json.dumps(ai_rec)
            )
            db.session.add(new_assessment)
            db.session.commit()

            return redirect(url_for('result', id=new_assessment.id))

        except Exception as e:
            flash(f"Error processing assessment: {str(e)}", "danger")
            return render_template('assessment.html')

    return render_template('assessment.html')


@app.route('/result/<int:id>')
def result(id):
    assessment = Assessment.query.get_or_404(id)
    
    try:
        rec_data = json.loads(assessment.recommendations)
    except Exception:
        rec_data = {"summary": assessment.recommendations, "recommendations": []}

    return render_template('result.html', assessment=assessment, rec=rec_data)


@app.route('/support')
def support():
    return render_template('support.html')


if __name__ == '__main__':
    app.run(debug=True)