import pymongo as mongo

def init_db(collection : str):
    uri = os.getenv("MONGODB_URI", "mongodb://localhost:27017/")
    client = mongo.MongoClient(uri)
    db = client["auth"]
    col = db[collection]

    return col
