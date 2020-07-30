"""
Script that makes backup of a collection
Requires DB_AUTH environment variable and database and collection names as arguments
"""
import sys
import json
import zipfile
import os.path
sys.path.append(os.path.abspath(os.path.pardir))
from core_lib.database.database import Database

database_name = sys.argv[1]
collection_name = sys.argv[2]

print('Database %s, collection %s' % (database_name, collection_name))
Database.set_database_name(database_name)
database = Database(collection_name)
doc_count = database.get_count()
print('Found %s documents' % (doc_count))
documents = [{}]
page = 0
archive_name = f'{database_name}_{collection_name}.zip'

with zipfile.ZipFile(archive_name, 'w', zipfile.ZIP_DEFLATED) as zip_object:
    while documents:
        documents = database.query(page=page, limit=100)
        if not documents:
            break

        file_name = f'{database_name}_{collection_name}_{page}.json'
        with open(file_name, 'w') as output_file:
            json.dump(documents, output_file)

        zip_object.write(file_name, file_name)
        os.remove(file_name)
        print('Page %s done' % (page))
        page += 1
