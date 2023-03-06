"""
Application module: Create Flask app and set configurations
"""
import os
import os.path
import sys
import logging
import logging.handlers
from flask_restful import Api
from flask_cors import CORS
from flask import Flask, request, session, render_template
from werkzeug.middleware.proxy_fix import ProxyFix
from jinja2.exceptions import TemplateNotFound
from core_lib.middlewares.auth import AuthenticationMiddleware
from core_lib.database.database import Database
from core_lib.utils.global_config import Config
from core_lib.utils.username_filter import UsernameFilter
from api.subcampaign_api import (
    CreateSubcampaignAPI,
    DeleteSubcampaignAPI,
    UpdateSubcampaignAPI,
    GetSubcampaignAPI,
    GetEditableSubcampaignAPI,
    GetDefaultSubcampaignSequenceAPI,
)
from api.ticket_api import (
    CreateTicketAPI,
    DeleteTicketAPI,
    UpdateTicketAPI,
    GetTicketAPI,
    GetTicketDatasetsAPI,
    GetTicketRequestsAPI,
    GetEditableTicketAPI,
    CreateRequestsForTicketAPI,
    GetTicketTwikiAPI,
)
from api.request_api import (
    CreateRequestAPI,
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
    GetRequestLumisectionsAPI,
    UpdateRequestWorkflowsAPI,
    RequestOptionResetAPI,
)
from api.search_api import SearchAPI, SuggestionsAPI, WildSearchAPI
from api.settings_api import SettingsAPI
from api.system_api import (
    SubmissionWorkerStatusAPI,
    SubmissionQueueAPI,
    LockerStatusAPI,
    UserInfoAPI,
    ObjectsInfoAPI,
    BuildInfoAPI,
    UptimeInfoAPI,
)


log_format = "[%(asctime)s][%(levelname)s] %(message)s"
logging.basicConfig(format=log_format, level=logging.DEBUG)

app = Flask(
    __name__,
    static_folder="./vue_frontend/dist/static",
    template_folder="./vue_frontend/dist",
)
# Set flask logging to warning
logging.getLogger("werkzeug").setLevel(logging.WARNING)
# Set paramiko logging to warning
logging.getLogger("paramiko").setLevel(logging.WARNING)

app.url_map.strict_slashes = False
# Handle redirections from a reverse proxy
app.wsgi_app = ProxyFix(app.wsgi_app, x_for=1, x_proto=1, x_host=1, x_prefix=1)

api = Api(app)
CORS(
    app,
    allow_headers=["Content-Type", "Authorization", "Access-Control-Allow-Credentials"],
    supports_credentials=True,
)

# OIDC client
# We require some environment variables to configure properly this component
# Instantiate the middleware inside the main function
auth: AuthenticationMiddleware = None
app.before_request(lambda: auth(request=request, session=session))


@app.route("/", defaults={"_path": ""})
@app.route("/<path:_path>")
def catch_all(_path):
    """
    Return index.html for all paths except API
    """
    try:
        return render_template("index.html")
    except TemplateNotFound:
        response = "<script>setTimeout(function() {location.reload();}, 5000);</script>"
        response += "Webpage is starting, please wait a few minutes..."
        return response


@app.route("/api", defaults={"_path": ""})
@app.route("/api/<path:_path>")
def api_documentation(_path):
    """
    Endpoint for API documentation HTML
    """
    docs = {}
    for endpoint, view in app.view_functions.items():
        view_class = dict(view.__dict__).get("view_class")
        if view_class is None:
            continue

        class_name = view_class.__name__
        class_doc = view_class.__doc__.strip()
        # pylint: disable=protected-access
        urls = sorted([r.rule for r in app.url_map._rules_by_endpoint[endpoint]])
        # pylint: enable=protected-access
        if _path:
            urls = [u for u in urls if u.startswith(f"/api/{_path}")]
            if not urls:
                continue

        category = [x for x in urls[0].split("/") if x][1]
        if category not in docs:
            docs[category] = {}

        docs[category][class_name] = {"doc": class_doc, "urls": urls, "methods": {}}
        for method_name in view_class.methods:
            method = view_class.__dict__.get(method_name.lower())
            method_dict = {"doc": method.__doc__.strip()}
            docs[category][class_name]["methods"][method_name] = method_dict
            if hasattr(method, "__role__"):
                method_dict["role"] = getattr(method, "__role__")

    return render_template("api_documentation.html", docs=docs)


