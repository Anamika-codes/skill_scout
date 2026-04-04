import subprocess
import logging
import sys
from pathlib import Path

# Set up logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)

def run_script(script_name, script_dir):
    """Run a Python script and return True if successful"""
    logger.info(f"Running {script_name}...")
    try:
        result = subprocess.run(
            [sys.executable, f"scripts/{script_dir}/{script_name}"],
            check=True,
            capture_output=True,
            text=True
        )
        logger.info(f"Successfully ran {script_name}")
        return True
    except subprocess.CalledProcessError as e:
        logger.error(f"Error running {script_name}: {e}")
        logger.error(f"Output: {e.output}")
        return False

def main():
    # Create necessary directories
    data_dir = Path("data")
    data_dir.mkdir(exist_ok=True)
    
    # Run the pipeline
    scripts = [
        ("generate_synthetic_data.py", "data_collection"),
        ("train_model.py", "model_training"),
        ("predict_careers.py", "prediction")
    ]
    
    for script, directory in scripts:
        if not run_script(script, directory):
            logger.error(f"Pipeline failed at {script}")
            return False
    
    logger.info("Pipeline completed successfully!")
    return True

if __name__ == "__main__":
    main() 