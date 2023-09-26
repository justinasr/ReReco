"""
Module that handles all email notifications
"""
import environment
from core_lib.utils.emailer import Emailer as BaseEmailer


class Emailer(BaseEmailer):
    """
    Emailer sends email notifications to users
    """

    def send(self, subject, body, recipients):
        body = body.strip()  + '\n\nSincerely,\nReReco Machine'
        if environment.DEVELOPMENT:
            subject = f'[ReReco-DEV] {subject}'
        else:
            subject = f'[ReReco] {subject}'

        super().send(subject, body, recipients)