api.add_resource(SearchAPI, "/api/search")
api.add_resource(SuggestionsAPI, "/api/suggestions")
api.add_resource(WildSearchAPI, "/api/wild_search")

api.add_resource(SettingsAPI, "/api/settings/get", "/api/settings/get/<string:name>")

api.add_resource(SubmissionWorkerStatusAPI, "/api/system/workers")
api.add_resource(SubmissionQueueAPI, "/api/system/queue")
api.add_resource(LockerStatusAPI, "/api/system/locks")
api.add_resource(UserInfoAPI, "/api/system/user_info")
api.add_resource(ObjectsInfoAPI, "/api/system/objects_info")
api.add_resource(BuildInfoAPI, "/api/system/build_info")
api.add_resource(UptimeInfoAPI, "/api/system/uptime")

api.add_resource(CreateSubcampaignAPI, "/api/subcampaigns/create")
api.add_resource(DeleteSubcampaignAPI, "/api/subcampaigns/delete")
api.add_resource(UpdateSubcampaignAPI, "/api/subcampaigns/update")
api.add_resource(GetSubcampaignAPI, "/api/subcampaigns/get/<string:prepid>")
api.add_resource(
    GetEditableSubcampaignAPI,
    "/api/subcampaigns/get_editable",
    "/api/subcampaigns/get_editable/<string:prepid>",
)
api.add_resource(
    GetDefaultSubcampaignSequenceAPI,
    "/api/subcampaigns/get_default_sequence",
    "/api/subcampaigns/get_default_sequence/<string:prepid>",
)

api.add_resource(CreateTicketAPI, "/api/tickets/create")
api.add_resource(DeleteTicketAPI, "/api/tickets/delete")
api.add_resource(UpdateTicketAPI, "/api/tickets/update")
api.add_resource(GetTicketAPI, "/api/tickets/get/<string:prepid>")
api.add_resource(
    GetEditableTicketAPI,
    "/api/tickets/get_editable",
    "/api/tickets/get_editable/<string:prepid>",
)
api.add_resource(GetTicketDatasetsAPI, "/api/tickets/get_datasets")
api.add_resource(GetTicketRequestsAPI, "/api/tickets/get_requests")
api.add_resource(CreateRequestsForTicketAPI, "/api/tickets/create_requests")
api.add_resource(GetTicketTwikiAPI, "/api/tickets/twiki_snippet/<string:prepid>")

api.add_resource(CreateRequestAPI, "/api/requests/create")
api.add_resource(DeleteRequestAPI, "/api/requests/delete")
api.add_resource(UpdateRequestAPI, "/api/requests/update")
api.add_resource(GetRequestAPI, "/api/requests/get/<string:prepid>")
api.add_resource(
    GetEditableRequestAPI,
    "/api/requests/get_editable",
    "/api/requests/get_editable/<string:prepid>",
)
api.add_resource(GetCMSDriverAPI, "/api/requests/get_cmsdriver/<string:prepid>")
api.add_resource(GetConfigUploadAPI, "/api/requests/get_config_upload/<string:prepid>")
api.add_resource(GetRequestJobDictAPI, "/api/requests/get_dict/<string:prepid>")
api.add_resource(RequestNextStatus, "/api/requests/next_status")
api.add_resource(RequestPreviousStatus, "/api/requests/previous_status")
api.add_resource(
    GetRequestRunsAPI,
    "/api/requests/get_runs",
    "/api/requests/get_runs/<string:prepid>",
)
api.add_resource(
    GetRequestLumisectionsAPI,
    "/api/requests/get_lumisections",
    "/api/requests/get_lumisections/<string:prepid>",
)
api.add_resource(UpdateRequestWorkflowsAPI, "/api/requests/update_workflows")
api.add_resource(RequestOptionResetAPI, "/api/requests/option_reset")


