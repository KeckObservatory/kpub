from email_validator import validate_email, EmailNotValidError
import requests
from datetime import datetime, timedelta 
import pytz
from flask import request, abort, make_response, jsonify
import logging
from logging.handlers import RotatingFileHandler
import os
import hashlib
from base64 import b64decode
from Crypto.Cipher import AES
import yaml
from smtplib import SMTP
from email.mime.text import MIMEText
import sys

lowercaseKeys = lambda d: {k.lower(): v for k,v in d.items()}

def parse_config(name):
    if not os.path.isfile(name):
        print("Config file does not exist")
        config = False
        sys.exit()
    with open(name) as f: 
        config = yaml.safe_load(f)
    return config

CONFIG_NAME = 'config.live.ini'
config = parse_config(CONFIG_NAME)

def create_logger(subsystem="keckOperations", savepath=None):
    formatter = logging.Formatter('%(asctime)s - %(name)s - %(levelname)s - %(message)s')
    ch = logging.StreamHandler()
    ch.setLevel(logging.INFO)
    ch.setFormatter(formatter)
    logger = logging.getLogger(subsystem)
    logger.addHandler(ch)
    if savepath:
        filepath = os.path.join(savepath, subsystem+'.log')
        if not os.path.exists(savepath):
            os.makedirs(savepath)
        fh = RotatingFileHandler(filepath, maxBytes=10000000, backupCount=5)
        fh.setLevel(logging.INFO)
        fh.setFormatter(formatter)
        logger.addHandler(fh)
    logger.setLevel(logging.INFO)
    return logger

def is_internal_ip():
    """
    Returns true/false whether or not the IP from which the request originated
    is an internal IP.

    :param: ip: IP address from header
    :type: ip: str
    :return: True/False
    :rtype: Boolean
    """

    internal = False

    # Header from www3
    ip = request.headers.get("X-Forwarded-For")

    # If it doesn't exist, then check the remote IP from Flask
    if not ip:
        ip = request.remote_addr

    # Get list of allowed IPs from config
    internalList = []
    internalList = config["internal"]

    # Always default to internal if internalList is empty or no IP
    if len(internalList) == 0 or not ip:
        return True

    for check in internalList:
        if ip.startswith(check):
            internal = True

    # Verify if IP is internal
    check = [i for i in internalList if ip.startswith(i)]
    internal = True if len(check) > 0 else False

    return internal

#---------------------------------------
# Decorators 
#---------------------------------------

def handle_error(fun):
    def decorator(*args, **kwargs):
        try:
            return fun(*args, **kwargs)
        except KeyError as err:
            output = [{"status":"ERROR", "message":str(err), "details":f"check input"}]
            abort(make_response(jsonify(output), 400))
    return decorator 

def internal_route(fun):
    def decorator(*args, **kwargs):
        internal = is_internal_ip()
        if not internal:
            output = [{"status":"ERROR", "message":"INTERNAL_USE_ONLY",
                       "details":f"route is internal: {internal}"}]
            return output
        return fun(*args, **kwargs) 
    return decorator

def is_admin():
    """
    Check if the user is an admin.
    """
    encryptedStaff = request.cookies.get('staff')
    if not encryptedStaff:
        return False
    # Decode the staff cookie
    try:
        staff = b64decode(encryptedStaff).decode('utf-8')
        staff = lowercaseKeys(staff)
    except Exception as e:
        return False
    # Check if the user is in the admin list
    adminList = config["admin"]
    if staff in adminList:
        return True
    return False

def admin_route(fun):
    def decorator(*args, **kwargs):
        encryptedStaff = request.cookies.get('staff')
        admin = is_admin()
        if not encryptedStaff:
            output = [{"status":"ERROR", "message":"Admin requires staff cookie. None found."}]
            return output
        if not admin:
            output = [{"status":"ERROR", "message":"ADMIN_USE_ONLY", "details":f"user {encryptedStaff} not in admin list"}]
            return output
        return fun(*args, **kwargs)
    return decorator