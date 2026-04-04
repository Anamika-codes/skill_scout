# SkillScout - Career Guidance Platform

## Project Overview

SkillScout is an AI-powered career guidance platform that helps users discover their perfect career path by analyzing their skills, interests, and experience. The platform provides personalized career recommendations and college suggestions based on user profiles.

## Features

### Core Features
- **AI-Powered Career Analysis**: Advanced machine learning algorithms analyze user profiles
- **Personalized Recommendations**: Tailored career suggestions based on individual profiles
- **College Recommendations**: Tier-based college suggestions with detailed information
- **Skill Tracking**: Monitor and track skill development progress
- **User Profiles**: Comprehensive profile management with academic and personal information

### Technical Features
- **Responsive Design**: Mobile-first approach with Bootstrap 5
- **Modern UI/UX**: Clean, professional interface with smooth animations
- **Form Validation**: Client-side and server-side validation
- **Security**: CSRF protection, secure sessions, and password hashing
- **Database**: SQLite database with SQLAlchemy ORM

## Technology Stack

### Backend
- **Python 3.8+**: Core programming language
- **Flask**: Web framework
- **SQLAlchemy**: Database ORM
- **Flask-Login**: User authentication
- **Flask-WTF**: Form handling and CSRF protection
- **scikit-learn**: Machine learning for career predictions

### Frontend
- **HTML5**: Semantic markup
- **CSS3**: Modern styling with CSS variables and animations
- **JavaScript**: Interactive functionality and form handling
- **Bootstrap 5**: Responsive UI framework
- **Font Awesome**: Icon library

### Data & ML
- **pandas**: Data manipulation
- **numpy**: Numerical computing
- **joblib**: Model persistence
- **Random Forest**: Career prediction model

## Project Structure

```
SkillScout/
├── app.py                 # Main Flask application
├── requirements.txt       # Python dependencies
├── README.md             # Project documentation
├── project_summary.md    # Detailed project overview
├── static/               # Static assets
│   ├── css/
│   │   └── main.css     # Main stylesheet
│   ├── js/
│   │   └── main.js     # Main JavaScript file
│   └── images/
│       └── Career.png   # Hero image
├── templates/            # HTML templates
│   ├── base.html        # Base template
│   ├── index.html       # Landing page
│   ├── login.html       # Login page
│   ├── register.html    # Registration page
│   ├── dashboard.html   # User dashboard
│   ├── profile.html     # Profile management
│   └── recommendations.html # Career recommendations
├── scripts/             # Python scripts
│   ├── data_collection/ # Data collection utilities
│   ├── database/        # Database initialization
│   ├── model_training/  # ML model training
│   └── prediction/      # Prediction modules
├── data/               # Data files
│   ├── models/         # Trained ML models
│   ├── processed/      # Processed datasets
│   └── raw/           # Raw data files
└── instance/           # Instance-specific files
    └── skillscout.db  # SQLite database
```

## Installation & Setup

### Prerequisites
- Python 3.8 or higher
- pip (Python package installer)

### Installation Steps

1. **Clone the repository**
   ```bash
   git clone <repository-url>
   cd SkillScout
   ```

2. **Create virtual environment**
   ```bash
   python -m venv venv
   source venv/bin/activate  # On Windows: venv\Scripts\activate
   ```

3. **Install dependencies**
   ```bash
   pip install -r requirements.txt
   ```

4. **Initialize the database**
   ```bash
   python -c "from app import init_db; init_db()"
   ```

5. **Run the application**
   ```bash
   python app.py
   ```

6. **Access the application**
   Open your browser and navigate to `http://localhost:5000`

## Usage

### For Users
1. **Register**: Create a new account with username and email
2. **Complete Profile**: Fill in academic information, skills, and preferences
3. **Get Recommendations**: View personalized career and college recommendations
4. **Update Profile**: Modify profile information to get updated recommendations

### For Developers
1. **Database**: Use SQLAlchemy models for data operations
2. **Templates**: Extend base.html for consistent styling
3. **Static Files**: Add CSS/JS to respective folders
4. **Models**: Update ML models in scripts/model_training/

## Key Features Implementation

### 1. Responsive Design
- Mobile-first approach with Bootstrap 5
- CSS Grid and Flexbox for layouts
- Custom CSS variables for consistent theming
- Smooth animations and transitions

### 2. User Authentication
- Secure password hashing with Werkzeug
- Session management with Flask-Login
- CSRF protection for all forms
- Remember me functionality

### 3. Career Prediction
- Random Forest model for career matching
- Feature scaling and preprocessing
- Model persistence with joblib
- Real-time prediction API

### 4. College Recommendations
- Tier-based college suggestions
- Detailed college information
- Location and budget filtering
- Acceptance rate and GPA requirements

## Security Features

- **Password Security**: Bcrypt hashing for passwords
- **Session Security**: Secure, HTTP-only cookies
- **CSRF Protection**: Token-based CSRF protection
- **Input Validation**: Server-side validation for all inputs
- **SQL Injection Prevention**: Parameterized queries with SQLAlchemy

## Performance Optimizations

- **Static File Caching**: Efficient static file serving
- **Database Indexing**: Optimized database queries
- **Lazy Loading**: Images and content loading
- **Minification**: CSS and JS minification (production)
- **CDN Integration**: Bootstrap and Font Awesome from CDN

## Browser Support

- Chrome 90+
- Firefox 88+
- Safari 14+
- Edge 90+

## Contributing

1. Fork the repository
2. Create a feature branch
3. Make your changes
4. Add tests if applicable
5. Submit a pull request

## License

This project is licensed under the MIT License - see the LICENSE file for details. 

## Support

For support and questions, please contact the development team or create an issue in the repository.

---

**SkillScout** - Your AI-powered career guidance companion 