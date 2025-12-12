import os
import logging
import pymongo
from pymongo import MongoClient
from datetime import datetime
from bson import ObjectId

logger = logging.getLogger(__name__)

def fix_oid(query: dict):
    """
    Recursively convert '_id' strings to ObjectId.
    """
    if not isinstance(query, dict):
        return query
        
    new_query = {}
    for k, v in query.items():
        if k == '_id' and isinstance(v, str):
            try:
                new_query[k] = ObjectId(v)
            except:
                new_query[k] = v
        elif isinstance(v, dict):
            new_query[k] = fix_oid(v)
        else:
            new_query[k] = v
    return new_query

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

def run_query(query: dict, limit: int = 10):
    """
    Run a raw MongoDB query.
    """
    db = init_db()
    if db is None:
        return []

    try:
    try:
        collection = db['comments']
        # Fix ObjectId in query
        query = fix_oid(query)
        
        # Use find, sort by stored_at desc, limit results
        cursor = collection.find(query).sort('stored_at', -1).limit(limit)
        results = list(cursor)
        # Convert ObjectId to string for JSON serialization if needed, though simple dict should be fine for display
        for r in results:
            if '_id' in r:
                r['_id'] = str(r['_id'])
        return results
    except Exception as e:
        logger.error(f"Query failed: {e}")
        return [{"error": str(e)}]

def create_document(data: dict):
    """
    Insert a new document.
    """
    db = init_db()
    if db is None:
        return {"error": "Database not connected"}
    
    try:
        # Add timestamp if missing
        if 'stored_at' not in data:
            data['stored_at'] = datetime.utcnow()
            
        result = db['comments'].insert_one(data)
        return {"inserted_id": str(result.inserted_id), "acknowledged": result.acknowledged}
    except Exception as e:
        logger.error(f"Create failed: {e}")
        return {"error": str(e)}

def update_document(filter_query: dict, update_data: dict, is_raw_update: bool = False):
    """
    Update a document.
    """
    db = init_db()
    if db is None:
        return {"error": "Database not connected"}
        
    try:
        # If not raw update, wrap in $set safety
        update_op = update_data if is_raw_update else {"$set": update_data}
        
        # Fix ObjectId in filter
        filter_query = fix_oid(filter_query)
        
        result = db['comments'].update_one(filter_query, update_op)
        return {
            "matched_count": result.matched_count,
            "modified_count": result.modified_count,
            "acknowledged": result.acknowledged
        }
    except Exception as e:
        logger.error(f"Update failed: {e}")
        return {"error": str(e)}

def delete_document(filter_query: dict):
    """
    Delete a document.
    """
    db = init_db()
    if db is None:
        return {"error": "Database not connected"}
        
    try:
        # Fix ObjectId
        filter_query = fix_oid(filter_query)
        
        result = db['comments'].delete_one(filter_query)
        return {
            "deleted_count": result.deleted_count,
            "acknowledged": result.acknowledged
        }
    except Exception as e:
        logger.error(f"Delete failed: {e}")
        return {"error": str(e)}
