# -*- coding: utf-8; -*-
from pymongo import MongoClient, DESCENDING, ASCENDING
import enviroment

def startMongo(db):
    client = MongoClient(enviroment.MONGO,)
    return client[db]

def find_one(db, collection,query):
    db = startMongo(db)
    response = db[collection].find_one(query)
    return response

def find(db, collection,query,sort="-ELO"):
    db = startMongo(db)
    response = db[collection].find(query)
    if sort:
        if sort[:1] == '-':
            response = response.sort(sort[1:], DESCENDING)
        else:
            response = response.sort(sort[1:], ASCENDING)
    return response

def update_doc(db, collection,query,data):
    db = startMongo(db)
    response = db[collection].update(query,data,upsert=False)
    return response

def insert_one(db, collection,data):
    db = startMongo(db)
    response = db[collection].insert_one(data)
    return response

def remove_by_query(db, collection,query):
    db = startMongo(db)
    response = db[collection].remove(query)
    return response