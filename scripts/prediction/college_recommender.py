import pandas as pd
import numpy as np
import json
from pathlib import Path
import logging
from sklearn.metrics.pairwise import cosine_similarity

# Set up logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)

class CollegeRecommender:
    def __init__(self):
        self.colleges_df = None
        self.load_data()
        
    def load_data(self):
        """Load college data from CSV file"""
        try:
            data_path = Path("data/processed/colleges.csv")
            if not data_path.exists():
                logger.error(f"College data file not found at {data_path}")
                return
            
            self.colleges_df = pd.read_csv(data_path)
            # Ensure all required columns exist
            required_columns = ['name', 'location', 'tier', 'tuition_fee', 'acceptance_rate', 'avg_gpa', 'website']
            for col in required_columns:
                if col not in self.colleges_df.columns:
                    logger.error(f"Missing required column: {col}")
                    return
            
            logger.info("Successfully loaded college data")
        except Exception as e:
            logger.error(f"Error loading college data: {str(e)}")
    
    def recommend_colleges(self, student_profile, career_data, num_recommendations=5):
        """Recommend colleges based on student profile and career preferences"""
        if self.colleges_df is None:
            logger.error("College data not loaded")
            return []
        
        try:
            # Filter colleges by preferred tier
            if student_profile.get('preferred_college_tier'):
                colleges = self.colleges_df[self.colleges_df['tier'] == student_profile['preferred_college_tier']]
            else:
                colleges = self.colleges_df
            
            # Filter by location if specified
            if student_profile.get('preferred_location'):
                location = student_profile['preferred_location'].lower()
                colleges = colleges[colleges['location'].str.lower().str.contains(location)]
            
            # Filter by budget if specified
            if student_profile.get('budget_range'):
                budget = student_profile['budget_range']
                if budget == 'low':
                    colleges = colleges[colleges['tuition_fee'] <= 150000]
                elif budget == 'medium':
                    colleges = colleges[(colleges['tuition_fee'] > 150000) & (colleges['tuition_fee'] <= 200000)]
                elif budget == 'high':
                    colleges = colleges[colleges['tuition_fee'] > 200000]
            
            # Calculate match score based on student's academic performance
            if student_profile.get('grading_system') == 'cgpa':
                academic_score = student_profile.get('gpa', 0) / 10.0  # Convert 0-10 scale to 0-1
            else:  # percentage
                academic_score = student_profile.get('percentage', 0) / 100.0  # Convert 0-100 to 0-1
            
            # Calculate overall score with more weight on academic performance
            colleges['match_score'] = (
                (colleges['acceptance_rate'] * 0.2) +  # Lower acceptance rate is better
                (academic_score * 0.5) +  # Student's academic performance
                (colleges['avg_gpa'] / 10.0 * 0.3)  # College's academic standards
            )
            
            # Sort by match score and get top recommendations
            recommendations = colleges.sort_values('match_score', ascending=False).head(num_recommendations)
            
            # Convert to list of dictionaries with all required fields
            result = []
            for _, row in recommendations.iterrows():
                college_dict = {
                    'name': row['name'],
                    'location': row['location'],
                    'tier': row['tier'],
                    'tuition_fee': float(row['tuition_fee']),
                    'acceptance_rate': float(row['acceptance_rate']),
                    'match_score': float(row['match_score']),
                    'website': row['website']
                }
                result.append(college_dict)
            
            return result
        except Exception as e:
            logger.error(f"Error recommending colleges: {str(e)}")
            return []

def main():
    # Example usage
    recommender = CollegeRecommender()
    if recommender.load_data():
        student_profile = {
            'gpa': 3.8,
            'preferred_location': 'California',
            'budget_range': 'high',
            'preferred_college_tier': 'Tier 1'
        }
        career = {
            'id': 1,
            'title': 'Software Engineer'
        }
        recommendations = recommender.recommend_colleges(student_profile, career)
        print(recommendations)

if __name__ == "__main__":
    main() 