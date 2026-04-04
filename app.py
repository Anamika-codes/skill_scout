from flask import Flask, render_template, request, redirect, url_for, flash, session, jsonify
from flask_sqlalchemy import SQLAlchemy
from flask_login import LoginManager, UserMixin, login_user, login_required, logout_user, current_user
from werkzeug.security import generate_password_hash, check_password_hash
from flask_wtf.csrf import CSRFProtect
import os
from scripts.prediction.predict_careers import CareerPredictor
from scripts.prediction.college_recommender import CollegeRecommender
import pandas as pd
import numpy as np
from sklearn.ensemble import RandomForestClassifier
from sklearn.preprocessing import StandardScaler
import joblib
import json
import logging
from datetime import datetime, timedelta

# Configure logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

# Initialize Flask app
app = Flask(__name__, 
            template_folder='templates',  # Keep using the existing templates folder for now
            static_folder='static')       # Keep using the existing static folder for now
app.config['SECRET_KEY'] = os.environ.get('SECRET_KEY', 'dev_key_for_development')
app.config['SQLALCHEMY_DATABASE_URI'] = 'sqlite:///skillscout.db'
app.config['SQLALCHEMY_TRACK_MODIFICATIONS'] = False
app.config['WTF_CSRF_ENABLED'] = True
app.config['PERMANENT_SESSION_LIFETIME'] = timedelta(minutes=30)
app.config['SESSION_COOKIE_SECURE'] = False  # Set to False for development (HTTP)
app.config['SESSION_COOKIE_HTTPONLY'] = True
app.config['SESSION_COOKIE_SAMESITE'] = 'Lax'
app.config['SESSION_COOKIE_NAME'] = 'skillscout_session'
app.config['SESSION_COOKIE_PATH'] = '/'
app.config['SESSION_COOKIE_DOMAIN'] = None
app.config['SESSION_REFRESH_EACH_REQUEST'] = True
app.config['SESSION_TYPE'] = 'filesystem'
app.config['SESSION_PERMANENT'] = False  # This ensures session expires when browser closes

# Initialize CSRF protection
csrf = CSRFProtect()
csrf.init_app(app)

# Configure CSRF settings for development
app.config['WTF_CSRF_TIME_LIMIT'] = None  # No time limit for CSRF tokens
app.config['WTF_CSRF_SSL_STRICT'] = False  # Allow CSRF tokens over HTTP for development
app.config['WTF_CSRF_ENABLED'] = True

# CSRF error handler
@app.errorhandler(400)
def handle_csrf_error(e):
    if 'CSRF' in str(e):
        flash('Session expired. Please refresh the page and try again.', 'error')
        return redirect(url_for('profile'))
    return str(e), 400

# Initialize database
db = SQLAlchemy(app)

# Initialize login manager
login_manager = LoginManager()
login_manager.init_app(app)
login_manager.login_view = 'login'
login_manager.session_protection = "strong"  # This will log out the user if the session is invalidated
login_manager.refresh_view = 'login'
login_manager.needs_refresh_message = 'Please login again to continue.'
login_manager.needs_refresh_message_category = 'info'

# Initialize career predictor
career_predictor = CareerPredictor()
career_predictor.load_model()

# Initialize college recommender
college_recommender = CollegeRecommender()
college_recommender.load_data()

# Add the fromjson filter
@app.template_filter('fromjson')
def fromjson_filter(value):
    if isinstance(value, str):
        try:
            return json.loads(value)
        except json.JSONDecodeError:
            return []
    return value

# Add the get_college_recommendations filter
@app.template_filter('get_college_recommendations')
def get_college_recommendations_filter(career_name, tier):
    return get_college_recommendations(career_name, tier)

# User model
class User(UserMixin, db.Model):
    id = db.Column(db.Integer, primary_key=True)
    username = db.Column(db.String(80), unique=True, nullable=False)
    email = db.Column(db.String(120), unique=True, nullable=False)
    password_hash = db.Column(db.String(128))
    profile = db.relationship('UserProfile', backref='user', uselist=False)
    
    def set_password(self, password):
        self.password_hash = generate_password_hash(password)
        
    def check_password(self, password):
        return check_password_hash(self.password_hash, password)

