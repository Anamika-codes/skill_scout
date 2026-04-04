import pandas as pd
import numpy as np
from pathlib import Path
import logging

# Set up logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)

# Define paths
DATA_DIR = Path("data")
PROCESSED_DIR = DATA_DIR / "processed"
PROCESSED_DIR.mkdir(parents=True, exist_ok=True)

def generate_career_requirements():
    """Generate synthetic career requirements data"""
    logger.info("Generating synthetic career requirements data...")
    
    # Define career categories
    career_categories = [
        "Technology", "Healthcare", "Finance", "Education", 
        "Engineering", "Marketing", "Legal", "Creative Arts"
    ]
    
    # Define skills
    skills = [
        "Programming", "Data Analysis", "Communication", "Problem Solving",
        "Leadership", "Project Management", "Research", "Critical Thinking",
        "Creativity", "Teamwork", "Technical Writing", "Public Speaking"
    ]
    
    # Generate data
    num_careers = 100
    careers = []
    
    for i in range(num_careers):
        career = {
            'occupation_id': f"OCC{i+1:04d}",
            'title': f"Career {i+1}",
            'category': np.random.choice(career_categories),
            'description': f"Description for career {i+1}",
            'required_education': np.random.choice(["High School", "Bachelor's", "Master's", "PhD"]),
            'skill_level': np.random.randint(1, 6),
            'knowledge_level': np.random.randint(1, 6),
            'ability_level': np.random.randint(1, 6),
            'required_skills': ", ".join(np.random.choice(skills, size=np.random.randint(3, 7), replace=False))
        }
        careers.append(career)
    
    # Create DataFrame
    career_data = pd.DataFrame(careers)
    
    # Save to CSV
    career_data.to_csv(PROCESSED_DIR / 'career_requirements.csv', index=False)
    logger.info(f"Generated {num_careers} synthetic career requirements")
    
    return career_data

def generate_employment_trends():
    """Generate synthetic employment trends data"""
    logger.info("Generating synthetic employment trends data...")
    
    # Generate data for the last 5 years
    years = range(2019, 2024)
    num_careers = 100
    
    trends = []
    
    for year in years:
        for i in range(num_careers):
            # Base growth rate with some randomness
            base_growth = np.random.normal(2.0, 1.0)
            
            trend = {
                'year': year,
                'occupation_id': f"OCC{i+1:04d}",
                'employment_count': int(np.random.normal(10000, 5000)),
                'growth_rate': base_growth,
                'market_demand': np.random.randint(1, 6),
                'salary_median': int(np.random.normal(60000, 20000)),
                'salary_low': int(np.random.normal(40000, 15000)),
                'salary_high': int(np.random.normal(80000, 25000))
            }
            trends.append(trend)
    
    # Create DataFrame
    trends_data = pd.DataFrame(trends)
    
    # Save to CSV
    trends_data.to_csv(PROCESSED_DIR / 'employment_trends.csv', index=False)
    logger.info(f"Generated employment trends for {len(years)} years and {num_careers} careers")
    
    return trends_data

def generate_academic_performance():
    """Generate synthetic academic performance data"""
    logger.info("Generating synthetic academic performance data...")
    
    num_students = 1000
    
    academic_data = pd.DataFrame({
        'student_id': range(1, num_students + 1),
        'gpa': np.random.normal(3.2, 0.5, num_students),
        'math_score': np.random.normal(75, 10, num_students),
        'science_score': np.random.normal(78, 12, num_students),
        'english_score': np.random.normal(80, 8, num_students),
        'extracurricular_activities': np.random.randint(0, 5, num_students),
        'leadership_roles': np.random.randint(0, 3, num_students),
        'interests': [", ".join(np.random.choice(
            ["Technology", "Healthcare", "Finance", "Education", "Engineering", "Marketing", "Legal", "Creative Arts"],
            size=np.random.randint(1, 4),
            replace=False
        )) for _ in range(num_students)]
    })
    
    # Ensure GPA is within valid range
    academic_data['gpa'] = academic_data['gpa'].clip(0, 4.0)
    
    # Ensure scores are within valid range
    for col in ['math_score', 'science_score', 'english_score']:
        academic_data[col] = academic_data[col].clip(0, 100)
    
    # Save to CSV
    academic_data.to_csv(PROCESSED_DIR / 'academic_performance.csv', index=False)
    logger.info(f"Generated academic performance data for {num_students} students")
    
    return academic_data

def generate_career_match_scores(career_data, academic_data):
    """Generate synthetic career match scores"""
    logger.info("Generating synthetic career match scores...")
    
    # Create a mapping of student interests to career categories
    interest_to_category = {
        "Technology": "Technology",
        "Healthcare": "Healthcare",
        "Finance": "Finance",
        "Education": "Education",
        "Engineering": "Engineering",
        "Marketing": "Marketing",
        "Legal": "Legal",
        "Creative Arts": "Creative Arts"
    }
    
    # Generate match scores
    match_scores = []
    
    for _, student in academic_data.iterrows():
        student_interests = student['interests'].split(", ")
        
        for _, career in career_data.iterrows():
            # Base score on academic performance
            base_score = (
                student['gpa'] / 4.0 * 0.3 +
                student['math_score'] / 100 * 0.2 +
                student['science_score'] / 100 * 0.2 +
                student['english_score'] / 100 * 0.2 +
                student['extracurricular_activities'] / 5 * 0.05 +
                student['leadership_roles'] / 3 * 0.05
            )
            
            # Adjust score based on interest match
            interest_match = 0
            for interest in student_interests:
                if interest_to_category.get(interest) == career['category']:
                    interest_match += 1
            
            interest_factor = 1.0 + (interest_match * 0.2)
            
            # Add some randomness
            random_factor = np.random.normal(1.0, 0.1)
            
            # Calculate final score (0-100)
            final_score = min(100, base_score * 100 * interest_factor * random_factor)
            
            match_score = {
                'student_id': student['student_id'],
                'occupation_id': career['occupation_id'],
                'career_match_score': final_score
            }
            match_scores.append(match_score)
    
    # Create DataFrame
    match_scores_data = pd.DataFrame(match_scores)
    
    # Save to CSV
    match_scores_data.to_csv(PROCESSED_DIR / 'career_match_scores.csv', index=False)
    logger.info(f"Generated {len(match_scores)} career match scores")
    
    return match_scores_data

def main():
    # Generate synthetic data
    career_data = generate_career_requirements()
    employment_data = generate_employment_trends()
    academic_data = generate_academic_performance()
    
    # Generate career match scores
    match_scores = generate_career_match_scores(career_data, academic_data)
    
    logger.info("Synthetic data generation completed successfully!")

if __name__ == "__main__":
    main() 