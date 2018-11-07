from pymongo import MongoClient, DESCENDING, ASCENDING

def startMongo():
    client = MongoClient('mongodb://45.76.22.55:27017/',)
    return client.historico

def find_one(collection,query):
    db = startMongo()
    response = db[collection].find_one(query)
    return response

def find(collection,query,sort="-__$elo"):
    db = startMongo()
    response = db[collection].find(query)
    if sort:
        if sort[:1] == '-':
            response = response.sort(sort[1:], DESCENDING)
        else:
            response = response.sort(sort[1:], ASCENDING)
    return response

def update_doc(collection,query,data):
    db = startMongo()
    response = db[collection].update(query,data,upsert=False)
    return response

def insert_one(collection,data):
    db = startMongo()
    response = db[collection].insert_one(data)
    return response

def remove_by_query(collection,query):
    db = startMongo()
    response = db[collection].remove(query)
    return response