# User profile model
class UserProfile(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    user_id = db.Column(db.Integer, db.ForeignKey('user.id'), nullable=False)
    grading_system = db.Column(db.String(10), default='cgpa')  # 'cgpa' or 'percentage'
    gpa = db.Column(db.Float)  # CGPA (0-10)
    percentage = db.Column(db.Float)  # Percentage (0-100)
    math_score = db.Column(db.Float)
    science_score = db.Column(db.Float)
    english_score = db.Column(db.Float)
    extracurricular_activities = db.Column(db.Integer)
    leadership_roles = db.Column(db.Integer)
    interests = db.Column(db.Text)
    recommended_careers = db.Column(db.Text)
    preferred_location = db.Column(db.String(100))
    budget_range = db.Column(db.String(50))
    preferred_college_tier = db.Column(db.String(50))

# College model
class College(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    name = db.Column(db.String(200), nullable=False)
    location = db.Column(db.String(100))
    tier = db.Column(db.String(50))  # Tier 1, Tier 2, Tier 3
    tuition_fee = db.Column(db.Float)
    acceptance_rate = db.Column(db.Float)
    avg_gpa = db.Column(db.Float)
    programs_offered = db.Column(db.Text)  # JSON string of programs
    career_paths = db.Column(db.Text)  # JSON string of career paths
    ranking = db.Column(db.Integer)
    website = db.Column(db.String(200))
    description = db.Column(db.Text)

# Career-College mapping model
class CareerCollegeMapping(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    career_id = db.Column(db.Integer, db.ForeignKey('career.id'))
    college_id = db.Column(db.Integer, db.ForeignKey('college.id'))
    strength_score = db.Column(db.Float)  # How strong is this college for this career

# Career model
class Career(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    title = db.Column(db.String(100), nullable=False)
    description = db.Column(db.Text)
    required_skills = db.Column(db.Text)
    salary_range = db.Column(db.String(50))
    growth_potential = db.Column(db.String(50))
    education_requirements = db.Column(db.Text)

@login_manager.user_loader
def load_user(user_id):
    return db.session.get(User, int(user_id))

# Routes
@app.route('/')
def index():
    return render_template('index.html')

@app.route('/register', methods=['GET', 'POST'])
def register():
    if request.method == 'POST':
        username = request.form.get('username')
        email = request.form.get('email')
        password = request.form.get('password')
        confirm_password = request.form.get('confirm_password')
        
        logger.info(f"Registration attempt for username: {username}, email: {email}")
        
        # Validate password length
        if len(password) < 8:
            logger.warning(f"Password too short for user: {username}")
            flash('Password must be at least 8 characters long')
            return redirect(url_for('register'))
        
        # Check if passwords match
        if password != confirm_password:
            logger.warning(f"Passwords don't match for user: {username}")
            flash('Passwords do not match')
            return redirect(url_for('register'))
        
        # Check if user already exists
        if User.query.filter_by(username=username).first():
            logger.warning(f"Username already exists: {username}")
            flash('Username already exists')
            return redirect(url_for('register'))
        
        if User.query.filter_by(email=email).first():
            logger.warning(f"Email already registered: {email}")
            flash('Email already registered')
            return redirect(url_for('register'))
        
        try:
            # Create new user
            new_user = User(username=username, email=email)
            new_user.set_password(password)
            db.session.add(new_user)
            db.session.commit()
            
            # Create user profile
            new_profile = UserProfile(user_id=new_user.id)
            db.session.add(new_profile)
            db.session.commit()
            
            logger.info(f"Successfully registered user: {username}")
            flash('Registration successful! Please login.')
            return redirect(url_for('login'))
        except Exception as e:
            logger.error(f"Error during registration for user {username}: {str(e)}")
            db.session.rollback()
            flash('An error occurred during registration. Please try again.')
            return redirect(url_for('register'))
    
    return render_template('register.html')

@app.route('/login', methods=['GET', 'POST'])
def login():
    if request.method == 'POST':
        username = request.form.get('username')
        password = request.form.get('password')
        
        logger.info(f"Login attempt for username: {username}")
        
        user = User.query.filter_by(username=username).first()
        
        if user and user.check_password(password):
            login_user(user)
            logger.info(f"Successful login for user: {username}")
            return redirect(url_for('dashboard'))
        else:
            if not user:
                logger.warning(f"Login failed - user not found: {username}")
            else:
                logger.warning(f"Login failed - incorrect password for user: {username}")
            flash('Invalid username or password')
    
    return render_template('login.html')

@app.route('/logout')
@login_required
def logout():
    logout_user()
    session.clear()
    flash('You have been logged out successfully.')
    return redirect(url_for('login'))

@app.route('/dashboard')
@login_required
def dashboard():
    try:
        if not current_user.profile:
            flash('Please complete your profile to get recommendations.')
            return redirect(url_for('profile'))
            
        # Always generate fresh recommendations to ensure updated scoring system
        recommendations = []
        college_recommendations = []
        
        student_profile = {
            'grading_system': current_user.profile.grading_system or 'cgpa',
            'gpa': current_user.profile.gpa or 0.0,
            'percentage': current_user.profile.percentage or 0.0,
            'math_score': current_user.profile.math_score or 0.0,
            'science_score': current_user.profile.science_score or 0.0,
            'english_score': current_user.profile.english_score or 0.0,
            'extracurricular_activities': current_user.profile.extracurricular_activities or 0,
            'leadership_roles': current_user.profile.leadership_roles or 0,
            'interests': current_user.profile.interests or ''
        }
        results = career_predictor.predict_careers(student_profile)
        if results is not None:
            results = results.sort_values('match_score', ascending=False).head(5)
            current_user.profile.recommended_careers = results.to_json()
            db.session.commit()
            logger.info(f"Dashboard: Generated fresh recommendations with updated scoring: {len(results)} careers")
        
        if results is not None and not results.empty:
            # Sort by match score and take top 5
            results = results.sort_values('match_score', ascending=False).head(5)
            
            # Convert to list of dictionaries with proper formatting
            for idx, (_, row) in enumerate(results.iterrows()):
                career = {
                    'id': idx + 1,  # Generate sequential IDs starting from 1
                    'career': row.get('career', 'Unknown Career'),
                    'category': row.get('category', 'Uncategorized'),
                    'match_score': float(row.get('match_score', 0)),
                    'salary_median': float(row.get('salary_median', 0)) * 83.5,  # Convert to INR
                    'description': row.get('description', 'No description available'),
                    'required_skills': row.get('required_skills', 'No skills specified'),
                    'growth_potential': row.get('growth_potential', 'Unknown'),
                    'education_requirements': row.get('education_requirements', 'Not specified'),
                    'growth_rate': float(row.get('growth_rate', 0)),
                    'market_demand': int(row.get('market_demand', 3))
                }
                recommendations.append(career)
                
                # Get college recommendations for each tier
                career_colleges = []
                for tier in ['Tier 1', 'Tier 2', 'Tier 3']:
                    colleges = get_college_recommendations(career['career'], tier)
                    if colleges:
                        career_colleges.append({
                            'tier': tier,
                            'colleges': colleges
                        })
                
                if career_colleges:
                    college_recommendations.append({
                        'career': career['career'],
                        'tiers': career_colleges
                    })
            
            # Update the user's profile with new recommendations
            current_user.profile.recommended_careers = json.dumps(recommendations)
            db.session.commit()
            
            logger.info(f"Generated {len(recommendations)} career recommendations and {len(college_recommendations)} college recommendations")
            
        return render_template(
            'dashboard.html',
            recommendations=recommendations,
            college_recommendations=college_recommendations
        )
        
    except Exception as e:
        logger.error(f"Error in dashboard: {str(e)}")
        flash('Error generating recommendations. Please try again.')
        return redirect(url_for('profile'))

@app.route('/profile', methods=['GET', 'POST'])
@login_required
@csrf.exempt
def profile():
    if request.method == 'POST':
        logger.info(f"Profile update request received for user: {current_user.username}")
        logger.info(f"Form data: {dict(request.form)}")
        try:
            # Update grading system
            grading_system = request.form.get('grading_system', 'cgpa')
            current_user.profile.grading_system = grading_system
            
            # Update academic scores based on grading system
            if grading_system == 'cgpa':
                gpa = request.form.get('gpa', '')
                current_user.profile.gpa = float(gpa) if gpa.strip() else 0.0
                current_user.profile.percentage = None
            else:  # percentage
                percentage = request.form.get('percentage', '')
                current_user.profile.percentage = float(percentage) if percentage.strip() else 0.0
                current_user.profile.gpa = None
            
            # Update other scores
            math_score = request.form.get('math_score', '')
            current_user.profile.math_score = float(math_score) if math_score.strip() else 0.0
            
            science_score = request.form.get('science_score', '')
            current_user.profile.science_score = float(science_score) if science_score.strip() else 0.0
            
            english_score = request.form.get('english_score', '')
            current_user.profile.english_score = float(english_score) if english_score.strip() else 0.0
            
            extracurricular = request.form.get('extracurricular_activities', '')
            current_user.profile.extracurricular_activities = int(extracurricular) if extracurricular.strip() else 0
            
            leadership = request.form.get('leadership_roles', '')
            current_user.profile.leadership_roles = int(leadership) if leadership.strip() else 0
            
            current_user.profile.interests = request.form.get('interests', '').strip()
            
            db.session.commit()
            flash('Profile updated successfully!')
            
            # Generate career recommendations
            student_profile = {
                'grading_system': current_user.profile.grading_system,
                'gpa': current_user.profile.gpa,
                'percentage': current_user.profile.percentage,
                'math_score': current_user.profile.math_score,
                'science_score': current_user.profile.science_score,
                'english_score': current_user.profile.english_score,
                'extracurricular_activities': current_user.profile.extracurricular_activities,
                'leadership_roles': current_user.profile.leadership_roles,
                'interests': current_user.profile.interests or ''  # Add interests to the profile
            }
            
            logger.info(f"Profile updated. Student profile: {student_profile}")
            
            results = career_predictor.predict_careers(student_profile)
            if results is not None:
                # Sort by match score in descending order and take top 5
                results = results.sort_values('match_score', ascending=False).head(5)
                current_user.profile.recommended_careers = results.to_json()
                db.session.commit()
                logger.info(f"Career recommendations saved: {len(results)} careers")
            else:
                logger.warning("No career recommendations generated")
            
            flash('Profile updated successfully!', 'success')
            logger.info("Profile update completed successfully")
            return redirect(url_for('recommendations'))
        except ValueError as e:
            flash('Please enter valid numbers for all score fields.')
            logger.error(f"Error updating profile: {str(e)}")
            return redirect(url_for('profile'))
    
    return render_template('profile.html')

@app.route('/recommendations')
@login_required
def recommendations():
    try:
        if not current_user.profile:
            flash('Please complete your profile to get recommendations.')
            return redirect(url_for('profile'))
            
        # Always generate fresh recommendations to ensure updated scoring system
        recommendations = []
        college_recommendations = []
        
        student_profile = {
            'grading_system': current_user.profile.grading_system or 'cgpa',
            'gpa': current_user.profile.gpa or 0.0,
            'percentage': current_user.profile.percentage or 0.0,
            'math_score': current_user.profile.math_score or 0.0,
            'science_score': current_user.profile.science_score or 0.0,
            'english_score': current_user.profile.english_score or 0.0,
            'extracurricular_activities': current_user.profile.extracurricular_activities or 0,
            'leadership_roles': current_user.profile.leadership_roles or 0,
            'interests': current_user.profile.interests or ''
        }
        results = career_predictor.predict_careers(student_profile)
        if results is not None:
            results = results.sort_values('match_score', ascending=False).head(5)
            current_user.profile.recommended_careers = results.to_json()
            db.session.commit()
            logger.info(f"Recommendations: Generated fresh recommendations with updated scoring: {len(results)} careers")
        
        logger.info(f"Raw results: {results}")
        
        if results is not None and not results.empty:
            # Sort by match score and take top 5
            results = results.sort_values('match_score', ascending=False).head(5)
            
            logger.info(f"Processed results: {results}")
            
            # Convert to list of dictionaries with proper formatting
            for idx, (_, row) in enumerate(results.iterrows()):
                career = {
                    'id': idx + 1,  # Generate sequential IDs starting from 1
                    'career': row.get('career', 'Unknown Career'),
                    'category': row.get('category', 'Uncategorized'),
                    'match_score': float(row.get('match_score', 0)),
                    'salary_median': float(row.get('salary_median', 0)) * 83.5,  # Convert to INR
                    'description': row.get('description', 'No description available'),
                    'required_skills': row.get('required_skills', 'No skills specified'),
                    'growth_potential': row.get('growth_potential', 'Unknown'),
                    'education_requirements': row.get('education_requirements', 'Not specified'),
                    'growth_rate': float(row.get('growth_rate', 0)),
                    'market_demand': int(row.get('market_demand', 3))
                }
                recommendations.append(career)
                
                # Get college recommendations for each tier
                career_colleges = []
                for tier in ['Tier 1', 'Tier 2', 'Tier 3']:
                    colleges = get_college_recommendations(career['career'], tier)
                    if colleges:
                        career_colleges.append({
                            'tier': tier,
                            'colleges': colleges
                        })
                
                if career_colleges:
                    college_recommendations.append({
                        'career': career['career'],
                        'tiers': career_colleges
                    })
            
            # Update the user's profile with new recommendations
            current_user.profile.recommended_careers = json.dumps(recommendations)
            db.session.commit()
            
            logger.info(f"Generated {len(recommendations)} career recommendations and {len(college_recommendations)} college recommendations")
            logger.info(f"Final recommendations: {recommendations}")
            
        else:
            logger.warning("No results returned from career predictor")
            
        return render_template(
            'recommendations.html',
            recommendations=recommendations,
            college_recommendations=college_recommendations
        )
        
    except Exception as e:
        logger.error(f"Error in recommendations: {str(e)}")
        import traceback
        traceback.print_exc()
        flash('Error loading recommendations. Please try again.')
        return redirect(url_for('profile'))

@app.route('/career/<int:career_id>')
def career_details(career_id):
    career = Career.query.get_or_404(career_id)
    return render_template('career_details.html', career=career)

@app.route('/predict', methods=['POST'])
def predict():
    try:
        data = request.get_json()
        student_profile = {
            'gpa': float(data.get('gpa', 0)),
            'math_score': float(data.get('math_score', 0)),
            'science_score': float(data.get('science_score', 0)),
            'english_score': float(data.get('english_score', 0)),
            'extracurricular_activities': int(data.get('extracurricular_activities', 0)),
            'leadership_roles': int(data.get('leadership_roles', 0))
        }
        
        results = career_predictor.predict_careers(student_profile)
        if results is not None:
            return jsonify({
                'success': True,
                'recommendations': results.head(10).to_dict('records')
            })
        else:
            return jsonify({
                'success': False,
                'error': 'Failed to generate recommendations'
            })
    except Exception as e:
        return jsonify({
            'success': False,
            'error': str(e)
        })

@app.before_request
def before_request():
    if current_user.is_authenticated:
        session.permanent = False  # Ensure session is not permanent
        session.modified = True  # Mark session as modified to refresh it

# Create database tables
def init_db():
    with app.app_context():
        db.create_all()
        
        # Add sample careers if none exist
        if Career.query.count() == 0:
            sample_careers = [
                Career(
                    title='Software Developer',
                    description='Software developers design, develop, and maintain software applications. They write code, debug issues, and collaborate with other team members to create high-quality software products.',
                    required_skills='Programming languages (Java, Python, JavaScript), Web development, Database management',
                    salary_range='₹6,00,000 - ₹15,00,000',
                    growth_potential='High',
                    education_requirements='Bachelor\'s degree in Computer Science or related field'
                ),
                Career(
                    title='Data Scientist',
                    description='Data scientists analyze complex data sets to help organizations make better decisions. They use statistical methods, machine learning, and data visualization to extract insights from data.',
                    required_skills='Python, R, SQL, Machine Learning, Statistics',
                    salary_range='₹8,00,000 - ₹20,00,000',
                    growth_potential='Very High',
                    education_requirements='Bachelor\'s or Master\'s degree in Computer Science, Statistics, or related field'
                ),
                Career(
                    title='AI Engineer',
                    description='AI engineers build and implement artificial intelligence systems. They develop machine learning models, natural language processing systems, and computer vision applications.',
                    required_skills='Python, TensorFlow, PyTorch, Machine Learning, Deep Learning',
                    salary_range='₹10,00,000 - ₹25,00,000',
                    growth_potential='Very High',
                    education_requirements='Bachelor\'s or Master\'s degree in Computer Science, AI, or related field'
                ),
                Career(
                    title='Cybersecurity Specialist',
                    description='Cybersecurity specialists protect computer systems and networks from cyber threats. They implement security measures, monitor for breaches, and respond to security incidents.',
                    required_skills='Network Security, Ethical Hacking, Security Tools, Incident Response',
                    salary_range='₹7,00,000 - ₹18,00,000',
                    growth_potential='High',
                    education_requirements='Bachelor\'s degree in Computer Science, Cybersecurity, or related field'
                ),
                Career(
                    title='IT Consultant',
                    description='IT consultants advise organizations on how to use information technology to meet their business objectives. They analyze IT systems and recommend improvements.',
                    required_skills='Business Analysis, IT Strategy, Project Management, Technical Knowledge',
                    salary_range='₹8,00,000 - ₹20,00,000',
                    growth_potential='High',
                    education_requirements='Bachelor\'s degree in Computer Science, IT, or Business with IT focus'
                )
            ]
            
            for career in sample_careers:
                db.session.add(career)
            
            db.session.commit()

def get_college_recommendations(career_name, tier):
    # Career-specific college data
    career_colleges = {
        'Software Developer': {
            'Tier 1': [
                {
                    'name': 'Indian Institute of Technology (IIT) - Multiple Locations',
                    'location': 'Mumbai, Delhi, Bangalore, Chennai, Kanpur, Kharagpur',
                    'fees': '₹2,00,000 - ₹3,00,000 per annum',
                    'acceptance_rate': '0.1% - 0.5%',
                    'avg_gpa': 9.5,
                    'programs': ['B.Tech Computer Science', 'B.Tech Information Technology'],
                    'ranking': 'Top 5 in Engineering'
                },
                {
                    'name': 'National Institute of Technology (NIT) - Multiple Locations',
                    'location': 'Warangal, Trichy, Surathkal, Calicut, Rourkela',
                    'fees': '₹1,50,000 - ₹2,50,000 per annum',
                    'acceptance_rate': '1% - 3%',
                    'avg_gpa': 9.0,
                    'programs': ['B.Tech Computer Science', 'B.Tech Information Technology'],
                    'ranking': 'Top 20 in Engineering'
                }
            ],
            'Tier 2': [
                {
                    'name': 'BITS Pilani',
                    'location': 'Pilani, Goa, Hyderabad',
                    'fees': '₹4,00,000 - ₹5,00,000 per annum',
                    'acceptance_rate': '5% - 10%',
                    'avg_gpa': 8.5,
                    'programs': ['B.E. Computer Science', 'B.E. Information Technology'],
                    'ranking': 'Top 10 in Engineering'
                },
                {
                    'name': 'VIT University',
                    'location': 'Vellore, Chennai, Bhopal',
                    'fees': '₹2,50,000 - ₹3,50,000 per annum',
                    'acceptance_rate': '15% - 25%',
                    'avg_gpa': 8.0,
                    'programs': ['B.Tech Computer Science', 'B.Tech Information Technology'],
                    'ranking': 'Top 30 in Engineering'
                }
            ],
            'Tier 3': [
                {
                    'name': 'Manipal Institute of Technology',
                    'location': 'Manipal, Karnataka',
                    'fees': '₹3,00,000 - ₹4,00,000 per annum',
                    'acceptance_rate': '30% - 40%',
                    'avg_gpa': 7.5,
                    'programs': ['B.Tech Computer Science', 'B.Tech Information Technology'],
                    'ranking': 'Top 50 in Engineering'
                }
            ]
        },
        'Data Scientist': {
            'Tier 1': [
                {
                    'name': 'Indian Institute of Technology (IIT) - Multiple Locations',
                    'location': 'Mumbai, Delhi, Bangalore, Chennai, Kanpur, Kharagpur',
                    'fees': '₹2,00,000 - ₹3,00,000 per annum',
                    'acceptance_rate': '0.1% - 0.5%',
                    'avg_gpa': 9.5,
                    'programs': ['B.Tech Computer Science', 'B.Tech Data Science'],
                    'ranking': 'Top 5 in Engineering'
                },
                {
                    'name': 'Indian Statistical Institute (ISI)',
                    'location': 'Kolkata, Bangalore, Delhi',
                    'fees': '₹1,00,000 - ₹2,00,000 per annum',
                    'acceptance_rate': '0.5% - 1%',
                    'avg_gpa': 9.0,
                    'programs': ['B.Stat', 'M.Stat', 'M.Tech in Computer Science'],
                    'ranking': 'Top 10 in Statistics'
                }
            ],
            'Tier 2': [
                {
                    'name': 'BITS Pilani',
                    'location': 'Pilani, Goa, Hyderabad',
                    'fees': '₹4,00,000 - ₹5,00,000 per annum',
                    'acceptance_rate': '5% - 10%',
                    'avg_gpa': 8.5,
                    'programs': ['B.E. Computer Science', 'M.Sc. Statistics'],
                    'ranking': 'Top 10 in Engineering'
                }
            ],
            'Tier 3': [
                {
                    'name': 'Christ University',
                    'location': 'Bangalore',
                    'fees': '₹2,00,000 - ₹3,00,000 per annum',
                    'acceptance_rate': '25% - 35%',
                    'avg_gpa': 7.5,
                    'programs': ['B.Sc. Computer Science', 'B.Sc. Statistics'],
                    'ranking': 'Top 50 in Science'
                }
            ]
        },
        'AI Engineer': {
            'Tier 1': [
                {
                    'name': 'Indian Institute of Technology (IIT) - Multiple Locations',
                    'location': 'Mumbai, Delhi, Bangalore, Chennai, Kanpur, Kharagpur',
                    'fees': '₹2,00,000 - ₹3,00,000 per annum',
                    'acceptance_rate': '0.1% - 0.5%',
                    'avg_gpa': 9.5,
                    'programs': ['B.Tech Computer Science', 'B.Tech AI/ML'],
                    'ranking': 'Top 5 in Engineering'
                },
                {
                    'name': 'International Institute of Information Technology (IIIT)',
                    'location': 'Bangalore, Hyderabad, Delhi',
                    'fees': '₹3,00,000 - ₹4,00,000 per annum',
                    'acceptance_rate': '1% - 3%',
                    'avg_gpa': 9.0,
                    'programs': ['B.Tech Computer Science', 'B.Tech AI/ML'],
                    'ranking': 'Top 15 in Engineering'
                }
            ],
            'Tier 2': [
                {
                    'name': 'BITS Pilani',
                    'location': 'Pilani, Goa, Hyderabad',
                    'fees': '₹4,00,000 - ₹5,00,000 per annum',
                    'acceptance_rate': '5% - 10%',
                    'avg_gpa': 8.5,
                    'programs': ['B.E. Computer Science', 'M.E. Computer Science'],
                    'ranking': 'Top 10 in Engineering'
                }
            ],
            'Tier 3': [
                {
                    'name': 'SRM Institute of Science and Technology',
                    'location': 'Chennai, Delhi, Sonepat',
                    'fees': '₹2,50,000 - ₹3,50,000 per annum',
                    'acceptance_rate': '30% - 40%',
                    'avg_gpa': 7.5,
                    'programs': ['B.Tech Computer Science', 'B.Tech AI/ML'],
                    'ranking': 'Top 50 in Engineering'
                }
            ]
        },
        'Cybersecurity Specialist': {
            'Tier 1': [
                {
                    'name': 'Indian Institute of Technology (IIT) - Multiple Locations',
                    'location': 'Mumbai, Delhi, Bangalore, Chennai, Kanpur, Kharagpur',
                    'fees': '₹2,00,000 - ₹3,00,000 per annum',
                    'acceptance_rate': '0.1% - 0.5%',
                    'avg_gpa': 9.5,
                    'programs': ['B.Tech Computer Science', 'B.Tech Cybersecurity'],
                    'ranking': 'Top 5 in Engineering'
                },
                {
                    'name': 'National Institute of Technology (NIT) - Multiple Locations',
                    'location': 'Warangal, Trichy, Surathkal, Calicut, Rourkela',
                    'fees': '₹1,50,000 - ₹2,50,000 per annum',
                    'acceptance_rate': '1% - 3%',
                    'avg_gpa': 9.0,
                    'programs': ['B.Tech Computer Science', 'B.Tech Information Security'],
                    'ranking': 'Top 20 in Engineering'
                }
            ],
            'Tier 2': [
                {
                    'name': 'BITS Pilani',
                    'location': 'Pilani, Goa, Hyderabad',
                    'fees': '₹4,00,000 - ₹5,00,000 per annum',
                    'acceptance_rate': '5% - 10%',
                    'avg_gpa': 8.5,
                    'programs': ['B.E. Computer Science', 'M.E. Information Security'],
                    'ranking': 'Top 10 in Engineering'
                }
            ],
            'Tier 3': [
                {
                    'name': 'Amrita School of Engineering',
                    'location': 'Coimbatore, Bangalore, Chennai',
                    'fees': '₹2,50,000 - ₹3,50,000 per annum',
                    'acceptance_rate': '25% - 35%',
                    'avg_gpa': 7.5,
                    'programs': ['B.Tech Computer Science', 'B.Tech Cybersecurity'],
                    'ranking': 'Top 40 in Engineering'
                }
            ]
        },
        'IT Consultant': {
            'Tier 1': [
                {
                    'name': 'Indian Institute of Technology (IIT) - Multiple Locations',
                    'location': 'Mumbai, Delhi, Bangalore, Chennai, Kanpur, Kharagpur',
                    'fees': '₹2,00,000 - ₹3,00,000 per annum',
                    'acceptance_rate': '0.1% - 0.5%',
                    'avg_gpa': 9.5,
                    'programs': ['B.Tech Computer Science', 'B.Tech Information Technology'],
                    'ranking': 'Top 5 in Engineering'
                },
                {
                    'name': 'Indian Institute of Management (IIM) - Multiple Locations',
                    'location': 'Ahmedabad, Bangalore, Calcutta, Lucknow',
                    'fees': '₹15,00,000 - ₹25,00,000 per annum',
                    'acceptance_rate': '0.1% - 0.5%',
                    'avg_gpa': 9.5,
                    'programs': ['MBA', 'PGDM'],
                    'ranking': 'Top 5 in Management'
                }
            ],
            'Tier 2': [
                {
                    'name': 'BITS Pilani',
                    'location': 'Pilani, Goa, Hyderabad',
                    'fees': '₹4,00,000 - ₹5,00,000 per annum',
                    'acceptance_rate': '5% - 10%',
                    'avg_gpa': 8.5,
                    'programs': ['B.E. Computer Science', 'MBA'],
                    'ranking': 'Top 10 in Engineering'
                }
            ],
            'Tier 3': [
                {
                    'name': 'Symbiosis Institute of Business Management',
                    'location': 'Pune, Bangalore, Hyderabad',
                    'fees': '₹8,00,000 - ₹12,00,000 per annum',
                    'acceptance_rate': '10% - 20%',
                    'avg_gpa': 7.5,
                    'programs': ['MBA', 'PGDM'],
                    'ranking': 'Top 30 in Management'
                }
            ]
        },
        'Technical Writer': {
            'Tier 1': [
                {
                    'name': 'Indian Institute of Technology (IIT) - Multiple Locations',
                    'location': 'Mumbai, Delhi, Bangalore, Chennai, Kanpur, Kharagpur',
                    'fees': '₹2,00,000 - ₹3,00,000 per annum',
                    'acceptance_rate': '0.1% - 0.5%',
                    'avg_gpa': 9.5,
                    'programs': ['B.Tech Computer Science', 'B.Tech Information Technology'],
                    'ranking': 'Top 5 in Engineering'
                },
                {
                    'name': 'Delhi University',
                    'location': 'Delhi',
                    'fees': '₹50,000 - ₹1,00,000 per annum',
                    'acceptance_rate': '5% - 10%',
                    'avg_gpa': 8.5,
                    'programs': ['B.A. English', 'M.A. English', 'B.Tech Computer Science'],
                    'ranking': 'Top 10 in Arts'
                }
            ],
            'Tier 2': [
                {
                    'name': 'Jamia Millia Islamia',
                    'location': 'Delhi',
                    'fees': '₹1,00,000 - ₹2,00,000 per annum',
                    'acceptance_rate': '10% - 15%',
                    'avg_gpa': 8.0,
                    'programs': ['B.A. English', 'M.A. English', 'B.Tech Computer Science'],
                    'ranking': 'Top 20 in Arts'
                },
                {
                    'name': 'Jadavpur University',
                    'location': 'Kolkata',
                    'fees': '₹50,000 - ₹1,50,000 per annum',
                    'acceptance_rate': '8% - 12%',
                    'avg_gpa': 8.2,
                    'programs': ['B.A. English', 'M.A. English', 'B.Tech Computer Science'],
                    'ranking': 'Top 15 in Arts'
                }
            ],
            'Tier 3': [
                {
                    'name': 'Christ University',
                    'location': 'Bangalore',
                    'fees': '₹2,00,000 - ₹3,00,000 per annum',
                    'acceptance_rate': '25% - 35%',
                    'avg_gpa': 7.5,
                    'programs': ['B.A. English', 'M.A. English', 'B.Tech Computer Science'],
                    'ranking': 'Top 50 in Arts'
                }
            ]
        },
        'Journalist': {
            'Tier 1': [
                {
                    'name': 'Delhi University',
                    'location': 'Delhi',
                    'fees': '₹50,000 - ₹1,00,000 per annum',
                    'acceptance_rate': '5% - 10%',
                    'avg_gpa': 8.5,
                    'programs': ['B.A. Journalism', 'M.A. Journalism', 'B.A. English'],
                    'ranking': 'Top 5 in Journalism'
                },
                {
                    'name': 'Jamia Millia Islamia',
                    'location': 'Delhi',
                    'fees': '₹1,00,000 - ₹2,00,000 per annum',
                    'acceptance_rate': '10% - 15%',
                    'avg_gpa': 8.0,
                    'programs': ['B.A. Mass Communication', 'M.A. Mass Communication'],
                    'ranking': 'Top 10 in Journalism'
                }
            ],
            'Tier 2': [
                {
                    'name': 'Jadavpur University',
                    'location': 'Kolkata',
                    'fees': '₹50,000 - ₹1,50,000 per annum',
                    'acceptance_rate': '8% - 12%',
                    'avg_gpa': 8.2,
                    'programs': ['B.A. Journalism', 'M.A. Journalism'],
                    'ranking': 'Top 15 in Journalism'
                },
                {
                    'name': 'Pune University',
                    'location': 'Pune',
                    'fees': '₹1,00,000 - ₹2,00,000 per annum',
                    'acceptance_rate': '12% - 18%',
                    'avg_gpa': 7.8,
                    'programs': ['B.A. Mass Communication', 'M.A. Mass Communication'],
                    'ranking': 'Top 25 in Journalism'
                }
            ],
            'Tier 3': [
                {
                    'name': 'Christ University',
                    'location': 'Bangalore',
                    'fees': '₹2,00,000 - ₹3,00,000 per annum',
                    'acceptance_rate': '25% - 35%',
                    'avg_gpa': 7.5,
                    'programs': ['B.A. Journalism', 'M.A. Journalism'],
                    'ranking': 'Top 50 in Journalism'
                }
            ]
        },
        'Content Writer': {
            'Tier 1': [
                {
                    'name': 'Delhi University',
                    'location': 'Delhi',
                    'fees': '₹50,000 - ₹1,00,000 per annum',
                    'acceptance_rate': '5% - 10%',
                    'avg_gpa': 8.5,
                    'programs': ['B.A. English', 'M.A. English', 'B.A. Journalism'],
                    'ranking': 'Top 5 in English'
                },
                {
                    'name': 'Jadavpur University',
                    'location': 'Kolkata',
                    'fees': '₹50,000 - ₹1,50,000 per annum',
                    'acceptance_rate': '8% - 12%',
                    'avg_gpa': 8.2,
                    'programs': ['B.A. English', 'M.A. English', 'B.A. Journalism'],
                    'ranking': 'Top 10 in English'
                }
            ],
            'Tier 2': [
                {
                    'name': 'Jamia Millia Islamia',
                    'location': 'Delhi',
                    'fees': '₹1,00,000 - ₹2,00,000 per annum',
                    'acceptance_rate': '10% - 15%',
                    'avg_gpa': 8.0,
                    'programs': ['B.A. English', 'M.A. English', 'B.A. Mass Communication'],
                    'ranking': 'Top 20 in English'
                },
                {
                    'name': 'Pune University',
                    'location': 'Pune',
                    'fees': '₹1,00,000 - ₹2,00,000 per annum',
                    'acceptance_rate': '12% - 18%',
                    'avg_gpa': 7.8,
                    'programs': ['B.A. English', 'M.A. English'],
                    'ranking': 'Top 25 in English'
                }
            ],
            'Tier 3': [
                {
                    'name': 'Christ University',
                    'location': 'Bangalore',
                    'fees': '₹2,00,000 - ₹3,00,000 per annum',
                    'acceptance_rate': '25% - 35%',
                    'avg_gpa': 7.5,
                    'programs': ['B.A. English', 'M.A. English'],
                    'ranking': 'Top 50 in English'
                }
            ]
        },
        'UI/UX Designer': {
            'Tier 1': [
                {
                    'name': 'National Institute of Design (NID)',
                    'location': 'Ahmedabad, Bangalore, Gandhinagar',
                    'fees': '₹3,00,000 - ₹4,00,000 per annum',
                    'acceptance_rate': '1% - 3%',
                    'avg_gpa': 9.0,
                    'programs': ['B.Des Communication Design', 'M.Des Interaction Design'],
                    'ranking': 'Top 3 in Design'
                },
                {
                    'name': 'Indian Institute of Technology (IIT) - Multiple Locations',
                    'location': 'Mumbai, Delhi, Bangalore, Chennai, Kanpur, Kharagpur',
                    'fees': '₹2,00,000 - ₹3,00,000 per annum',
                    'acceptance_rate': '0.1% - 0.5%',
                    'avg_gpa': 9.5,
                    'programs': ['B.Tech Computer Science', 'B.Tech Design'],
                    'ranking': 'Top 5 in Engineering'
                }
            ],
            'Tier 2': [
                {
                    'name': 'Srishti Institute of Art, Design and Technology',
                    'location': 'Bangalore',
                    'fees': '₹4,00,000 - ₹5,00,000 per annum',
                    'acceptance_rate': '15% - 25%',
                    'avg_gpa': 8.0,
                    'programs': ['B.Des Communication Design', 'M.Des Interaction Design'],
                    'ranking': 'Top 10 in Design'
                },
                {
                    'name': 'MIT Institute of Design',
                    'location': 'Pune',
                    'fees': '₹3,00,000 - ₹4,00,000 per annum',
                    'acceptance_rate': '20% - 30%',
                    'avg_gpa': 7.8,
                    'programs': ['B.Des Communication Design', 'M.Des Interaction Design'],
                    'ranking': 'Top 15 in Design'
                }
            ],
            'Tier 3': [
                {
                    'name': 'Pearl Academy',
                    'location': 'Delhi, Mumbai, Bangalore, Jaipur',
                    'fees': '₹3,00,000 - ₹4,50,000 per annum',
                    'acceptance_rate': '30% - 40%',
                    'avg_gpa': 7.5,
                    'programs': ['B.Des Communication Design', 'M.Des Interaction Design'],
                    'ranking': 'Top 30 in Design'
                }
            ]
        },
        'Creative Director': {
            'Tier 1': [
                {
                    'name': 'National Institute of Design (NID)',
                    'location': 'Ahmedabad, Bangalore, Gandhinagar',
                    'fees': '₹3,00,000 - ₹4,00,000 per annum',
                    'acceptance_rate': '1% - 3%',
                    'avg_gpa': 9.0,
                    'programs': ['B.Des Communication Design', 'M.Des Design Management'],
                    'ranking': 'Top 3 in Design'
                },
                {
                    'name': 'Indian Institute of Management (IIM) - Multiple Locations',
                    'location': 'Ahmedabad, Bangalore, Calcutta, Lucknow',
                    'fees': '₹15,00,000 - ₹25,00,000 per annum',
                    'acceptance_rate': '0.1% - 0.5%',
                    'avg_gpa': 9.5,
                    'programs': ['MBA', 'PGDM'],
                    'ranking': 'Top 5 in Management'
                }
            ],
            'Tier 2': [
                {
                    'name': 'Srishti Institute of Art, Design and Technology',
                    'location': 'Bangalore',
                    'fees': '₹4,00,000 - ₹5,00,000 per annum',
                    'acceptance_rate': '15% - 25%',
                    'avg_gpa': 8.0,
                    'programs': ['B.Des Communication Design', 'M.Des Design Management'],
                    'ranking': 'Top 10 in Design'
                },
                {
                    'name': 'MIT Institute of Design',
                    'location': 'Pune',
                    'fees': '₹3,00,000 - ₹4,00,000 per annum',
                    'acceptance_rate': '20% - 30%',
                    'avg_gpa': 7.8,
                    'programs': ['B.Des Communication Design', 'M.Des Design Management'],
                    'ranking': 'Top 15 in Design'
                }
            ],
            'Tier 3': [
                {
                    'name': 'Pearl Academy',
                    'location': 'Delhi, Mumbai, Bangalore, Jaipur',
                    'fees': '₹3,00,000 - ₹4,50,000 per annum',
                    'acceptance_rate': '30% - 40%',
                    'avg_gpa': 7.5,
                    'programs': ['B.Des Communication Design', 'M.Des Design Management'],
                    'ranking': 'Top 30 in Design'
                }
            ]
        }
    }
    
    # Return career-specific colleges for the given tier
    colleges = career_colleges.get(career_name, {}).get(tier, [])
    if not colleges:
        # If no specific colleges found, return some relevant ones
        if 'Software' in career_name or 'Developer' in career_name:
            return career_colleges.get('Software Developer', {}).get(tier, [])
        elif 'Data' in career_name or 'Scientist' in career_name:
            return career_colleges.get('Data Scientist', {}).get(tier, [])
        elif 'AI' in career_name or 'Engineer' in career_name:
            return career_colleges.get('AI Engineer', {}).get(tier, [])
        elif 'Security' in career_name or 'Cybersecurity' in career_name:
            return career_colleges.get('Cybersecurity Specialist', {}).get(tier, [])
        elif 'Consultant' in career_name or 'IT' in career_name:
            return career_colleges.get('IT Consultant', {}).get(tier, [])
    
    return colleges

if __name__ == '__main__':
    init_db()
    app.run(debug=True) 