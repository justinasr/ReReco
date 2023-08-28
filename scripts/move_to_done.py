"""
Script that tries to move submitted requests to done
It should be run periodically
Requires MongoDB credentials and API access credentials for requesting
access tokens.
"""
import sys
import json
import os.path
import http.client
import pprint
sys.path.append(os.path.abspath(os.path.pardir))
from core_lib.database.database import Database
from core_lib.utils.common_utils import get_client_credentials, get_access_token


def get_database_credentials() -> dict[str, str | int]:
    """
    Retrieves database credentials from environment variables
    and raises a runtime exception if any of them is missing

    Returns:
        dict[str, str | int]: Configuration variables for database
    
    Raises:
        RuntimeError: If some of the required configuration variables for the
            database is missing.
    """
    error_msg: str = (
        "Some required environment variables for the database are missing. \n"
        "Please set them, they are: \n"
    )
    missing_variables: list[str] = []
    database_variables: dict[str, str | int] = {
        "MONGO_DB_USERNAME": os.getenv("MONGO_DB_USERNAME", ""),
        "MONGO_DB_PASSWORD": os.getenv("MONGO_DB_PASSWORD", ""),
        "MONGO_DB_HOST": os.getenv("MONGO_DB_HOST", ""),
        "MONGO_DB_PORT": int(os.getenv("MONGO_DB_PORT", "27017"))
    }
    
    for var, value in database_variables.items():
        if not value:
            missing_variables.append(var)
    
    if missing_variables:
        error_msg += pprint.pformat(missing_variables, indent=4)
        raise RuntimeError(error_msg)
    
    return database_variables


def move_to_done(host, client_credentials):
    """
    Try to move all submitted requests to next status

    Args:
        host (str): RelVal web application domain
        client_credentials (dict[str, str]): Credentials for requesting access tokens
            to authenticate request to the SSO
    """
    connection = http.client.HTTPSConnection(host=host, timeout=300)
    headers = {'Content-Type': 'application/json'}
    request_db = Database('requests')
    requests = [{}]
    page = 0
    while requests:
        requests = request_db.query(query_string='status=submitted', page=page)
        page += 1
        for request in requests:
            print(request['prepid'])
            headers["Authorization"] = get_access_token(credentials=client_credentials)
            connection.request('POST',
                               '/rereco/api/requests/next_status',
                               json.dumps(request),
                               headers=headers)
            response = connection.getresponse()
            response_text = json.loads(response.read())['message']
            print('  %s %s' % (response.code, response_text))


def main():
    """
    Move ReReco requests to done state. This script is designed to be executed
    by an integration workflow: Jenkins, GitHub Actions, etc.
    """
    # Retrieve client credentials
    api_access_credentials = get_client_credentials()

    # Retrieve database credentials
    database_credentials = get_database_credentials()

    # RelVal Service URL
    rereco_service_domain = os.getenv("SERVICE_DOMAIN", "cms-pdmv-prod.web.cern.ch")

    # Set database configuration
    Database.set_host_port(
        host=database_credentials["MONGO_DB_HOST"],
        port=database_credentials["MONGO_DB_PORT"]
    )
    Database.set_credentials(
        username=database_credentials["MONGO_DB_USERNAME"],
        password=database_credentials["MONGO_DB_PASSWORD"]
    )
    Database.set_database_name('rereco')
    move_to_done(host=rereco_service_domain, client_credentials=api_access_credentials)

if __name__ == '__main__':
    main()
