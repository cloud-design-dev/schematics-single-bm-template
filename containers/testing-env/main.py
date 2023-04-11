import os
import logging
from logdna import LogDNAHandler
import time
from ibm_cloud_sdk_core.authenticators import IAMAuthenticator
from ibm_cloud_sdk_core import ApiException
from ibm_schematics.schematics_v1 import SchematicsV1
from datetime import datetime
from ibm_platform_services import GlobalTaggingV1
import SoftLayer
from SoftLayer import VSManager, Client



# Set up IAM authenticator and pull refresh token
authenticator = IAMAuthenticator(
    apikey=os.environ.get('IBMCLOUD_API_KEY'),
    client_id='bx',
    client_secret='bx'
    )

refreshToken = authenticator.token_manager.request_token()['refresh_token']

def logDnaLogger():
    key = os.environ.get('LOGDNA_INGESTION_KEY')
    log = logging.getLogger('logdna')
    log.setLevel(logging.INFO)

    options = {
        'index_meta': True,
        'tags': 'testing-ce-private-endpoints',
        'url': 'https://logs.private.us-south.logging.cloud.ibm.com/logs/ingest',
        'log_error_response': True
    }

    logger = LogDNAHandler(key, options)

    log.addHandler(logger)

    return log

def slClient():
    client = SoftLayer.create_client_from_env(
        username='apikey',
        api_key=os.environ.get('IBMCLOUD_API_KEY'),
        endpoint_url='https://api.service.softlayer.com/rest/v3.1/'
    )
    return client

def schematicsClient():
    client = SchematicsV1(authenticator=authenticator)
    schematicsURL = 'https://private-us-east.schematics.cloud.ibm.com'
    client.set_service_url(schematicsURL)
    return client

def getWorkspaces():
    client = schematicsClient()
    workspaces = client.list_workspaces().get_result()
    for workspace in workspaces:
        log.info(workspace['id'])

def getVirtualGuests():
    client = slClient()
    virtualGuests = client['Account'].getVirtualGuests()
    for virtualGuest in virtualGuests:
        log.info(virtualGuest['id'])

try:
    log = logDnaLogger()
    log.info(":: Attempting list of workspaces using the private endpoint")
    getWorkspaces()
    log.info(":: Attempting list of virtual guests using the private endpoint")
    getVirtualGuests()
except ApiException as ae:
    log.error(":: Code failed.")
    log.error(" - status code: " + str(ae.code))
    log.error(" - error message: " + ae.message)
    if ("reason" in ae.http_response.json()):
        log.error(" - reason: " + ae.http_response.json()["reason"])