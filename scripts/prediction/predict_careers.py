import pandas as pd
import numpy as np
import joblib
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
MODELS_DIR = DATA_DIR / "models"

class CareerPredictor:
    def __init__(self):
        self.model = None
        self.scaler = None
        self.feature_columns = None
        self.career_data = None
        self.employment_data = None
        
    def load_model(self):
        """Load the trained model and related files"""
        try:
            # Load model
            self.model = joblib.load(MODELS_DIR / 'career_recommender.joblib')
            
            # Load scaler
            self.scaler = joblib.load(MODELS_DIR / 'feature_scaler.joblib')
            
            # Load feature columns
            with open(MODELS_DIR / 'feature_columns.txt', 'r') as f:
                self.feature_columns = f.read().splitlines()
            
            # Load career data
            self.career_data = pd.read_csv(PROCESSED_DIR / 'career_requirements.csv')
            
            # Load latest employment data
            employment_data = pd.read_csv(PROCESSED_DIR / 'employment_trends.csv')
            self.employment_data = (
                employment_data.sort_values('year')
                .groupby('occupation_id')
                .last()
                .reset_index()
            )
            
            logger.info("Successfully loaded model and related data")
            return True
        except Exception as e:
            logger.error(f"Error loading model: {str(e)}")
            return False
    
    def predict_careers(self, student_profile):
        """Predict careers based on student profile with more accurate and distinct scoring"""
        try:
            # More specific and accurate interest mapping
            interest_career_mapping = {
                'programming': ['Software Developer', 'AI Engineer', 'Cybersecurity Specialist'],
                'coding': ['Software Developer', 'AI Engineer', 'Cybersecurity Specialist'],
                'software': ['Software Developer', 'AI Engineer', 'IT Consultant'],
                'data': ['Data Scientist', 'AI Engineer', 'Business Analyst'],
                'analytics': ['Data Scientist', 'Business Analyst', 'Financial Advisor'],
                'artificial intelligence': ['AI Engineer', 'Data Scientist', 'Software Developer'],
                'machine learning': ['AI Engineer', 'Data Scientist', 'Software Developer'],
                'cybersecurity': ['Cybersecurity Specialist', 'IT Consultant', 'Software Developer'],
                'business': ['Business Analyst', 'Management Consultant', 'Financial Advisor'],
                'finance': ['Financial Advisor', 'Business Analyst', 'Management Consultant'],
                'marketing': ['Marketing Manager', 'Business Analyst', 'Content Writer'],
                'writing': ['Content Writer', 'Technical Writer', 'Journalist'],
                'communication': ['Content Writer', 'Journalist', 'Technical Writer'],
                'design': ['Graphic Designer', 'UI/UX Designer', 'Creative Director'],
                'art': ['Graphic Designer', 'UI/UX Designer', 'Creative Director'],
                'science': ['Research Scientist', 'Data Scientist', 'Environmental Scientist'],
                'research': ['Research Scientist', 'Data Scientist', 'AI Engineer'],
                'health': ['Doctor', 'Nurse', 'Healthcare Administrator'],
                'medicine': ['Doctor', 'Nurse', 'Healthcare Administrator']
            }
            
            # Get user interests
            interests = student_profile.get('interests', '').lower()
            logger.info(f"User interests: '{interests}'")
            
            # Initialize results DataFrame
            results = pd.DataFrame(columns=['career', 'category', 'match_score', 'salary_median', 'description', 'required_skills', 'growth_potential', 'education_requirements', 'growth_rate', 'market_demand'])
            
            # Calculate academic scores
            if student_profile.get('grading_system') == 'cgpa': 
                academic_score = student_profile.get('gpa', 0) / 10.0
            else:
                academic_score = student_profile.get('percentage', 0) / 100.0
            
            math_score = student_profile.get('math_score', 0) / 100.0
            science_score = student_profile.get('science_score', 0) / 100.0
            english_score = student_profile.get('english_score', 0) / 100.0
            
            # Calculate extracurricular and leadership scores
            extracurricular_score = min(student_profile.get('extracurricular_activities', 0) / 5.0, 1.0)
            leadership_score = min(student_profile.get('leadership_roles', 0) / 5.0, 1.0)
            
            # Find matching careers based on interests
            matched_careers = {}
            for interest, careers in interest_career_mapping.items():
                if interest in interests:
                    logger.info(f"Found interest match: '{interest}' -> {careers}")
                    for career in careers:
                        if career not in matched_careers:
                            matched_careers[career] = []
                        matched_careers[career].append(interest)
            
            logger.info(f"Matched careers: {list(matched_careers.keys())}")
            
            # Calculate distinct match scores for each career
            for career, matching_interests in matched_careers.items():
                career_data = self.get_career_data(career)
                if career_data:
                    # Base score from interest match (0.2 to 0.4)
                    interest_score = 0.2 + (len(matching_interests) * 0.04)
                    
                    # Subject-specific scoring based on career requirements
                    if career in ['Software Developer', 'AI Engineer', 'Cybersecurity Specialist']:
                        # Tech careers heavily favor math and science
                        subject_score = (math_score * 0.4 + science_score * 0.4 + english_score * 0.2) * 0.25
                        career_bonus = 0.08 if math_score > 0.8 and science_score > 0.8 else 0.03
                    elif career == 'Data Scientist':
                        # Data science favors math, science, and analytical thinking
                        subject_score = (math_score * 0.5 + science_score * 0.3 + english_score * 0.2) * 0.25
                        career_bonus = 0.10 if math_score > 0.85 else 0.05
                    elif career in ['Business Analyst', 'Management Consultant', 'Financial Advisor']:
                        # Business careers favor math and English
                        subject_score = (math_score * 0.4 + english_score * 0.4 + science_score * 0.2) * 0.25
                        career_bonus = 0.06 if math_score > 0.75 and english_score > 0.75 else 0.03
                    elif career in ['Content Writer', 'Technical Writer', 'Journalist']:
                        # Writing careers heavily favor English
                        subject_score = (english_score * 0.7 + math_score * 0.2 + science_score * 0.1) * 0.25
                        career_bonus = 0.08 if english_score > 0.8 else 0.03
                    elif career in ['Graphic Designer', 'UI/UX Designer', 'Creative Director']:
                        # Design careers favor creativity and English
                        subject_score = (english_score * 0.5 + math_score * 0.3 + science_score * 0.2) * 0.25
                        career_bonus = 0.05 if english_score > 0.7 else 0.02
                    else:
                        # General careers use balanced scoring
                        subject_score = (math_score + science_score + english_score) / 3 * 0.25
                        career_bonus = 0.03
                    
                    # Academic performance factor (0.1 to 0.2)
                    academic_factor = academic_score * 0.2
                    
                    # Extracurricular and leadership factors (0.02 to 0.08)
                    soft_skills_factor = (extracurricular_score + leadership_score) * 0.04
                    
                    # Calculate final match score with distinct values
                    match_score = interest_score + subject_score + academic_factor + soft_skills_factor + career_bonus
                    
                    # Add random variation to ensure distinctness (0.01 to 0.03)
                    import random
                    random.seed(hash(career + str(academic_score) + str(math_score) + str(science_score) + str(english_score)))  # More unique seed
                    variation = random.uniform(0.01, 0.03)
                    match_score += variation
                    
                    # Ensure score is between 0.5 and 0.9
                    match_score = max(0.5, min(0.9, match_score))
                    
                    career_data['match_score'] = match_score
                    results = pd.concat([results, pd.DataFrame([career_data])], ignore_index=True)
            
            # If we don't have enough careers, add academic-based recommendations
            if len(results) < 5:
                academic_careers = self.get_academic_based_careers(student_profile)
                results = pd.concat([results, academic_careers], ignore_index=True)
            
            # Remove duplicates and sort by match score
            results = results.drop_duplicates(subset=['career'])
            results = results.sort_values('match_score', ascending=False).head(5)
            
            logger.info(f"Final recommendations with distinct scores:")
            for idx, row in results.iterrows():
                logger.info(f"  {row['career']}: {row['match_score']:.3f}")
            
            return results
        except Exception as e:
            logger.error(f"Error making predictions: {str(e)}")
            return None

    def get_career_data(self, career_title):
        """Get detailed information about a specific career"""
        # This would typically come from a database or predefined dataset
        career_data = {
            'career': career_title,
            'category': self.get_career_category(career_title),
            'salary_median': self.get_salary_data(career_title),
            'description': self.get_career_description(career_title),
            'required_skills': self.get_required_skills(career_title),
            'growth_potential': self.get_growth_potential(career_title),
            'education_requirements': self.get_education_requirements(career_title),
            'growth_rate': self.get_growth_rate(career_title),
            'market_demand': self.get_market_demand(career_title)
        }
        return career_data

    def get_academic_based_careers(self, student_profile):
        """Get career recommendations based on academic performance"""
        try:
            # Get academic scores
            if student_profile.get('grading_system') == 'cgpa':
                academic_score = student_profile.get('gpa', 0) / 10.0
            else:
                academic_score = student_profile.get('percentage', 0) / 100.0
            
            math_score = student_profile.get('math_score', 0) / 100.0
            science_score = student_profile.get('science_score', 0) / 100.0
            english_score = student_profile.get('english_score', 0) / 100.0
            
            # Define career recommendations based on academic strengths
            careers = []
            
            # High math and science scores -> Technology/Science careers
            if math_score > 0.7 and science_score > 0.7:
                tech_careers = ['Software Developer', 'Data Scientist', 'AI Engineer', 'Cybersecurity Specialist', 'IT Consultant']
                for i, career in enumerate(tech_careers):
                    career_data = self.get_career_data(career)
                    if career_data:
                        # Calculate match score based on academic performance
                        base_score = (math_score + science_score) / 2 * 0.4 + academic_score * 0.3
                        # Add variation based on position
                        match_score = base_score + (0.08 - (i * 0.015))
                        # Add career-specific variation
                        if career in ['Software Developer', 'Data Scientist', 'AI Engineer']:
                            match_score += 0.05
                        elif career in ['Cybersecurity Specialist', 'IT Consultant']:
                            match_score += 0.03
                        # Add random variation
                        import random
                        random.seed(hash(career + str(academic_score) + str(math_score) + str(science_score)))
                        variation = random.uniform(0.01, 0.03)
                        match_score += variation
                        match_score = max(0.5, min(0.9, match_score))
                        career_data['match_score'] = match_score
                        careers.append(career_data)
            
            # High English scores -> Communication/Media careers
            if english_score > 0.7:
                comm_careers = ['Content Writer', 'Journalist', 'Technical Writer', 'Editor', 'Author']
                for i, career in enumerate(comm_careers):
                    career_data = self.get_career_data(career)
                    if career_data:
                        base_score = english_score * 0.4 + academic_score * 0.3
                        match_score = base_score + (0.08 - (i * 0.015))
                        # Add career-specific variation
                        if career in ['Content Writer', 'Technical Writer']:
                            match_score += 0.05
                        elif career in ['Journalist', 'Editor']:
                            match_score += 0.03
                        # Add random variation
                        import random
                        random.seed(hash(career + str(academic_score) + str(english_score)))
                        variation = random.uniform(0.01, 0.03)
                        match_score += variation
                        match_score = max(0.5, min(0.9, match_score))
                        career_data['match_score'] = match_score
                        careers.append(career_data)
            
            # High overall academic performance -> Business/Management careers
            if academic_score > 0.8:
                business_careers = ['Business Analyst', 'Financial Advisor', 'Marketing Manager', 'Management Consultant']
                for i, career in enumerate(business_careers):
                    career_data = self.get_career_data(career)
                    if career_data:
                        base_score = academic_score * 0.4 + (math_score + english_score) / 2 * 0.3
                        match_score = base_score + (0.08 - (i * 0.015))
                        # Add career-specific variation
                        if career in ['Business Analyst', 'Management Consultant']:
                            match_score += 0.05
                        elif career in ['Financial Advisor', 'Marketing Manager']:
                            match_score += 0.03
                        # Add random variation
                        import random
                        random.seed(hash(career + str(academic_score) + str(math_score) + str(english_score)))
                        variation = random.uniform(0.01, 0.03)
                        match_score += variation
                        match_score = max(0.5, min(0.9, match_score))
                        career_data['match_score'] = match_score
                        careers.append(career_data)
            
            # If no specific matches, provide general recommendations
            if not careers:
                general_careers = ['Software Developer', 'Data Scientist', 'Business Analyst', 'Content Writer', 'Graphic Designer']
                for i, career in enumerate(general_careers):
                    career_data = self.get_career_data(career)
                    if career_data:
                        base_score = academic_score * 0.3 + (math_score + science_score + english_score) / 3 * 0.4
                        match_score = base_score + (0.08 - (i * 0.015))
                        # Add career-specific variation
                        if career in ['Software Developer', 'Data Scientist']:
                            match_score += 0.05
                        elif career in ['Business Analyst', 'Content Writer']:
                            match_score += 0.03
                        elif career in ['Graphic Designer']:
                            match_score += 0.02
                        # Add random variation
                        import random
                        random.seed(hash(career + str(academic_score) + str(math_score) + str(science_score) + str(english_score)))
                        variation = random.uniform(0.01, 0.03)
                        match_score += variation
                        match_score = max(0.5, min(0.9, match_score))
                        career_data['match_score'] = match_score
                        careers.append(career_data)
            
            # Convert to DataFrame
            if careers:
                return pd.DataFrame(careers)
            else:
                return pd.DataFrame()
                
        except Exception as e:
            logger.error(f"Error in get_academic_based_careers: {str(e)}")
            return pd.DataFrame()

    def get_career_category(self, career_title):
        """Get the category for a specific career"""
        category_mapping = {
            'Travel Writer': 'Creative Arts',
            'Tour Guide': 'Hospitality',
            'Travel Agent': 'Business',
            'International Relations Specialist': 'Social Sciences',
            'Cultural Anthropologist': 'Social Sciences',
            'Photographer': 'Creative Arts',
            'Photojournalist': 'Media',
            'Visual Artist': 'Creative Arts',
            'Digital Media Specialist': 'Technology',
            'Creative Director': 'Creative Arts',
            'Musician': 'Creative Arts',
            'Music Producer': 'Creative Arts',
            'Sound Engineer': 'Technology',
            'Music Teacher': 'Education',
            'Music Therapist': 'Healthcare',
            'Sports Coach': 'Sports',
            'Athletic Trainer': 'Healthcare',
            'Sports Medicine Specialist': 'Healthcare',
            'Sports Journalist': 'Media',
            'Sports Agent': 'Business',
            'Graphic Designer': 'Creative Arts',
            'Art Director': 'Creative Arts',
            'Museum Curator': 'Arts',
            'Art Teacher': 'Education',
            'Content Writer': 'Creative Arts',
            'Journalist': 'Media',
            'Author': 'Creative Arts',
            'Technical Writer': 'Technology',
            'Editor': 'Media',
            'Software Developer': 'Technology',
            'Data Scientist': 'Technology',
            'AI Engineer': 'Technology',
            'Cybersecurity Specialist': 'Technology',
            'IT Consultant': 'Technology',
            'Business Analyst': 'Business',
            'Financial Advisor': 'Finance',
            'Marketing Manager': 'Business',
            'Entrepreneur': 'Business',
            'Management Consultant': 'Business',
            'Research Scientist': 'Science',
            'Environmental Scientist': 'Science',
            'Biologist': 'Science',
            'Chemist': 'Science',
            'Physicist': 'Science',
            'Doctor': 'Healthcare',
            'Nurse': 'Healthcare',
            'Physical Therapist': 'Healthcare',
            'Nutritionist': 'Healthcare',
            'Healthcare Administrator': 'Healthcare'
        }
        return category_mapping.get(career_title, 'Other')

    def get_salary_data(self, career_title):
        """Get salary data for a specific career"""
        salary_data = {
            'Travel Writer': 50000,
            'Tour Guide': 35000,
            'Travel Agent': 40000,
            'International Relations Specialist': 60000,
            'Cultural Anthropologist': 55000,
            'Photographer': 45000,
            'Photojournalist': 50000,
            'Visual Artist': 48000,
            'Digital Media Specialist': 65000,
            'Creative Director': 80000,
            'Musician': 45000,
            'Music Producer': 60000,
            'Sound Engineer': 55000,
            'Music Teacher': 45000,
            'Music Therapist': 50000,
            'Sports Coach': 40000,
            'Athletic Trainer': 45000,
            'Sports Medicine Specialist': 60000,
            'Sports Journalist': 50000,
            'Sports Agent': 70000,
            'Graphic Designer': 50000,
            'Art Director': 70000,
            'Museum Curator': 55000,
            'Art Teacher': 45000,
            'Content Writer': 45000,
            'Journalist': 50000,
            'Author': 55000,
            'Technical Writer': 60000,
            'Editor': 55000,
            'Software Developer': 80000,
            'Data Scientist': 90000,
            'AI Engineer': 95000,
            'Cybersecurity Specialist': 85000,
            'IT Consultant': 75000,
            'Business Analyst': 70000,
            'Financial Advisor': 75000,
            'Marketing Manager': 75000,
            'Entrepreneur': 60000,
            'Management Consultant': 80000,
            'Research Scientist': 75000,
            'Environmental Scientist': 65000,
            'Biologist': 60000,
            'Chemist': 65000,
            'Physicist': 70000,
            'Doctor': 120000,
            'Nurse': 65000,
            'Physical Therapist': 70000,
            'Nutritionist': 55000,
            'Healthcare Administrator': 80000
        }
        return salary_data.get(career_title, 50000)

    def get_career_description(self, career_title):
        """Get description for a specific career"""
        descriptions = {
            'Travel Writer': 'Creates engaging content about travel experiences, destinations, and tips for various media platforms.',
            'Tour Guide': 'Leads and educates groups through historical sites, museums, and other points of interest.',
            'Travel Agent': 'Helps clients plan and book travel arrangements, including flights, hotels, and activities.',
            'International Relations Specialist': 'Analyzes and advises on international political and economic relations.',
            'Cultural Anthropologist': 'Studies human cultures, societies, and development patterns.',
            'Photographer': 'Captures and creates visual images for various purposes including art, journalism, and commercial use.',
            'Photojournalist': 'Tells stories through photographs, often working for news organizations.',
            'Visual Artist': 'Creates original artwork using various mediums and techniques.',
            'Digital Media Specialist': 'Manages and creates content for digital platforms and social media.',
            'Creative Director': 'Oversees the creative vision and direction of projects in various industries.',
            'Musician': 'Creates and performs music professionally.',
            'Music Producer': 'Oversees the production of music recordings and manages artists.',
            'Sound Engineer': 'Works with audio equipment and software to record, mix, and master sound.',
            'Music Teacher': 'Educates students in music theory, performance, and appreciation.',
            'Music Therapist': 'Uses music to help clients improve their physical and mental health.',
            'Sports Coach': 'Trains and develops athletes in specific sports.',
            'Athletic Trainer': 'Prevents, diagnoses, and treats muscle and bone injuries and illnesses.',
            'Sports Medicine Specialist': 'Provides medical care to athletes and active individuals.',
            'Sports Journalist': 'Reports on sports events, athletes, and related news.',
            'Sports Agent': 'Represents athletes in contract negotiations and career management.',
            'Graphic Designer': 'Creates visual concepts to communicate ideas that inspire, inform, and captivate consumers.',
            'Art Director': 'Oversees the visual style and images in magazines, newspapers, product packaging, and movie and television productions.',
            'Museum Curator': 'Manages collections of artwork and historical items and organizes exhibitions.',
            'Art Teacher': 'Educates students in various forms of visual art.',
            'Content Writer': 'Creates written content for websites, blogs, and other digital platforms.',
            'Journalist': 'Researches and reports news stories for various media outlets.',
            'Author': 'Writes books, articles, and other literary works.',
            'Technical Writer': 'Creates technical documentation and instructions.',
            'Editor': 'Reviews and revises content for publication.',
            'Software Developer': 'Designs, develops, and maintains software applications.',
            'Data Scientist': 'Analyzes complex data sets to help organizations make better decisions.',
            'AI Engineer': 'Develops artificial intelligence systems and machine learning models.',
            'Cybersecurity Specialist': 'Protects computer systems and networks from cyber threats.',
            'IT Consultant': 'Advises organizations on how to use information technology to meet their business objectives.',
            'Business Analyst': 'Analyzes business processes and recommends improvements.',
            'Financial Advisor': 'Provides financial planning and investment advice to clients.',
            'Marketing Manager': 'Plans and executes marketing campaigns and strategies.',
            'Entrepreneur': 'Starts and manages their own business ventures.',
            'Management Consultant': 'Helps organizations improve their performance and efficiency.',
            'Research Scientist': 'Conducts experiments and research in various scientific fields.',
            'Environmental Scientist': 'Studies the environment and develops solutions to environmental problems.',
            'Biologist': 'Studies living organisms and their relationship to their environment.',
            'Chemist': 'Studies the composition and properties of substances.',
            'Physicist': 'Studies matter, energy, and the fundamental forces of nature.',
            'Doctor': 'Diagnoses and treats medical conditions and injuries.',
            'Nurse': 'Provides and coordinates patient care and educates patients about health conditions.',
            'Physical Therapist': 'Helps patients improve movement and manage pain.',
            'Nutritionist': 'Advises people on what to eat to lead a healthy lifestyle or achieve a specific health-related goal.',
            'Healthcare Administrator': 'Manages the business aspects of healthcare facilities.'
        }
        return descriptions.get(career_title, 'No description available.')

    def get_required_skills(self, career_title):
        """Get required skills for a specific career"""
        skills = {
            'Travel Writer': 'Writing, Research, Photography, Cultural Awareness',
            'Tour Guide': 'Public Speaking, History Knowledge, Customer Service, Language Skills',
            'Travel Agent': 'Customer Service, Organization, Sales, Travel Industry Knowledge',
            'International Relations Specialist': 'Research, Analysis, Communication, Cultural Understanding',
            'Cultural Anthropologist': 'Research, Analysis, Cultural Understanding, Writing',
            'Photographer': 'Photography, Editing, Creativity, Technical Skills',
            'Photojournalist': 'Photography, Journalism, Ethics, Storytelling',
            'Visual Artist': 'Creativity, Technical Skills, Art History, Portfolio Development',
            'Digital Media Specialist': 'Social Media, Content Creation, Analytics, Marketing',
            'Creative Director': 'Leadership, Creativity, Project Management, Communication',
            'Musician': 'Musical Talent, Performance, Theory, Practice',
            'Music Producer': 'Music Theory, Technology, Leadership, Business',
            'Sound Engineer': 'Technical Skills, Audio Equipment, Software, Problem Solving',
            'Music Teacher': 'Teaching, Music Theory, Patience, Communication',
            'Music Therapist': 'Music, Psychology, Empathy, Communication',
            'Sports Coach': 'Leadership, Sports Knowledge, Communication, Motivation',
            'Athletic Trainer': 'Medical Knowledge, First Aid, Communication, Physical Fitness',
            'Sports Medicine Specialist': 'Medical Knowledge, Sports Science, Diagnosis, Treatment',
            'Sports Journalist': 'Writing, Sports Knowledge, Research, Communication',
            'Sports Agent': 'Negotiation, Business, Sports Knowledge, Communication',
            'Graphic Designer': 'Creativity, Software Skills, Typography, Design Principles',
            'Art Director': 'Leadership, Creativity, Project Management, Design',
            'Museum Curator': 'Research, Organization, Art History, Communication',
            'Art Teacher': 'Teaching, Art Knowledge, Patience, Communication',
            'Content Writer': 'Writing, Research, SEO, Creativity',
            'Journalist': 'Writing, Research, Ethics, Communication',
            'Author': 'Writing, Creativity, Research, Discipline',
            'Technical Writer': 'Writing, Technical Knowledge, Organization, Communication',
            'Editor': 'Writing, Grammar, Attention to Detail, Communication',
            'Software Developer': 'Programming, Problem Solving, Algorithms, Teamwork',
            'Data Scientist': 'Statistics, Programming, Machine Learning, Analysis',
            'AI Engineer': 'Programming, Machine Learning, Mathematics, Problem Solving',
            'Cybersecurity Specialist': 'Security, Programming, Problem Solving, Analysis',
            'IT Consultant': 'Technology, Problem Solving, Communication, Business',
            'Business Analyst': 'Analysis, Communication, Problem Solving, Business Knowledge',
            'Financial Advisor': 'Finance, Communication, Analysis, Ethics',
            'Marketing Manager': 'Marketing, Strategy, Communication, Analysis',
            'Entrepreneur': 'Business, Leadership, Risk Management, Innovation',
            'Management Consultant': 'Analysis, Communication, Problem Solving, Business',
            'Research Scientist': 'Research, Analysis, Writing, Technical Skills',
            'Environmental Scientist': 'Research, Analysis, Field Work, Communication',
            'Biologist': 'Research, Analysis, Laboratory Skills, Writing',
            'Chemist': 'Research, Analysis, Laboratory Skills, Safety',
            'Physicist': 'Mathematics, Research, Analysis, Problem Solving',
            'Doctor': 'Medical Knowledge, Communication, Empathy, Problem Solving',
            'Nurse': 'Medical Knowledge, Communication, Empathy, Organization',
            'Physical Therapist': 'Medical Knowledge, Communication, Empathy, Physical Fitness',
            'Nutritionist': 'Nutrition Knowledge, Communication, Analysis, Counseling',
            'Healthcare Administrator': 'Leadership, Healthcare Knowledge, Organization, Communication'
        }
        return skills.get(career_title, 'No specific skills listed.')

    def get_growth_potential(self, career_title):
        """Get growth potential for a specific career"""
        growth_potentials = {
            'Travel Writer': 'Moderate',
            'Tour Guide': 'Stable',
            'Travel Agent': 'Declining',
            'International Relations Specialist': 'Growing',
            'Cultural Anthropologist': 'Stable',
            'Photographer': 'Competitive',
            'Photojournalist': 'Declining',
            'Visual Artist': 'Competitive',
            'Digital Media Specialist': 'Growing',
            'Creative Director': 'Growing',
            'Musician': 'Competitive',
            'Music Producer': 'Growing',
            'Sound Engineer': 'Growing',
            'Music Teacher': 'Stable',
            'Music Therapist': 'Growing',
            'Sports Coach': 'Growing',
            'Athletic Trainer': 'Growing',
            'Sports Medicine Specialist': 'Growing',
            'Sports Journalist': 'Stable',
            'Sports Agent': 'Growing',
            'Graphic Designer': 'Growing',
            'Art Director': 'Growing',
            'Museum Curator': 'Stable',
            'Art Teacher': 'Stable',
            'Content Writer': 'Growing',
            'Journalist': 'Declining',
            'Author': 'Competitive',
            'Technical Writer': 'Growing',
            'Editor': 'Stable',
            'Software Developer': 'Growing',
            'Data Scientist': 'Growing',
            'AI Engineer': 'Growing',
            'Cybersecurity Specialist': 'Growing',
            'IT Consultant': 'Growing',
            'Business Analyst': 'Growing',
            'Financial Advisor': 'Growing',
            'Marketing Manager': 'Growing',
            'Entrepreneur': 'Competitive',
            'Management Consultant': 'Growing',
            'Research Scientist': 'Growing',
            'Environmental Scientist': 'Growing',
            'Biologist': 'Growing',
            'Chemist': 'Growing',
            'Physicist': 'Growing',
            'Doctor': 'Growing',
            'Nurse': 'Growing',
            'Physical Therapist': 'Growing',
            'Nutritionist': 'Growing',
            'Healthcare Administrator': 'Growing'
        }
        return growth_potentials.get(career_title, 'Unknown')

    def get_education_requirements(self, career_title):
        """Get education requirements for a specific career"""
        education = {
            'Travel Writer': 'Bachelor\'s degree in Journalism, Communications, or related field',
            'Tour Guide': 'High school diploma or equivalent, certification may be required',
            'Travel Agent': 'High school diploma, certification preferred',
            'International Relations Specialist': 'Bachelor\'s or Master\'s degree in International Relations or related field',
            'Cultural Anthropologist': 'Master\'s or PhD in Anthropology',
            'Photographer': 'Bachelor\'s degree in Photography or related field',
            'Photojournalist': 'Bachelor\'s degree in Journalism or Photography',
            'Visual Artist': 'Bachelor\'s degree in Fine Arts or related field',
            'Digital Media Specialist': 'Bachelor\'s degree in Digital Media, Marketing, or related field',
            'Creative Director': 'Bachelor\'s degree in Design, Fine Arts, or related field',
            'Musician': 'Bachelor\'s degree in Music or equivalent experience',
            'Music Producer': 'Bachelor\'s degree in Music Production or related field',
            'Sound Engineer': 'Bachelor\'s degree in Audio Engineering or related field',
            'Music Teacher': 'Bachelor\'s degree in Music Education',
            'Music Therapist': 'Bachelor\'s degree in Music Therapy',
            'Sports Coach': 'Bachelor\'s degree in Sports Science or related field',
            'Athletic Trainer': 'Bachelor\'s degree in Athletic Training',
            'Sports Medicine Specialist': 'Medical degree with specialization in Sports Medicine',
            'Sports Journalist': 'Bachelor\'s degree in Journalism or related field',
            'Sports Agent': 'Bachelor\'s degree in Sports Management or related field',
            'Graphic Designer': 'Bachelor\'s degree in Graphic Design or related field',
            'Art Director': 'Bachelor\'s degree in Fine Arts or related field',
            'Museum Curator': 'Master\'s degree in Museum Studies or related field',
            'Art Teacher': 'Bachelor\'s degree in Art Education',
            'Content Writer': 'Bachelor\'s degree in English, Journalism, or related field',
            'Journalist': 'Bachelor\'s degree in Journalism or related field',
            'Author': 'Bachelor\'s degree in English, Creative Writing, or related field',
            'Technical Writer': 'Bachelor\'s degree in Technical Writing, English, or related field',
            'Editor': 'Bachelor\'s degree in English, Journalism, or related field',
            'Software Developer': 'Bachelor\'s degree in Computer Science or related field',
            'Data Scientist': 'Master\'s degree in Data Science, Statistics, or related field',
            'AI Engineer': 'Master\'s degree in Computer Science, AI, or related field',
            'Cybersecurity Specialist': 'Bachelor\'s degree in Cybersecurity or related field',
            'IT Consultant': 'Bachelor\'s degree in Information Technology or related field',
            'Business Analyst': 'Bachelor\'s degree in Business, Economics, or related field',
            'Financial Advisor': 'Bachelor\'s degree in Finance, Economics, or related field',
            'Marketing Manager': 'Bachelor\'s degree in Marketing or related field',
            'Entrepreneur': 'Bachelor\'s degree in Business or related field',
            'Management Consultant': 'Bachelor\'s degree in Business or related field',
            'Research Scientist': 'PhD in relevant scientific field',
            'Environmental Scientist': 'Master\'s degree in Environmental Science or related field',
            'Biologist': 'Master\'s degree in Biology or related field',
            'Chemist': 'Master\'s degree in Chemistry or related field',
            'Physicist': 'PhD in Physics',
            'Doctor': 'Medical degree (MD or DO)',
            'Nurse': 'Bachelor\'s degree in Nursing',
            'Physical Therapist': 'Doctor of Physical Therapy (DPT)',
            'Nutritionist': 'Bachelor\'s degree in Nutrition or related field',
            'Healthcare Administrator': 'Master\'s degree in Healthcare Administration or related field'
        }
        return education.get(career_title, 'Education requirements vary.')

    def get_growth_rate(self, career_title):
        """Get growth rate for a specific career"""
        growth_rates = {
            'Travel Writer': 5,
            'Tour Guide': 3,
            'Travel Agent': -2,
            'International Relations Specialist': 8,
            'Cultural Anthropologist': 4,
            'Photographer': 3,
            'Photojournalist': -4,
            'Visual Artist': 4,
            'Digital Media Specialist': 10,
            'Creative Director': 8,
            'Musician': 2,
            'Music Producer': 6,
            'Sound Engineer': 7,
            'Music Teacher': 4,
            'Music Therapist': 9,
            'Sports Coach': 6,
            'Athletic Trainer': 8,
            'Sports Medicine Specialist': 9,
            'Sports Journalist': 3,
            'Sports Agent': 7,
            'Graphic Designer': 7,
            'Art Director': 8,
            'Museum Curator': 4,
            'Art Teacher': 4,
            'Content Writer': 8,
            'Journalist': -3,
            'Author': 2,
            'Technical Writer': 9,
            'Editor': 3,
            'Software Developer': 12,
            'Data Scientist': 15,
            'AI Engineer': 16,
            'Cybersecurity Specialist': 14,
            'IT Consultant': 10,
            'Business Analyst': 9,
            'Financial Advisor': 8,
            'Marketing Manager': 10,
            'Entrepreneur': 5,
            'Management Consultant': 9,
            'Research Scientist': 8,
            'Environmental Scientist': 9,
            'Biologist': 7,
            'Chemist': 6,
            'Physicist': 7,
            'Doctor': 7,
            'Nurse': 9,
            'Physical Therapist': 10,
            'Nutritionist': 8,
            'Healthcare Administrator': 9
        }
        return growth_rates.get(career_title, 5)

    def get_market_demand(self, career_title):
        """Get market demand for a specific career"""
        market_demands = {
            'Travel Writer': 3,
            'Tour Guide': 3,
            'Travel Agent': 2,
            'International Relations Specialist': 4,
            'Cultural Anthropologist': 3,
            'Photographer': 3,
            'Photojournalist': 2,
            'Visual Artist': 3,
            'Digital Media Specialist': 4,
            'Creative Director': 4,
            'Musician': 2,
            'Music Producer': 3,
            'Sound Engineer': 4,
            'Music Teacher': 3,
            'Music Therapist': 4,
            'Sports Coach': 4,
            'Athletic Trainer': 4,
            'Sports Medicine Specialist': 4,
            'Sports Journalist': 3,
            'Sports Agent': 3,
            'Graphic Designer': 4,
            'Art Director': 4,
            'Museum Curator': 3,
            'Art Teacher': 3,
            'Content Writer': 4,
            'Journalist': 2,
            'Author': 2,
            'Technical Writer': 4,
            'Editor': 3,
            'Software Developer': 5,
            'Data Scientist': 5,
            'AI Engineer': 5,
            'Cybersecurity Specialist': 5,
            'IT Consultant': 4,
            'Business Analyst': 4,
            'Financial Advisor': 4,
            'Marketing Manager': 4,
            'Entrepreneur': 3,
            'Management Consultant': 4,
            'Research Scientist': 4,
            'Environmental Scientist': 4,
            'Biologist': 4,
            'Chemist': 4,
            'Physicist': 4,
            'Doctor': 5,
            'Nurse': 5,
            'Physical Therapist': 5,
            'Nutritionist': 4,
            'Healthcare Administrator': 4
        }
        return market_demands.get(career_title, 3)

