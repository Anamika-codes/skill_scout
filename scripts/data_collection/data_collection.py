import pandas as pd
import numpy as np
import requests
import json
import os
from pathlib import Path
import logging
from datetime import datetime

# Set up logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)

# Create data directories if they don't exist
DATA_DIR = Path("data")
RAW_DIR = DATA_DIR / "raw"
PROCESSED_DIR = DATA_DIR / "processed"

for dir_path in [DATA_DIR, RAW_DIR, PROCESSED_DIR]:
    dir_path.mkdir(parents=True, exist_ok=True)

class DataCollector:
    def __init__(self):
        self.raw_data = {}
        self.processed_data = {}

    def download_onet_data(self):
        """Download O*NET database data"""
        logger.info("Downloading O*NET data...")
        # O*NET API endpoints
        endpoints = {
            'occupations': 'https://services.onetcenter.org/ws/online/occupations',
            'skills': 'https://services.onetcenter.org/ws/online/skills',
            'knowledge': 'https://services.onetcenter.org/ws/online/knowledge',
            'abilities': 'https://services.onetcenter.org/ws/online/abilities'
        }
        
        for name, url in endpoints.items():
            try:
                response = requests.get(url)
                if response.status_code == 200:
                    data = response.json()
                    self.raw_data[f'onet_{name}'] = data
                    # Save raw data
                    with open(RAW_DIR / f'onet_{name}.json', 'w') as f:
                        json.dump(data, f)
                    logger.info(f"Successfully downloaded {name} data")
                else:
                    logger.error(f"Failed to download {name} data: {response.status_code}")
            except Exception as e:
                logger.error(f"Error downloading {name} data: {str(e)}")

    def download_bls_data(self):
        """Download Bureau of Labor Statistics data"""
        logger.info("Downloading BLS data...")
        # BLS API endpoint for occupational employment statistics
        url = "https://api.bls.gov/publicAPI/v2/timeseries/data/"
        
        try:
            response = requests.get(url)
            if response.status_code == 200:
                data = response.json()
                self.raw_data['bls_employment'] = data
                # Save raw data
                with open(RAW_DIR / 'bls_employment.json', 'w') as f:
                    json.dump(data, f)
                logger.info("Successfully downloaded BLS data")
            else:
                logger.error(f"Failed to download BLS data: {response.status_code}")
        except Exception as e:
            logger.error(f"Error downloading BLS data: {str(e)}")

    def process_onet_data(self):
        """Process O*NET data into structured format"""
        logger.info("Processing O*NET data...")
        try:
            # Process occupations data
            occupations = pd.DataFrame(self.raw_data['onet_occupations'])
            skills = pd.DataFrame(self.raw_data['onet_skills'])
            knowledge = pd.DataFrame(self.raw_data['onet_knowledge'])
            abilities = pd.DataFrame(self.raw_data['onet_abilities'])

            # Merge relevant data
            career_data = occupations.merge(skills, on='id', how='left')
            career_data = career_data.merge(knowledge, on='id', how='left')
            career_data = career_data.merge(abilities, on='id', how='left')

            # Save processed data
            career_data.to_csv(PROCESSED_DIR / 'career_requirements.csv', index=False)
            logger.info("Successfully processed O*NET data")
        except Exception as e:
            logger.error(f"Error processing O*NET data: {str(e)}")

    def process_bls_data(self):
        """Process BLS data into structured format"""
        logger.info("Processing BLS data...")
        try:
            # Convert BLS data to DataFrame
            bls_data = pd.DataFrame(self.raw_data['bls_employment'])
            
            # Process and clean data
            bls_data['year'] = pd.to_datetime(bls_data['year'])
            bls_data = bls_data.sort_values('year')
            
            # Save processed data
            bls_data.to_csv(PROCESSED_DIR / 'employment_trends.csv', index=False)
            logger.info("Successfully processed BLS data")
        except Exception as e:
            logger.error(f"Error processing BLS data: {str(e)}")

    def create_sample_academic_data(self):
        """Create sample academic performance dataset"""
        logger.info("Creating sample academic data...")
        try:
            # Generate sample academic data
            academic_data = pd.DataFrame({
                'student_id': range(1, 1001),
                'gpa': np.random.normal(3.2, 0.5, 1000),
                'math_score': np.random.normal(75, 10, 1000),
                'science_score': np.random.normal(78, 12, 1000),
                'english_score': np.random.normal(80, 8, 1000),
                'extracurricular_activities': np.random.randint(0, 5, 1000),
                'leadership_roles': np.random.randint(0, 3, 1000)
            })
            
            # Save sample data
            academic_data.to_csv(PROCESSED_DIR / 'academic_performance.csv', index=False)
            logger.info("Successfully created sample academic data")
        except Exception as e:
            logger.error(f"Error creating sample academic data: {str(e)}")

def main():
    collector = DataCollector()
    
    # Download data
    collector.download_onet_data()
    collector.download_bls_data()
    
    # Process data
    collector.process_onet_data()
    collector.process_bls_data()
    
    # Create sample academic data
    collector.create_sample_academic_data()
    
    logger.info("Data collection and processing completed!")

if __name__ == "__main__":
    main() 