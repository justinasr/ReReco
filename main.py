from api.campaign_api import CreateCampaignAPI, DeleteCampaignAPI, UpdateCampaignAPI, GetCampaignAPI, GetEditableCampaignAPI, GetDefaultCampaignSequenceAPI
from api.campaign_ticket_api import CreateCampaignTicketAPI, DeleteCampaignTicketAPI, UpdateCampaignTicketAPI, GetCampaignTicketAPI, GetCampaignTicketDatasetsAPI, GetEditableCampaignTicketAPI, CreateRequestsForCampaignTicketAPI
from api.flow_api import CreateFlowAPI, DeleteFlowAPI, UpdateFlowAPI, GetFlowAPI
from api.request_api import CreateRequestAPI, DeleteRequestAPI, UpdateRequestAPI, GetRequestAPI, GetEditableRequestAPI, GetCMSDriverCommands
from api.search_api import SearchAPI
import logging
from flask_restful import Api
from flask import Flask, render_template, redirect
from flask_cors import CORS


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

api.add_resource(CreateCampaignAPI, '/api/campaigns/create')
api.add_resource(DeleteCampaignAPI, '/api/campaigns/delete')
api.add_resource(UpdateCampaignAPI, '/api/campaigns/update')
api.add_resource(GetCampaignAPI, '/api/campaigns/get/<string:prepid>')
api.add_resource(GetEditableCampaignAPI, '/api/campaigns/get_editable', '/api/campaigns/get_editable/<string:prepid>')
api.add_resource(GetDefaultCampaignSequenceAPI, '/api/campaigns/get_default_sequence', '/api/campaigns/get_default_sequence/<string:prepid>')

api.add_resource(CreateCampaignTicketAPI, '/api/campaign_tickets/create')
api.add_resource(DeleteCampaignTicketAPI, '/api/campaign_tickets/delete')
api.add_resource(UpdateCampaignTicketAPI, '/api/campaign_tickets/update')
api.add_resource(GetCampaignTicketAPI, '/api/campaign_tickets/get/<string:prepid>')
api.add_resource(GetEditableCampaignTicketAPI, '/api/campaign_tickets/get_editable', '/api/campaign_tickets/get_editable/<string:prepid>')
api.add_resource(GetCampaignTicketDatasetsAPI, '/api/campaign_tickets/get_datasets')
api.add_resource(CreateRequestsForCampaignTicketAPI, '/api/campaign_tickets/create_requests')

api.add_resource(CreateFlowAPI, '/api/flows/create')
api.add_resource(DeleteFlowAPI, '/api/flows/delete')
api.add_resource(UpdateFlowAPI, '/api/flows/update')
api.add_resource(GetFlowAPI, '/api/flows/get/<string:prepid>')

api.add_resource(CreateRequestAPI, '/api/requests/create')
api.add_resource(DeleteRequestAPI, '/api/requests/delete')
api.add_resource(UpdateRequestAPI, '/api/requests/update')
api.add_resource(GetRequestAPI, '/api/requests/get/<string:prepid>')
api.add_resource(GetEditableRequestAPI, '/api/requests/get_editable', '/api/requests/get_editable/<string:prepid>')
api.add_resource(GetCMSDriverCommands, '/api/requests/get_cmsdrivers/<string:prepid>')

app.run(host='0.0.0.0',
        port=8003,
        threaded=True,
        debug=True)