def setup_logging(debug):
    """
    Setup logging format and place - console for debug mode and rotating files for production
    """
    logger = logging.getLogger()
    logger.propagate = False
    if debug:
        handler = logging.StreamHandler(sys.stdout)
        handler.setLevel(logging.DEBUG)
    else:
        if not os.path.isdir("logs"):
            os.mkdir("logs")

        handler = logging.handlers.RotatingFileHandler(
            "logs/rereco.log", "a", 8 * 1024 * 1024, 50
        )
        handler.setLevel(logging.INFO)

    formatter = logging.Formatter(
        fmt="[%(asctime)s][%(user)s][%(levelname)s] %(message)s"
    )
    handler.setFormatter(formatter)
    handler.addFilter(UsernameFilter())
    logger.handlers.clear()
    logger.addHandler(handler)
    return logger


def set_app(
    config_path: str = "config.cfg", mode: str = "dev", debug: bool = True
) -> tuple[str, int, bool]:
    """
    Set Flask appplication configuration via config.cfg file

    Parameters
    ----------
    config_path : str
        Path to config.cfg file with all environment variables
    mode: str
        Web server deployment mode: dev or prod
    debug: bool
        Set DEBUG logging level

    Returns
    ----------
    tuple[str, int, bool]
        Host name, port number, debug mode configurations for deployment server
    """
    # Instantiate the middleware here
    # Configure cookie security settings for the Flask application
    global auth, app

    logger = setup_logging(debug)
    logger.info("Setting up Flask application in mode: %s", mode)
    logger.info("Configuration file path: %s", config_path)

    config = Config.load(config_path, mode)
    database_auth = config.get("database_auth")

    # Include the application secret key used to sign cookiess
    app.secret_key = config.get("secret_key")

    # Include the middleware
    logger.info("Creating authetication middleware")
    auth = AuthenticationMiddleware(
        app=app,
        client_id=config.get("oidc_client_id"),
        client_secret=config.get("oidc_client_secret"),
        home_endpoint="catch_all",
        valid_audiences=config.get("valid_audiences"),
    )
    logger.info("Authentication middleware: %s", auth)

    # Set application database
    Database.set_database_name("rereco")
    if database_auth:
        Database.set_credentials_file(database_auth)

    Database.add_search_rename("requests", "runs", "runs<int>")
    Database.add_search_rename("requests", "run", "runs<int>")
    Database.add_search_rename("requests", "workflows", "workflows.name")
    Database.add_search_rename("requests", "workflow", "workflows.name")
    Database.add_search_rename("requests", "output_dataset", "output_datasets")
    Database.add_search_rename("requests", "input_dataset", "input.dataset")
    Database.add_search_rename("requests", "input_request", "input.request")
    Database.add_search_rename("requests", "created_on", "history.0.time")
    Database.add_search_rename("requests", "created_by", "history.0.user")
    Database.add_search_rename("subcampaigns", "created_on", "history.0.time")
    Database.add_search_rename("subcampaigns", "created_by", "history.0.user")
    Database.add_search_rename("tickets", "created_on", "history.0.time")
    Database.add_search_rename("tickets", "created_by", "history.0.user")
    Database.add_search_rename("tickets", "subcampaign", "steps.subcampaign")
    Database.add_search_rename(
        "tickets", "processing_string", "steps.processing_string"
    )

    # Deployment server configuration
    port: int = int(config.get("port", 8002))
    host: str = config.get("host", "0.0.0.0")
    logger.info("Deployment host: %s:%d", host, port)
    logger.info("Debug mode: %s", debug)
    return host, port, debug
