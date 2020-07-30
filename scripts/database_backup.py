"""
Script that makes backup of a collection
Requires DB_AUTH environment variable and database and collection names as arguments
"""
import sys
import json
import os
from pymongo import MongoClient

database_name = sys.argv[1]
collection_name = sys.argv[2]
output_directory = sys.argv[3]


db_host = os.environ.get('DB_HOST', 'localhost')
db_port = os.environ.get('DB_PORT', 27017)
db_auth = os.environ.get('DB_AUTH', None)
username = None
password = None
if db_auth:
    with open(db_auth) as json_file:
        credentials = json.load(json_file)

    username = credentials['username']
    password = credentials['password']

if username and password:
    client = MongoClient(db_host,
                         db_port,
                         username=username,
                         password=password,
                         authSource='admin',
                         authMechanism='SCRAM-SHA-256')
else:
    client = MongoClient(db_host, db_port)

collection = client[database_name][collection_name]
print('Database %s, collection %s' % (database_name, collection_name))
doc_count = collection.count_documents({})
print('Found %s documents' % (doc_count))
documents = [{}]
page = 0
limit = 100
collection_path = f'{output_directory}/{collection_name}'
os.makedirs(collection_path)
while documents:
    documents = collection.find({}).sort('_id', 1).skip(page * limit).limit(limit)
    documents = [d for d in documents]
    if not documents:
        break

    file_name = f'{collection_path}/{database_name}_{collection_name}_{page}.json'
    with open(file_name, 'w') as output_file:
        json.dump(documents, output_file)

    print('Page %s done' % (page))
    page += 1
