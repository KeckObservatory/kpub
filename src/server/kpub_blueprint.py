from flask import Blueprint, request, make_response
import pdb
import typing
from typing import List, Dict
from flask.json import jsonify
from astroplan import Observer
from bson.objectid import ObjectId
from datetime import datetime
from astropy.time import Time
import requests
from common import obsid_is_admin, handle_error, lowercaseKeys
from astroquery.vizier import Vizier
from db_conn_mongo import db_conn_mongo
from db_conn import db_conn
from base64 import b64decode
from target_functions import KECK_LAT, KECK_LONG, KECK_ELEVATION, alt_az_deg, get_hour_angle, hours_to_deg
import logging
from common import parse_config
from schedule_functions import get_info_by_observer

API = 'kpub'
CONFIG_NAME = "config.live.ini"
CONFIG = parse_config(CONFIG_NAME)

DATABASE = CONFIG[API]["database"]
COLLECTION = CONFIG[API]["collection"]

logger = logging.getLogger(API)
logger.setLevel(logging.INFO)

kpub_api = Blueprint(API, __name__)

def get_staffid_from_cookie():
    staffCookie = request.json.get("staff_cookie")
    # obsid cookie is encoded end of string
    encodedstaff = staffCookie.split('username=')[-1]
    if encodedstaff:
        username = b64decode(encodedstaff)
        username = username.decode('utf-8')
        return int()

@handle_error
@planning_tool_api.route('/userinfo', methods=['POST'])
def userinfo() -> dict:
    obsid = get_obsid_from_cookie()
    if not obsid:
        return make_response(jsonify("observer cookie not found"), 401)
    isAdmin = obsid_is_admin(obsid, API)
    keckOpsDb = db_conn(CONFIG_NAME, "keckOperations")
    userinfo = get_info_by_observer(keckOpsDb, internal=False, obsid=obsid,
                                firstName=None, lastName=None, email=None)
    userinfo = userinfo[0]
    if isAdmin:
        userinfo["admin"] = True
    return jsonify(userinfo)

@handle_error
@kpub_api.route('/update', methods=['GET'])
def update(self):
    """
    Update the KPUB database with the latest data from the KPUB API.
    """
    # Get the obsid from the cookie
    obsid = get_obsid_from_cookie()
    
    # Check if obsid is valid
    if not obsid:
        return jsonify({"error": "Invalid obsid"}), 400
    
    # Connect to the KPUB database
    db = db_conn_mongo(CONFIG_NAME, DATABASE, COLLECTION)
    
    # Check if connection was successful
    if db.error:
        return jsonify({"error": db.error}), 500
    
    # Get the latest data from the KPUB API
    response = requests.get(f"https://kpub-api.keck.hawaii.edu/v1/obs/{obsid}")
    
    # Check if the request was successful
    if response.status_code != 200:
        return jsonify({"error": "Failed to fetch data from KPUB API"}), 500
    
    # Parse the response data
    data = response.json()
    
    # Update the KPUB database with the new data
    db.collection.update_one({"_id": ObjectId(obsid)}, {"$set": data})
    
    return jsonify({"message": "KPUB database updated successfully"}), 200
