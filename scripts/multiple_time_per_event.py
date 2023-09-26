"""
Script to make time per event and size per event as lists in requests and tickets
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
ticket_db = Database('tickets')

total_requests = request_db.get_count()
total_tickets = ticket_db.get_count()


for index, request in enumerate(request_db.query(limit=total_requests)):
    print('Processing request %s/%s %s' % (index + 1, total_requests, request['prepid']))
    sequences = request['sequences']
    save = False
    if not isinstance(request['time_per_event'], list):
        save = True
        request['time_per_event'] = [request['time_per_event']] * len(sequences)

    if not isinstance(request['size_per_event'], list):
        save = True
        request['size_per_event'] = [request['size_per_event']] * len(sequences)

    if save:
        print('Saving %s' % (request['prepid']))
        request_db.save(request)

for index, ticket in enumerate(ticket_db.query(limit=total_tickets)):
    print('Processing ticket %s/%s %s' % (index + 1, total_tickets, ticket['prepid']))
    steps = ticket['steps']
    save = False
    for step in steps:
        subcampaign = subcampaign_db.get(step['subcampaign'])
        sequences = subcampaign['sequences']
        if not isinstance(step['time_per_event'], list):
            save = True
            step['time_per_event'] = [step['time_per_event']] * len(sequences)

        if not isinstance(step['size_per_event'], list):
            save = True
            step['size_per_event'] = [step['size_per_event']] * len(sequences)

    if save:
        print('Saving %s' % (ticket['prepid']))
        ticket_db.save(ticket)
