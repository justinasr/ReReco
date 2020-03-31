"""
Module that handles all email notifications
"""
import logging
import smtplib
from email.message import EmailMessage


class Emailer():
    """
    Emailer sends email notifications to users
    """

    def __init__(self):
        self.logger = logging.getLogger()

    def get_recipients(self, rereco_object):
        """
        Return list of emails of people that are in object's history
        """
        recipients = set()
        for entry in rereco_object.get('history'):
            user = entry['user']
            if not user or user == 'automatic':
                continue

            recipients.add(f'{user}@cern.ch')

        self.logger.info('Recipients of %s are %s',
                         rereco_object.get_prepid(),
                         ', '.join(recipients))

        return list(recipients)

    def send(self, subject, body, recipients):
        """
        Send email
        """
        # Create a text/plain message
        message = EmailMessage()
        body = body.strip()
        body += '\n\nSincerely,\nReReco Machine'
        message.set_content(body)
        message['Subject'] = f'[ReReco] {subject}'
        message['From'] = 'PdmV Service Account <pdmvserv@cern.ch>'
        message['To'] = ', '.join(recipients)
        message['Cc'] = 'pdmvserv@cern.ch'
        # Send the message via our own SMTP server.
        smtp = smtplib.SMTP()
        smtp.connect()
        self.logger.debug('Sending email %s to %s', message['Subject'], message['To'])
        smtp.send_message(message)
        smtp.quit()
