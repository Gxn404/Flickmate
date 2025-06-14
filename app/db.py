import os
import pymongo as mongo

def init_db(collection: str):
    uri = os.getenv("MONGO_PUBLIC_URL")  # ← use Railway's default var

    if not uri:
        raise Exception("❌ Mongo URI is missing!")

    client = mongo.MongoClient(uri)
    db = client["auth"]
    return db[collection]
