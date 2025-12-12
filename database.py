import os
import logging
import pymongo
from pymongo import MongoClient
from datetime import datetime

logger = logging.getLogger(__name__)

# Global client to reuse connection
_client = None
_db = None

def init_db():
    """
    Initialize MongoDB connection.
    Returns the database object or None if connection fails.
    """
    global _client, _db
    
    if _db is not None:
        return _db
        
    uri = os.getenv("MONGODB_URI")
    db_name = os.getenv("DB_NAME", "reddit_analysis")
    
    if not uri:
        logger.warning("MONGODB_URI not set. Database storage disabled.")
        return None
        
    try:
        _client = MongoClient(uri, serverSelectionTimeoutMS=5000)
        # Check connection
        _client.server_info()
        _db = _client[db_name]
        logger.info(f"Connected to MongoDB: {db_name}")
        return _db
    except Exception as e:
        logger.error(f"Failed to connect to MongoDB: {e}")
        return None

def save_comment(data: dict):
    """
    Save a classified comment to MongoDB.
    """
    db = init_db()
    if db is None:
        return
        
    try:
        collection = db['comments']
        # Add timestamp if not present
        if 'stored_at' not in data:
            data['stored_at'] = datetime.utcnow()
            
        collection.insert_one(data)
        logger.debug(f"Saved comment {data.get('id')} to DB.")
    except Exception as e:
        logger.error(f"Error saving to MongoDB: {e}")
