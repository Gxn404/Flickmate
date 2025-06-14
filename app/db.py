import pymongo as mongo

def init_db(collection : str):
    client = mongo.MongoClient('mongodb://localhost:27017/')
    db = client["auth"]
    col = db[collection]

    return col
