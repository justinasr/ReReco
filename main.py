from api.campaign_api import CreateCampaignAPI, DeleteCampaignAPI, UpdateCampaignAPI, GetCampaignAPI
from api.flow_api import CreateFlowAPI, DeleteFlowAPI, UpdateFlowAPI, GetFlowAPI
from api.search_api import SearchAPI
from core.database.database import Database
import logging
from flask_restful import Api
from flask import Flask, render_template
from flask_cors import CORS


__LOG_FORMAT = '[%(asctime)s][%(levelname)s] %(message)s'
logging.basicConfig(format=__LOG_FORMAT, level=logging.DEBUG)

app = Flask(__name__,
            static_folder="./html/static",
            template_folder="./html")
app.url_map.strict_slashes = False
api = Api(app)
CORS(app,
     allow_headers=["Content-Type",
                    "Authorization",
                    "Access-Control-Allow-Credentials"],
     supports_credentials=True)

api.add_resource(SearchAPI, '/api/search')

api.add_resource(CreateCampaignAPI, '/api/campaigns/create')
api.add_resource(DeleteCampaignAPI, '/api/campaigns/delete')
api.add_resource(UpdateCampaignAPI, '/api/campaigns/update')
api.add_resource(GetCampaignAPI, '/api/campaigns/get/<string:prepid>')

api.add_resource(CreateFlowAPI, '/api/flows/create')
api.add_resource(DeleteFlowAPI, '/api/flows/delete')
api.add_resource(UpdateFlowAPI, '/api/flows/update')
api.add_resource(GetFlowAPI, '/api/flows/get/<string:prepid>')


# These methods will be deleted after development
@app.route('/')
def index():
    return render_template('index.html', objects=None, database=None)


@app.route('/campaigns')
def campaigns():
    db = Database('campaigns')
    campaigns = db.query(page=0, limit=db.get_count())
    for c in campaigns:
        del c['_id']

    return render_template('index.html', objects=campaigns, database='campaigns')


@app.route('/flows')
def flows():
    db = Database('flows')
    flows = db.query(page=0, limit=db.get_count())
    for f in flows:
        del f['_id']

    return render_template('index.html', objects=flows, database='flows')


app.run(host='0.0.0.0',
        port=5000,
        threaded=True,
        debug=True)
