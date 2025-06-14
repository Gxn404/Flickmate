import pymongo as mongo

def init_db(collection : str):
    client = mongo.MongoClient(os.getenv("MONGODB_URI"))
    db = client["auth"]
    col = db[collection]

    return col
