"""
Script to remove gpu_steps attribute from subcampaigns and requests
"""
import sys
import os.path
import os
# pylint: disable-next=wrong-import-position
sys.path.append(os.path.abspath(os.path.pardir))
from core_lib.database.database import Database

Database.set_credentials_file(os.getenv('DB_AUTH'))
Database.set_database_name('rereco')

request_db = Database('requests')
subcampaign_db = Database('subcampaigns')

total_subcampaigns = subcampaign_db.get_count()
total_requests = request_db.get_count()

print('Requests: %s' % (total_requests))
print('Subcampaigns: %s' % (total_subcampaigns))

for index, subcampaign in enumerate(subcampaign_db.query(limit=total_subcampaigns)):
    print('Processing subcampaign %s/%s %s' % (index + 1,
                                               total_subcampaigns,
                                               subcampaign['prepid']))
    for sequence in subcampaign.get('sequences'):
        sequence.pop('gpu_steps', None)

    subcampaign_db.save(subcampaign)

for index, request in enumerate(request_db.query(limit=total_requests)):
    print('Processing request %s/%s %s' % (index + 1, total_requests, request['prepid']))
    for sequence in request.get('sequences'):
        sequence.pop('gpu_steps', None)

    request_db.save(request)


total_subcampaigns = subcampaign_db.get_count()
total_requests = request_db.get_count()

print('Requests: %s' % (total_requests))
print('Subcampaigns: %s' % (total_subcampaigns))
