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
    res = col.insert_one(record)
    return str(res.inserted_id)


def list_generated_mongo(limit: int = 100):
    client = get_mongo_client()
    db = client.get_database(MONGO_DB_NAME)
    col = db.get_collection(MONGO_COLLECTION)
    docs = list(col.find().sort('created_at', -1).limit(limit))
    # Convert ObjectId and datetime to str
    for d in docs:
        d['_id'] = str(d.get('_id'))
        if 'created_at' in d:
            try:
                d['created_at'] = d['created_at'].isoformat()
            except Exception:
                d['created_at'] = str(d['created_at'])
    return docs


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
