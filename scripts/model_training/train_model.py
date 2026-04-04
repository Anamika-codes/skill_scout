import pandas as pd
import numpy as np
from sklearn.model_selection import train_test_split
from sklearn.preprocessing import StandardScaler
from sklearn.ensemble import RandomForestRegressor
from sklearn.metrics import mean_squared_error, r2_score
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
MODELS_DIR.mkdir(parents=True, exist_ok=True)

class CareerRecommender:
    def __init__(self):
        self.model = None
        self.scaler = StandardScaler()
        self.feature_columns = None
        
    def load_data(self):
        """Load and prepare training data"""
        logger.info("Loading training data...")
        try:
            # Load career requirements data
            career_data = pd.read_csv(PROCESSED_DIR / 'career_requirements.csv')
            
            # Load academic performance data
            academic_data = pd.read_csv(PROCESSED_DIR / 'academic_performance.csv')
            
            # Load employment trends
            employment_data = pd.read_csv(PROCESSED_DIR / 'employment_trends.csv')
            
            # Load career match scores
            match_scores = pd.read_csv(PROCESSED_DIR / 'career_match_scores.csv')
            
            # Get the latest employment data for each career
            latest_employment = employment_data.sort_values('year').groupby('occupation_id').last().reset_index()
            
            # Merge datasets
            self.data = match_scores.merge(academic_data, on='student_id', how='left')
            self.data = self.data.merge(career_data, on='occupation_id', how='left')
            self.data = self.data.merge(latest_employment, on='occupation_id', how='left')
            
            logger.info("Successfully loaded all datasets")
            return True
        except Exception as e:
            logger.error(f"Error loading data: {str(e)}")
            return False

    def prepare_features(self):
        """Prepare features for model training"""
        logger.info("Preparing features...")
        try:
            # Select relevant features
            self.feature_columns = [
                'gpa',
                'math_score',
                'science_score',
                'english_score',
                'extracurricular_activities',
                'leadership_roles',
                'skill_level',
                'knowledge_level',
                'ability_level',
                'market_demand',
                'growth_rate'
            ]
            
            # Create feature matrix
            X = self.data[self.feature_columns]
            
            # Create target variable (career match score)
            y = self.data['career_match_score']
            
            # Split data
            X_train, X_test, y_train, y_test = train_test_split(
                X, y, test_size=0.2, random_state=42
            )
            
            # Scale features
            X_train_scaled = self.scaler.fit_transform(X_train)
            X_test_scaled = self.scaler.transform(X_test)
            
            logger.info("Successfully prepared features")
            return X_train_scaled, X_test_scaled, y_train, y_test
        except Exception as e:
            logger.error(f"Error preparing features: {str(e)}")
            return None

    def train_model(self, X_train, y_train):
        """Train the career recommendation model"""
        logger.info("Training model...")
        try:
            self.model = RandomForestRegressor(
                n_estimators=100,
                max_depth=10,
                random_state=42
            )
            
            self.model.fit(X_train, y_train)
            logger.info("Successfully trained model")
            return True
        except Exception as e:
            logger.error(f"Error training model: {str(e)}")
            return False

    def evaluate_model(self, X_test, y_test):
        """Evaluate model performance"""
        logger.info("Evaluating model...")
        try:
            y_pred = self.model.predict(X_test)
            
            # Calculate metrics
            mse = mean_squared_error(y_test, y_pred)
            r2 = r2_score(y_test, y_pred)
            
            logger.info(f"Model Performance:")
            logger.info(f"Mean Squared Error: {mse:.2f}")
            logger.info(f"R² Score: {r2:.2f}")
            
            # Feature importance
            feature_importance = pd.DataFrame({
                'feature': self.feature_columns,
                'importance': self.model.feature_importances_
            }).sort_values('importance', ascending=False)
            
            logger.info("Feature Importance:")
            for _, row in feature_importance.iterrows():
                logger.info(f"{row['feature']}: {row['importance']:.4f}")
            
            return True
        except Exception as e:
            logger.error(f"Error evaluating model: {str(e)}")
            return False

    def save_model(self):
        """Save the trained model and scaler"""
        logger.info("Saving model...")
        try:
            # Save model
            joblib.dump(self.model, MODELS_DIR / 'career_recommender.joblib')
            
            # Save scaler
            joblib.dump(self.scaler, MODELS_DIR / 'feature_scaler.joblib')
            
            # Save feature columns
            with open(MODELS_DIR / 'feature_columns.txt', 'w') as f:
                f.write('\n'.join(self.feature_columns))
            
            logger.info("Successfully saved model and related files")
            return True
        except Exception as e:
            logger.error(f"Error saving model: {str(e)}")
            return False

def main():
    recommender = CareerRecommender()
    
    # Load and prepare data
    if not recommender.load_data():
        return
    
    # Prepare features
    prepared_data = recommender.prepare_features()
    if prepared_data is None:
        return
    
    X_train, X_test, y_train, y_test = prepared_data
    
    # Train model
    if not recommender.train_model(X_train, y_train):
        return
    
    # Evaluate model
    if not recommender.evaluate_model(X_test, y_test):
        return
    
    # Save model
    if not recommender.save_model():
        return
    
    logger.info("Model training pipeline completed successfully!")

if __name__ == "__main__":
    main() 