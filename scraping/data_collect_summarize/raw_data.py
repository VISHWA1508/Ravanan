from pymongo import MongoClient
from datetime import datetime

# Connect to MongoDB Atlas
client = MongoClient("mongodb://localhost:27017/")
db = client["ravanan"]
collection = db["raw_data"]

def save_raw_data(company: str, url: str, raw_content: str = None):
    # Optional: Avoid inserting duplicate URLs
    if  collection.find_one({"url": url}):
        print(f"[⚠️] URL already exists in DB: {url}")
        return

    doc = {
        "company": company,
        "url": url,
        "raw_content": raw_content,
        "scraped_at": datetime.utcnow()
    }
    collection.insert_one(doc)
    print(f"[✅] Saved: {url}")
