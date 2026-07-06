import sys
from pathlib import Path
import os
import datetime
from services.db_service import get_mongo_client
from config import MONGO_DB_NAME

def reset_admin():
    try:
        client = get_mongo_client()
        db = client.get_database(MONGO_DB_NAME)
        
        # Reset generation limits in user_limits
        col = db.get_collection('user_limits')
        col.update_one({'username': 'admin'}, {'$set': {'generations': 0}})
        
        # Also reset legacy ai_usage in users if any
        users = db.get_collection('users')
        today = datetime.datetime.utcnow().strftime('%Y-%m-%d')
        users.update_one({'username': 'admin'}, {'$set': {f'ai_usage.{today}': 0}})
        
        print("Successfully reset all AI credits for admin account!")
    except Exception as e:
        print(f"Error: {e}")

if __name__ == '__main__':
    reset_admin()
