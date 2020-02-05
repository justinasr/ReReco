from api.subcampaign_api import CreateSubcampaignAPI, DeleteSubcampaignAPI, UpdateSubcampaignAPI, GetSubcampaignAPI, GetEditableSubcampaignAPI, GetDefaultSubcampaignSequenceAPI
from api.subcampaign_ticket_api import CreateSubcampaignTicketAPI, DeleteSubcampaignTicketAPI, UpdateSubcampaignTicketAPI, GetSubcampaignTicketAPI, GetSubcampaignTicketDatasetsAPI, GetEditableSubcampaignTicketAPI, CreateRequestsForSubcampaignTicketAPI
from api.flow_api import CreateFlowAPI, DeleteFlowAPI, UpdateFlowAPI, GetFlowAPI
from api.request_api import CreateRequestAPI, DeleteRequestAPI, UpdateRequestAPI, GetRequestAPI, GetEditableRequestAPI, GetCMSDriverAPI, GetRequestJobDictAPI, RequestNextStatus
from api.search_api import SearchAPI
from api.system_api import SubmissionWorkerStatusAPI, LockerStatusAPI
from flask_restful import Api
from flask import Flask, render_template
from flask_cors import CORS
from core.utils.request_submitter import RequestSubmitter
import logging
import argparse


__LOG_FORMAT = '[%(asctime)s][%(levelname)s] %(message)s'
logging.basicConfig(format=__LOG_FORMAT, level=logging.DEBUG)

app = Flask(__name__,
            static_folder="./vue_frontend/dist/static",
            template_folder="./vue_frontend/dist")
app.url_map.strict_slashes = False
api = Api(app)
CORS(app,
     allow_headers=["Content-Type",
                    "Authorization",
                    "Access-Control-Allow-Credentials"],
     supports_credentials=True)


@app.route('/', defaults={'path': ''})
@app.route('/<path:path>')
def catch_all(path):
    return render_template('index.html')


@app.route('/api', defaults={'path': ''})
@app.route('/api/<path:path>')
def api_documentation(path):
    docs = {}
    for endpoint, view in app.view_functions.items():
        view_class = dict(view.__dict__).get('view_class')
        if view_class is None:
            continue

        class_name = view_class.__name__
        class_doc = view_class.__doc__.strip()
        urls = sorted([r.rule for r in app.url_map._rules_by_endpoint[endpoint]])
        category = [x for x in urls[0].split('/') if x][1]
        if category not in docs:
            docs[category] = {}

        docs[category][class_name] = {'doc': class_doc, 'urls': urls, 'methods': {}}
        for method_name in view_class.methods:
            method = view_class.__dict__.get(method_name.lower())
            docs[category][class_name]['methods'][method_name] = method.__doc__.strip()

    return render_template('api_documentation.html', docs=docs)


api.add_resource(SearchAPI, '/api/search')

api.add_resource(SubmissionWorkerStatusAPI, '/api/system/workers')
api.add_resource(LockerStatusAPI, '/api/system/locks')

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

api.add_resource(CreateSubcampaignTicketAPI, '/api/subcampaign_tickets/create')
api.add_resource(DeleteSubcampaignTicketAPI, '/api/subcampaign_tickets/delete')
api.add_resource(UpdateSubcampaignTicketAPI, '/api/subcampaign_tickets/update')
api.add_resource(GetSubcampaignTicketAPI, '/api/subcampaign_tickets/get/<string:prepid>')
api.add_resource(GetEditableSubcampaignTicketAPI,
                 '/api/subcampaign_tickets/get_editable',
                 '/api/subcampaign_tickets/get_editable/<string:prepid>')
api.add_resource(GetSubcampaignTicketDatasetsAPI, '/api/subcampaign_tickets/get_datasets')
api.add_resource(CreateRequestsForSubcampaignTicketAPI, '/api/subcampaign_tickets/create_requests')

api.add_resource(CreateFlowAPI, '/api/flows/create')
api.add_resource(DeleteFlowAPI, '/api/flows/delete')
api.add_resource(UpdateFlowAPI, '/api/flows/update')
api.add_resource(GetFlowAPI, '/api/flows/get/<string:prepid>')

api.add_resource(CreateRequestAPI, '/api/requests/create')
api.add_resource(DeleteRequestAPI, '/api/requests/delete')
api.add_resource(UpdateRequestAPI, '/api/requests/update')
api.add_resource(GetRequestAPI, '/api/requests/get/<string:prepid>')
api.add_resource(GetEditableRequestAPI,
                 '/api/requests/get_editable',
                 '/api/requests/get_editable/<string:prepid>')
api.add_resource(GetCMSDriverAPI, '/api/requests/get_cmsdriver/<string:prepid>')
api.add_resource(GetRequestJobDictAPI, '/api/requests/get_dict/<string:prepid>')
api.add_resource(RequestNextStatus, '/api/requests/next_status/<string:prepid>')

parser = argparse.ArgumentParser(description='Stats2')
parser.add_argument('--debug',
                    help='Run Flask in debug mode',
                    action='store_true')

args = vars(parser.parse_args())
debug = args.get('debug', False)
# rs = RequestSubmitter()
app.run(host='0.0.0.0',
        port=8005,
        threaded=True,
        debug=debug)
