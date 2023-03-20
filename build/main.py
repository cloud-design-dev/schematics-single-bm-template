import sys
import json
import base64
import os
import time
from ibm_cloud_sdk_core.authenticators import IAMAuthenticator
from ibm_cloud_sdk_core import ApiException
from ibm_schematics.schematics_v1 import SchematicsV1
from dotenv import load_dotenv
import logging
from logdna import LogDNAHandler

load_dotenv()
# Set up IAM authenticator and pull refresh token
authenticator = IAMAuthenticator(
    apikey=os.environ.get('IBMCLOUD_API_KEY'),
    client_id='bx',
    client_secret='bx'
    )

refreshToken = authenticator.token_manager.request_token()['refresh_token']

osOption = os.environ.get('OS_OPTION')
workspaceId = os.environ.get('WORKSPACE_ID')
# Set up Schematics service client and declare workspace ID

def logDnaLogger():
    key = os.environ.get('LOGDNA_INGESTION_KEY')
    log = logging.getLogger('logdna')
    log.setLevel(logging.INFO)

    options = {
        'app': 'rolling-iaas',
        'url': 'https://logs.us-south.logging.cloud.ibm.com/logs/ingest',
    }

    logger = LogDNAHandler(key, options)

    log.addHandler(logger)

    return log

def schematicsClient():
    schClient = SchematicsV1(authenticator=authenticator)
    schematicsURL = "https://us.schematics.cloud.ibm.com"
    schClient.set_service_url(schematicsURL)
    return schClient

def deleteWorkspaceResources():
    client = schematicsClient()
    log = logDnaLogger()
    wsDestroy = client.destroy_workspace_command(
    w_id=workspaceId,
    refresh_token=refreshToken
    ).get_result()
    
    destroyActivityId = wsDestroy.get('activityid')
    while True:
        destroyStatus = client.get_job(job_id=destroyActivityId).get_result()['status']['workspace_job_status']['status_code']
        if (destroyStatus == 'job_in_progress' or destroyStatus == 'job_pending'):
            log.info("Workspace destroy in progress. Checking again in 2 minutes...")
            time.sleep(120)
        elif (destroyStatus == 'job_cancelled' or destroyStatus == 'job_failed'):
            log.error("Workspace apply failed. Please check the logs by running the following command: ibmcloud schematics job logs --id " + destroyActivityId)
            break
        else:
            log.info("Workspace apply complete. Gathering workspace outputs.")
            break

def planWorkspace():
    client = schematicsClient()
    log = logDnaLogger()
    action_options_template_model =  {
            'tf_vars': 'os=' + osOption
    }

    wsPlan = client.plan_workspace_command(
        w_id=workspaceId,
        refresh_token=refreshToken,
        action_options=[action_options_template_model]
    ).get_result()

    planActivityId = wsPlan.get('activityid')

    while True:
        planStatus = client.get_job(job_id=planActivityId).get_result()['status']['workspace_job_status']['status_code']
        if (planStatus == 'job_in_progress' or planStatus == 'job_pending'):
            log.info("Workspace apply in progress. Checking again in 2 minutes...")
            time.sleep(120)
        elif (planStatus == 'job_cancelled' or planStatus == 'job_failed'):
            log.error("Workspace apply failed. Please check the logs by running the following command: ibmcloud schematics job logs --id " + planActivityId)
            break
        else:
            log.info("Workspace apply complete. Gathering workspace outputs.")
            break

def applyWorkspace():
    client = schematicsClient()
    log = logDnaLogger()
    wsApply = client.apply_workspace_command(
        w_id=workspaceId,
        refresh_token=refreshToken,
    ).get_result()

    applyActivityId = wsApply.get('activityid')

    while True:
        applyStatus = client.get_job(job_id=applyActivityId).get_result()['status']['workspace_job_status']['status_code']
        if (applyStatus == 'job_in_progress' or applyStatus == 'job_pending'):
            log.info("Workspace apply in progress. Checking again in 2 minutes...")
            time.sleep(120)
        elif (applyStatus == 'job_cancelled' or applyStatus == 'job_failed'):
            log.error("Workspace apply failed. Please check the logs by running the following command: ibmcloud schematics job logs --id " + applyActivityId)
            break
        else:
            log.info("Workspace apply complete. Gathering workspace outputs.")
            break


def pullAllOutputs():
    client = schematicsClient()
    wsOutputs = client.get_workspace_outputs(
        w_id=workspaceId,
    ).get_result()

    outputs = wsOutputs[0]['output_values']

    return outputs

def pullInstanceId():
    client = schematicsClient()
    wsOutputs = client.get_workspace_outputs(
        w_id=workspaceId,
    ).get_result()

    instanceIdOutput = wsOutputs[0]['output_values'][0]['instance_id']['value']

    return instanceIdOutput

try:
    log = logDnaLogger()
    # log.info("Action 1: Pull current output for instance_id and write to etcd cancellation queue")
    # pullInstanceIdOutput = pullInstanceId()
    # log.info("Current instance ID is: " + str(pullInstanceIdOutput))
    # log.info("Action 2: Call workspace destroy command to remove resources.")
    # wsDestroy = deleteWorkspaceResources()
    log.info("Action 3: Run workspace plan to see if OS change is picked up")
    planWorkspace()
    log.info("Action 4: Run workspace apply to recreate resources")
    wsApply = applyWorkspace()
    log.info("Action 5: Pull new server output and write to current servers queue")
    newInstanceIdOutput = pullInstanceId()
    log.info("New instance ID is: " + str(newInstanceIdOutput))
except ApiException as ae:
    log.error("Pull of outputs failed.")
    log.error(" - status code: " + str(ae.code))
    log.error(" - error message: " + ae.message)
    if ("reason" in ae.http_response.json()):
        log.error(" - reason: " + ae.http_response.json()["reason"])
