from pymongo import MongoClient
import datetime

MONGO_URI = "mongodb://localhost:27017/"
MONGO_DB_NAME = "flashcard_db"

def reset_credits():
    client = MongoClient(MONGO_URI)
    db = client.get_database(MONGO_DB_NAME)
    col = db.get_collection('user_limits')
    
    col.update_many(
        {},
        {'$set': {'generations': 0, 'last_reset_date': datetime.date.today().isoformat()}}
    )
    print("Successfully reset all user AI credits for today!")

if __name__ == "__main__":
    reset_credits()
