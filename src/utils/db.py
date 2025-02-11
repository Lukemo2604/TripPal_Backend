# src/utils/db.py

from pymongo import MongoClient
import os
import urllib.parse

class Mongo:
    client = None
    db = None

def init_db(mongo_uri):
    # Connect to MongoDB
    Mongo.client = MongoClient(mongo_uri)
    Mongo.db = Mongo.client["trippal"]  # database name

def get_db():
    return Mongo.db
