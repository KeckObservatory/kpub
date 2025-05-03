from flask_swagger_ui import get_swaggerui_blueprint
from flask import Flask, jsonify
from os.path import isfile
from socket import gethostname
from kpub_blueprint import kpub_api
import eventlet
from eventlet import wsgi
from common import create_logger, parse_config, is_internal_ip, admin_route
import yaml
import logging
import pdb


API = "kpub"
logger = create_logger(API, './logs')
configname = "config.live.ini"

app = Flask(__name__)

#---------------------------------------
# PlanningTool API Routes
#---------------------------------------

@app.route("/", methods=["GET"])
def home():
    """
    Just display usage
    """
    return {"status":"ERROR"}

@app.route(f"/api/{API}/{API}_api.yaml", methods=["GET"]) #needed to test locally
@app.route(f"/{API}/{API}_api.yaml", methods=["GET"]) #needed to test locally
def swagger():
    planning_tool_api_path = f'./docs/{API}_api.yaml'
    with open(planning_tool_api_path, 'r') as f:
        return jsonify(yaml.safe_load(f))

#---------------------------------------
config = parse_config(configname)
# Parse config file
host  = gethostname() #"vm-appserver.keck.hawaii.edu" #"0.0.0.0"
port  = config[API]["port"]
debug = config[API]["debug"]
# Configure Swagger UI
SWAGGER_URL = f"/{API}/swagger"
API_URL = f"/api/{API}/{API}_api.yaml"
swaggerui_blueprint = get_swaggerui_blueprint(
    SWAGGER_URL,
    API_URL,
    config={
        "app_name": f"{API.upper()}_API"
    }
)
app.register_blueprint(swaggerui_blueprint, url_prefix=SWAGGER_URL)
app.register_blueprint(kpub_api, url_prefix="/kpub")

if __name__ == "__main__":
    # Start the Flask server
    logger.info(f"Starting {API} server on {host}:{port}") 
    wsgi.server(eventlet.listen((host, port)), app, debug=config[API]["debug"])
