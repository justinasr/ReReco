"""
Main module that starts flask web server
"""
import logging
import argparse
from flask_restful import Api
from flask_cors import CORS
from flask import Flask, render_template
from core_lib.database.database import Database
from api.subcampaign_api import (CreateSubcampaignAPI,
                                 DeleteSubcampaignAPI,
                                 UpdateSubcampaignAPI,
                                 GetSubcampaignAPI,
                                 GetEditableSubcampaignAPI,
                                 GetDefaultSubcampaignSequenceAPI)
from api.ticket_api import (CreateTicketAPI,
                            DeleteTicketAPI,
                            UpdateTicketAPI,
                            GetTicketAPI,
                            GetTicketDatasetsAPI,
                            GetEditableTicketAPI,
                            CreateRequestsForTicketAPI,
                            GetTicketTwikiAPI)
from api.request_api import (CreateRequestAPI,
                             DeleteRequestAPI,
                             UpdateRequestAPI,
                             GetRequestAPI,
                             GetEditableRequestAPI,
                             GetCMSDriverAPI,
                             GetConfigUploadAPI,
                             GetRequestJobDictAPI,
                             RequestNextStatus,
                             RequestPreviousStatus,
                             GetRequestRunsAPI,
                             UpdateRequestWorkflowsAPI,
                             RequestOptionResetAPI)
from api.search_api import SearchAPI
from api.settings_api import SettingsAPI
from api.system_api import (SubmissionWorkerStatusAPI,
                            SubmissionQueueAPI,
                            LockerStatusAPI,
                            UserInfoAPI,
                            ObjectsInfoAPI)


log_format = '[%(asctime)s][%(levelname)s] %(message)s'
logging.basicConfig(format=log_format, level=logging.DEBUG)

app = Flask(__name__,
            static_folder='./vue_frontend/dist/static',
            template_folder='./vue_frontend/dist')
# Set flask logging to warning
logging.getLogger('werkzeug').setLevel(logging.WARNING)

app.url_map.strict_slashes = False
api = Api(app)
CORS(app,
     allow_headers=['Content-Type',
                    'Authorization',
                    'Access-Control-Allow-Credentials'],
     supports_credentials=True)


@app.route('/', defaults={'_path': ''})
@app.route('/<path:_path>')
def catch_all(_path):
    """
    Return index.html for all paths except API
    """
    return render_template('index.html')


@app.route('/api', defaults={'_path': ''})
@app.route('/api/<path:_path>')
def api_documentation(_path):
    """
    Endpoint for API documentation HTML
    """
    docs = {}
    for endpoint, view in app.view_functions.items():
        view_class = dict(view.__dict__).get('view_class')
        if view_class is None:
            continue

        class_name = view_class.__name__
        class_doc = view_class.__doc__.strip()
        #pylint: disable=protected-access
        urls = sorted([r.rule for r in app.url_map._rules_by_endpoint[endpoint]])
        #pylint: enable=protected-access
        category = [x for x in urls[0].split('/') if x][1]
        if category not in docs:
            docs[category] = {}

        docs[category][class_name] = {'doc': class_doc, 'urls': urls, 'methods': {}}
        for method_name in view_class.methods:
            method = view_class.__dict__.get(method_name.lower())
            method_dict = {'doc': method.__doc__.strip()}
            docs[category][class_name]['methods'][method_name] = method_dict
            if hasattr(method, '__role__'):
                method_dict['role'] = getattr(method, '__role__')

    return render_template('api_documentation.html', docs=docs)


api.add_resource(SearchAPI, '/api/search')

api.add_resource(SettingsAPI,
                 '/api/settings/get',
                 '/api/settings/get/<string:name>')

api.add_resource(SubmissionWorkerStatusAPI, '/api/system/workers')
api.add_resource(SubmissionQueueAPI, '/api/system/queue')
api.add_resource(LockerStatusAPI, '/api/system/locks')
api.add_resource(UserInfoAPI, '/api/system/user_info')
api.add_resource(ObjectsInfoAPI, '/api/system/objects_info')

api.add_resource(CreateSubcampaignAPI, '/api/subcampaigns/create')
api.add_resource(DeleteSubcampaignAPI, '/api/subcampaigns/delete')
api.add_resource(UpdateSubcampaignAPI, '/api/subcampaigns/update')
api.add_resource(GetSubcampaignAPI, '/api/subcampaigns/get/<string:prepid>')
api.add_resource(GetEditableSubcampaignAPI,
                 '/api/subcampaigns/get_editable',
                 '/api/subcampaigns/get_editable/<string:prepid>')
api.add_resource(GetDefaultSubcampaignSequenceAPI,
                 '/api/subcampaigns/get_default_sequence',
                 '/api/subcampaigns/get_default_sequence/<string:prepid>')

api.add_resource(CreateTicketAPI, '/api/tickets/create')
api.add_resource(DeleteTicketAPI, '/api/tickets/delete')
api.add_resource(UpdateTicketAPI, '/api/tickets/update')
api.add_resource(GetTicketAPI, '/api/tickets/get/<string:prepid>')
api.add_resource(GetEditableTicketAPI,
                 '/api/tickets/get_editable',
                 '/api/tickets/get_editable/<string:prepid>')
api.add_resource(GetTicketDatasetsAPI, '/api/tickets/get_datasets')
api.add_resource(CreateRequestsForTicketAPI,
                 '/api/tickets/create_requests')
api.add_resource(GetTicketTwikiAPI,
                 '/api/tickets/twiki_snippet/<string:prepid>')

api.add_resource(CreateRequestAPI, '/api/requests/create')
api.add_resource(DeleteRequestAPI, '/api/requests/delete')
api.add_resource(UpdateRequestAPI, '/api/requests/update')
api.add_resource(GetRequestAPI, '/api/requests/get/<string:prepid>')
api.add_resource(GetEditableRequestAPI,
                 '/api/requests/get_editable',
                 '/api/requests/get_editable/<string:prepid>')
api.add_resource(GetCMSDriverAPI, '/api/requests/get_cmsdriver/<string:prepid>')
api.add_resource(GetConfigUploadAPI, '/api/requests/get_config_upload/<string:prepid>')
api.add_resource(GetRequestJobDictAPI, '/api/requests/get_dict/<string:prepid>')
api.add_resource(RequestNextStatus, '/api/requests/next_status')
api.add_resource(RequestPreviousStatus, '/api/requests/previous_status')
api.add_resource(GetRequestRunsAPI, '/api/requests/get_runs/<string:prepid>')
api.add_resource(UpdateRequestWorkflowsAPI, '/api/requests/update_workflows')
api.add_resource(RequestOptionResetAPI, '/api/requests/option_reset')


def main():
    """
    Main function: start Flask web server
    """
    parser = argparse.ArgumentParser(description='ReReco Machine')
    parser.add_argument('--debug',
                        help='Run Flask in debug mode',
                        action='store_true')

    Database.set_database_name('rereco')
    Database.add_search_rename('requests', 'runs', 'runs<int>')
    Database.add_search_rename('requests', 'run', 'runs<int>')
    Database.add_search_rename('requests', 'workflows', 'workflows.name')
    Database.add_search_rename('requests', 'workflow', 'workflows.name')
    Database.add_search_rename('requests', 'output_dataset', 'output_datasets')

    args = vars(parser.parse_args())
    debug = args.get('debug', False)
    app.run(host='0.0.0.0',
            port=8002,
            threaded=True,
            debug=debug)

if __name__ == '__main__':
    main()
