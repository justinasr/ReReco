"""
Script to update data format in database for PhaseII update
"""
import sys
import os.path
sys.path.append(os.path.abspath(os.path.pardir))
from core_lib.database.database import Database

Database.set_database_name('rereco')

request_db = Database('requests')
subcampaign_db = Database('subcampaigns')
old_ticket_db = Database('subcampaign_tickets')
new_ticket_db = Database('tickets')

total_subcampaigns = subcampaign_db.get_count()
total_requests = request_db.get_count()
total_old_tickets = old_ticket_db.get_count()
total_new_tickets = new_ticket_db.get_count()

print('Requests: %s' % (total_requests))
print('Subcampaigns: %s' % (total_subcampaigns))
print('(Old) subcampaign tickets: %s' % (total_old_tickets))
print('(New) tickets: %s' % (total_new_tickets))

for index, subcampaign in enumerate(subcampaign_db.query(limit=total_subcampaigns)):
    print('Processing subcampaign %s/%s %s' % (index + 1, total_subcampaigns, subcampaign['prepid']))
    subcampaign.pop('_rev', None)
    subcampaign.pop('step', None)
    subcampaign_db.save(subcampaign)

for index, request in enumerate(request_db.query(limit=total_requests)):
    print('Processing request %s/%s %s' % (index + 1, total_requests, request['prepid']))
    request.pop('_rev', None)
    request.pop('step', None)
    if 'input_dataset' in request:
        request['input'] = {'dataset': request.pop('input_dataset'),
                            'request': ''}

    request_db.save(request)

for index, ticket in enumerate(old_ticket_db.query(limit=total_old_tickets)):
    print('Processing ticket %s/%s %s' % (index + 1, total_old_tickets, ticket['prepid']))
    ticket.pop('_rev', None)
    if 'subcampaign' in ticket:
        ticket['steps'] = [{'subcampaign': ticket.pop('subcampaign'),
                            'processing_string': ticket.pop('processing_string'),
                            'time_per_event': ticket.pop('time_per_event'),
                            'size_per_event': ticket.pop('size_per_event'),
                            'priority': ticket.pop('priority')}]

    new_ticket_db.save(ticket)

total_subcampaigns = subcampaign_db.get_count()
total_requests = request_db.get_count()
total_old_tickets = old_ticket_db.get_count()
total_new_tickets = new_ticket_db.get_count()

print('Requests: %s' % (total_requests))
print('Subcampaigns: %s' % (total_subcampaigns))
print('(Old) subcampaign tickets: %s' % (total_old_tickets))
print('(New) tickets: %s' % (total_new_tickets))

print('Subcampaign tickets database can be removed')
