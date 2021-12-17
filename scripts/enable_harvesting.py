"""
Script to add "enable_harvesting" parameters to Subcampaigns and Requests
"""
import sys
import os.path
import os
sys.path.append(os.path.abspath(os.path.pardir))
from core_lib.database.database import Database

Database.set_credentials_file(os.getenv('DB_AUTH'))
Database.set_database_name('rereco')

subcampaigns_database = Database('subcampaigns')
requests_database = Database('requests')

total_subcampaigns = subcampaigns_database.get_count()
total_requests = requests_database.get_count()

print('Total subcampaigns: %s' % (total_subcampaigns))
print('Total requests: %s' % (total_requests))

for index, item in enumerate(subcampaigns_database.query(limit=total_subcampaigns)):
    print('Processing entry %s/%s %s' % (index + 1, total_subcampaigns, item.get('prepid', '<no-id>')))
    item['enable_harvesting'] = True
    subcampaigns_database.save(item)

for index, item in enumerate(requests_database.query(limit=total_requests)):
    print('Processing entry %s/%s %s' % (index + 1, total_requests, item.get('prepid', '<no-id>')))
    item['enable_harvesting'] = True
    requests_database.save(item)


print('Done')
