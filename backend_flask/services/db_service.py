import os
import json
import datetime
import logging
from pathlib import Path

try:
    from backend_flask.config import (
        MONGO_URI,
        MONGO_DB_NAME,
        MONGO_COLLECTION,
        GENERATED_DIR,
        ENABLE_FILE_DB,
    )
except ModuleNotFoundError:
    from config import (
        MONGO_URI,
        MONGO_DB_NAME,
        MONGO_COLLECTION,
        GENERATED_DIR,
        ENABLE_FILE_DB,
    )

logger = logging.getLogger(__name__)

DB_FILE = Path(GENERATED_DIR) / 'flashcard_records.jsonl'

_mongo_client = None
_mongo_available = False

try:
    from pymongo import MongoClient
    _mongo_available = True
except Exception:
    _mongo_available = False


def get_mongo_client():
    """Return a singleton MongoClient. Lazily initializes the client."""
    global _mongo_client
    if not _mongo_available:
        raise RuntimeError('pymongo not available')
    if _mongo_client is None:
        _mongo_client = MongoClient(MONGO_URI, serverSelectionTimeoutMS=2000)
    return _mongo_client


def save_generated_mongo(record: dict):
    client = get_mongo_client()
    db = client.get_database(MONGO_DB_NAME)
    col = db.get_collection(MONGO_COLLECTION)
    if '_id' in record:
        col.replace_one({'_id': record['_id']}, record, upsert=True)
        return str(record['_id'])
    else:
        res = col.insert_one(record)
        return str(res.inserted_id)

def check_duplicate(filename: str, username: str) -> bool:
    if not _mongo_available:
        return False
    try:
        client = get_mongo_client()
        db = client.get_database(MONGO_DB_NAME)
        col = db.get_collection(MONGO_COLLECTION)
        return col.find_one({'source_file': filename, 'created_by': username}) is not None
    except Exception:
        return False

def list_generated_mongo(limit: int = 100):
    client = get_mongo_client()
    db = client.get_database(MONGO_DB_NAME)
    col = db.get_collection(MONGO_COLLECTION)
    docs = list(col.find().sort('created_at', -1).limit(limit))
    # Convert ObjectId and datetime to str
    def _convert_mongo_doc(d: dict):
        d['_id'] = str(d.get('_id'))
        if 'created_at' in d:
            try:
                d['created_at'] = d['created_at'].isoformat()
            except:
                d['created_at'] = str(d['created_at'])
        return d
    return [_convert_mongo_doc(d) for d in docs]

def get_user_generation_count(username: str) -> int:
    if not _mongo_available:
        return 0
    try:
        client = get_mongo_client()
        db = client.get_database(MONGO_DB_NAME)
        col = db.get_collection('user_limits')
        user_doc = col.find_one({'username': username})
        if not user_doc:
            return 0
            
        today = datetime.date.today().isoformat()
        if user_doc.get('last_reset_date') != today:
            return 0
            
        return user_doc.get('generations', 0)
    except Exception as e:
        logger.error(f"Error getting limit: {e}")
        return 0

def check_and_increment_generation(username: str, limit: int = 5) -> bool:
    if not _mongo_available:
        return True
    try:
        client = get_mongo_client()
        db = client.get_database(MONGO_DB_NAME)
        col = db.get_collection('user_limits')
        
        user_doc = col.find_one({'username': username})
        today = datetime.date.today().isoformat()
        
        current_count = 0
        if user_doc and user_doc.get('last_reset_date') == today:
            current_count = user_doc.get('generations', 0)
        
        if current_count >= limit:
            return False
            
        col.update_one(
            {'username': username},
            {
                '$inc': {'generations': 1},
                '$set': {'last_reset_date': today}
            } if user_doc and user_doc.get('last_reset_date') == today else {
                '$set': {'generations': 1, 'last_reset_date': today}
            },
            upsert=True
        )
        return True
    except Exception as e:
        logger.error(f"Error checking limit: {e}")
        return True


def save_generated_file(record: dict):
    if not ENABLE_FILE_DB:
        # File-backed DB disabled by configuration; pretend to succeed but do
        # not create files on disk. Return a sentinel indicating file DB is
        # disabled so callers can handle it if needed.
        return None

    os.makedirs(Path(GENERATED_DIR), exist_ok=True)
    # append as jsonl
    with open(DB_FILE, 'a', encoding='utf-8') as f:
        f.write(json.dumps(record, ensure_ascii=False) + '\n')
    return str(DB_FILE)


def list_generated_file(limit: int = 100):
    out = []
    if not ENABLE_FILE_DB:
        # File DB disabled, return empty set
        return out

    if not DB_FILE.exists():
        return out
    with open(DB_FILE, 'r', encoding='utf-8') as f:
        for ln in reversed(list(f)):
            if not ln.strip():
                continue
            try:
                obj = json.loads(ln)
                out.append(obj)
                if len(out) >= limit:
                    break
            except Exception:
                continue
    return out


def get_record_by_id(record_id: str):
    if not _mongo_available:
        return None
    from bson.objectid import ObjectId
    try:
        client = get_mongo_client()
        db = client.get_database(MONGO_DB_NAME)
        col = db.get_collection(MONGO_COLLECTION)
        return col.find_one({'_id': ObjectId(record_id)})
    except Exception as e:
        logger.error(f"Error fetching record: {e}")
        return None

def check_and_increment_ai_limit(username: str) -> bool:
    if not _mongo_available:
        return True # Default allow if no Mongo
    
    today = datetime.datetime.utcnow().strftime('%Y-%m-%d')
    client = get_mongo_client()
    db = client.get_database(MONGO_DB_NAME)
    users = db.get_collection('users')
    
    user = users.find_one({'username': username})
    if not user:
        return False
        
    usage = user.get('ai_usage', {})
    count = usage.get(today, 0)
    
    if count >= 2:
        return False
        
    usage[today] = count + 1
    users.update_one({'username': username}, {'$set': {'ai_usage': usage}})
    return True


def save_generated(record: dict):
    """Save a generated flashcard record to the DB if possible, otherwise to file.

    Returns: inserted id (str) or file path.
    """
    rec = dict(record)
    rec.setdefault('created_at', datetime.datetime.utcnow())
    # Prefer Mongo if available. Only fall back to file if explicitly enabled
    # via configuration (ENABLE_FILE_DB). This avoids creating repo files by
    # default on machines without Mongo.
    if _mongo_available:
        try:
            return save_generated_mongo(rec)
        except Exception as e:
            logger.warning('Mongo save failed')
            if ENABLE_FILE_DB:
                logger.warning('Falling back to file DB: %s', e)
                return save_generated_file(rec)
            logger.warning('File DB disabled; not persisting generated record')
            return None
    else:
        if ENABLE_FILE_DB:
            return save_generated_file(rec)
        logger.info('Mongo not available and file DB is disabled; not saving record')
        return None


def list_generated(limit: int = 100):
    if _mongo_available:
        try:
            return list_generated_mongo(limit=limit)
        except Exception as e:
            logger.warning('Failed to list from mongo, falling back to file: %s', e)
            return list_generated_file(limit=limit)
    else:
        return list_generated_file(limit=limit)
