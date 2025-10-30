"""
Continual learning pipeline: merge new approved flashcards into train.jsonl and fine-tune the model.

- Fetches newly approved flashcards from MongoDB (flashcards collection)
- Appends unique Q&A pairs to ml_service/data/processed/train.jsonl
- Logs dataset size and number of new entries
- Optionally fine-tunes the model for N epochs (default: 1)

Usage:
    python ml_service/scripts/update_dataset.py [--epochs 2]
"""
import os
import json
import logging
import argparse
from pathlib import Path
from collections import OrderedDict
from pymongo import MongoClient

DATA_PATH = Path("ml_service/data/processed/train.jsonl")
MONGO_URI = os.environ.get("MONGO_URI", "mongodb://localhost:27017/")
MONGO_DB = os.environ.get("MONGO_DB_NAME", "flashcard_db")
MONGO_COLLECTION = os.environ.get("MONGO_COLLECTION", "flashcards")

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger("update_dataset")

def load_existing(path):
    """Load existing Q&A pairs as set of (input, output) tuples."""
    pairs = set()
    if not path.exists():
        return pairs
    with open(path, "r", encoding="utf-8") as f:
        for line in f:
            try:
                obj = json.loads(line)
                pairs.add((obj["input"].strip(), obj["output"].strip()))
            except Exception:
                continue
    return pairs

def fetch_approved_flashcards():
    """Fetch approved flashcards from MongoDB."""
    client = MongoClient(MONGO_URI)
    db = client[MONGO_DB]
    col = db[MONGO_COLLECTION]
    # Only fetch those with an 'approved' field True, or all if not present
    query = {"approved": True} if col.count_documents({"approved": True}) else {}
    cursor = col.find(query)
    for doc in cursor:
        for fc in doc.get("flashcards", []):
            q = fc.get("question", "").strip()
            a = fc.get("answer", "").strip()
            if q and a:
                yield (q, a)

def append_new_to_dataset(new_pairs, path):
    """Append new Q&A pairs to train.jsonl as {input, output}."""
    with open(path, "a", encoding="utf-8") as f:
        for q, a in new_pairs:
            obj = {"input": f"Generate a 7-mark Q&A from this text: {q}", "output": a}
            f.write(json.dumps(obj, ensure_ascii=False) + "\n")

def main():
    parser = argparse.ArgumentParser()
    parser.add_argument("--epochs", type=int, default=1, help="Number of fine-tuning epochs after update")
    args = parser.parse_args()

    logger.info("Loading existing dataset...")
    existing = load_existing(DATA_PATH)
    logger.info(f"Current dataset size: {len(existing)}")

    logger.info("Fetching new approved flashcards from MongoDB...")
    new = set(fetch_approved_flashcards())
    new_unique = new - set((q, a) for (q, a) in existing)
    logger.info(f"New unique Q&A pairs to add: {len(new_unique)}")

    if new_unique:
        append_new_to_dataset(new_unique, DATA_PATH)
        logger.info(f"Appended {len(new_unique)} new entries to {DATA_PATH}")
    else:
        logger.info("No new entries to append.")

    # Optionally retrain
    if args.epochs > 0:
        logger.info(f"Starting fine-tuning for {args.epochs} epoch(s)...")
        os.system(f"python ml_service/scripts/train_model.py --data {DATA_PATH} --out ml_service/models/flashmind_v1/ --epochs {args.epochs}")
        logger.info("Fine-tuning complete.")

if __name__ == "__main__":
    main()