def format_career_recommendations(results, top_n=10):
    """Format career recommendations in a readable way"""
    if results is None or len(results) == 0:
        return "No career recommendations found."
    
    output = "Top Career Recommendations:\n\n"
    
    for i, (_, career) in enumerate(results.head(top_n).iterrows(), 1):
        output += f"{i}. {career['career']} (Category: {career['category']})\n"
        output += f"   Match Score: {career['match_score']:.1f}%\n"
        output += f"   Required Education: {career['required_education']}\n"
        output += f"   Required Skills: {career['required_skills']}\n"
        output += f"   Median Salary: ${career['salary_median']:,.2f}\n"
        output += f"   Growth Rate: {career['growth_rate']:.1f}%\n"
        output += f"   Market Demand: {career['market_demand']}/5\n"
        output += "\n"
    
    return output

def main():
    # Initialize predictor
    predictor = CareerPredictor()
    
    # Load model and data
    if not predictor.load_model():
        return
    
    # Example student profile
    student_profile = {
        'gpa': 3.8,
        'math_score': 85,
        'science_score': 90,
        'english_score': 78,
        'extracurricular_activities': 3,
        'leadership_roles': 2
    }
    
    # Get predictions
    results = predictor.predict_careers(student_profile)
    
    # Print recommendations
    print("\nStudent Profile:")
    print(f"GPA: {student_profile['gpa']}")
    print(f"Math Score: {student_profile['math_score']}")
    print(f"Science Score: {student_profile['science_score']}")
    print(f"English Score: {student_profile['english_score']}")
    print(f"Extracurricular Activities: {student_profile['extracurricular_activities']}")
    print(f"Leadership Roles: {student_profile['leadership_roles']}")
    print("\n" + "="*50 + "\n")
    print(format_career_recommendations(results))

if __name__ == "__main__":
    main() 

