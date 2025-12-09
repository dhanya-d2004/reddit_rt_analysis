import os
import re
import logging
from dotenv import load_dotenv

# Configure logging
logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(name)s - %(levelname)s - %(message)s')
logger = logging.getLogger(__name__)

def load_config():
    """Load environment variables from .env file."""
    load_dotenv()
    
    required_vars = ["REDDIT_CLIENT_ID", "REDDIT_SECRET", "USER_AGENT"]
    missing_vars = [var for var in required_vars if not os.getenv(var)]
    
    if missing_vars:
        logger.warning(f"Missing environment variables: {', '.join(missing_vars)}. Application may not function correctly.")
        return False
    return True

def clean_text(text: str) -> str:
    """
    Clean the input text by removing URLs and excessive whitespace.
    """
    if not text:
        return ""
    
    # Remove URLs
    text = re.sub(r'http\S+', '', text)
    
    # Remove whitespace
    text = text.strip()
    text = re.sub(r'\s+', ' ', text)
    
    return text
