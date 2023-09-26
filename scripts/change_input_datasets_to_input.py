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

ticket_db = Database('tickets')

total_tickets = ticket_db.get_count()

for index, ticket in enumerate(ticket_db.query(limit=total_tickets)):
    print('Processing ticket %s/%s %s' % (index + 1, total_tickets, ticket['prepid']))
    ticket['input'] = ticket.pop('input_datasets')
    ticket_db.save(ticket)
