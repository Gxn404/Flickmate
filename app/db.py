import pymongo as mongo

def init_db(collection : str):
    client = mongo.MongoClient('mongodb://mongo:DcqyilLRbvnZqQDrPpmfiVTynTxulnHJ@centerbeam.proxy.rlwy.net:30952')
    db = client["auth"]
    col = db[collection]

    return col
