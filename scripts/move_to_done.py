"""
Script that tries to move submitted requests to done
It should be run periodically
Requires DB_AUTH environment variable and locally website port as only argument
"""
import sys
import json
import os.path
import http.client
sys.path.append(os.path.abspath(os.path.pardir))
from core_lib.database.database import Database

Database.set_database_name('rereco')
database_credentials = os.getenv('DB_AUTH')
if database_credentials:
     Database.set_credentials_file(database_credentials)

connection = http.client.HTTPConnection('localhost', port=sys.argv[1], timeout=300)
headers = {'Content-Type': 'application/json',
           'Adfs-Login': 'pdmvserv',
           'Adfs-Group': 'cms-service-pdmv-admins'}
request_db = Database('requests')
requests = [{}]
page = 0

while requests:
    requests = request_db.query(query_string='status=submitted', page=page)
    page += 1
    for request in requests:
        print(request['prepid'])
        connection.request('POST',
                           '/api/requests/next_status',
                           json.dumps(request),
                           headers=headers)
        response = connection.getresponse()
        response_text = json.loads(response.read())['message']
        print('  %s %s' % (response.code, response_text))
