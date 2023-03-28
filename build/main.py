import os
import logging
from logdna import LogDNAHandler
import time
from ibm_cloud_sdk_core.authenticators import IAMAuthenticator
from ibm_cloud_sdk_core import ApiException
from ibm_schematics.schematics_v1 import SchematicsV1
from datetime import datetime

# Set up IAM authenticator and pull refresh token
authenticator = IAMAuthenticator(
    apikey=os.environ.get('IBMCLOUD_API_KEY'),
    client_id='bx',
    client_secret='bx'
    )

refreshToken = authenticator.token_manager.request_token()['refresh_token']

workspaceId = os.environ.get('WORKSPACE_ID')

def logDnaLogger():
    key = os.environ.get('LOGDNA_INGESTION_KEY')
    log = logging.getLogger('logdna')
    log.setLevel(logging.INFO)

    options = {
        'env': 'code-engine',
        'index_meta': True,
        'tags': str(workspaceId + '-ce-job'),
        'url': 'https://logs.private.us-south.logging.cloud.ibm.com/logs/ingest',
        'log_error_response': True
    }

    logger = LogDNAHandler(key, options)

    log.addHandler(logger)

    return log

def schematicsClient():
    schClient = SchematicsV1(authenticator=authenticator)
    schematicsURL = 'https://private-us-east.schematics.cloud.ibm.com'
    schClient.set_service_url(schematicsURL)
    return schClient

def getWorkspaceStatus():
    client = schematicsClient()
    wsStatus = client.get_workspace(
        w_id=workspaceId,
    ).get_result()

    status = wsStatus['status']
    return status

def deleteWorkspaceResources():
    log = logDnaLogger()
    client = schematicsClient()
    wsDestroy = client.destroy_workspace_command(
    w_id=workspaceId,
    refresh_token=refreshToken
    ).get_result()
    
    destroyActivityId = wsDestroy.get('activityid')
    # Next step is to check the status of the workspace vs the status of the job that is running the destroy command

    # Need to verify the status names that get returned from the API. I believe these all use UPPERCASE
    while True:
        destroyStatus = client.get_job(job_id=destroyActivityId).get_result()['status']['workspace_job_status']['status_code']
        if (destroyStatus == 'job_in_progress' or destroyStatus == 'job_pending'):
            log.info("Workspace destroy in progress. Checking again in 2 minutes...")
            time.sleep(120)
        elif (destroyStatus == 'job_cancelled' or destroyStatus == 'job_failed'):
            log.error("Workspace apply failed. Please check the logs by running the following command: ibmcloud schematics job logs --id " + destroyActivityId)
            break
        else:
            log.info("Workspace resources successfully destroyed. Starting workspace plan.")
            break

def planWorkspace():
    client = schematicsClient()
    log = logDnaLogger()
    wsPlan = client.plan_workspace_command(
        w_id=workspaceId,
        refresh_token=refreshToken
    ).get_result()

    planActivityId = wsPlan.get('activityid')

    while True:
        planStatus = client.get_job(job_id=planActivityId).get_result()['status']['workspace_job_status']['status_code']
        if (planStatus == 'job_in_progress' or planStatus == 'job_pending'):
            log.info("Workspace Plan in progress. Checking again in 2 minutes...")
            time.sleep(120)
        elif (planStatus == 'job_cancelled' or planStatus == 'job_failed'):
            log.error("Workspace plan failed. Please check the logs by running the following command: ibmcloud schematics job logs --id " + planActivityId)
            break
        else:
            log.info("Workspace Plan complete. Starting workspace apply.")
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
            log.info("Workspace apply in progress. Checking again in 10 minutes...")
            time.sleep(600)
        elif (applyStatus == 'job_cancelled' or applyStatus == 'job_failed'):
            log.error("Workspace apply failed. Please check the logs by running the following command: ibmcloud schematics job logs --id " + applyActivityId)
            break
        else:
            log.info("Workspace apply complete. Visit the following URL to see the deployed resources: https://cloud.ibm.com/schematics/workspaces/" + workspaceId + "/resources?region=us")
            break

try:
    log = logDnaLogger()
    deployTimestamp = datetime.now().strftime("%Y-%m-%d:%H:%M:%S")
    log.debug("Starting Code Engine job at " + deployTimestamp)
    workspaceStatus = getWorkspaceStatus()
    if (workspaceStatus == 'ACTIVE'): 
        log.info("Workspace is active. Starting destroy.")
        deleteWorkspaceResources()
        planWorkspace()
        applyWorkspace()
    elif (workspaceStatus == 'INACTIVE'):
        log.info("Workspace is inactive. Starting plan.")
        planWorkspace()
        applyWorkspace()
    else:
        log.error("Workspace is in an unknown state. Please check the workspace status and try again.")
    # currentStatus = getWorkspaceStatus()
    # log.debug("Current workspace status: " + currentStatus)
    # deleteWorkspaceResources()
    # planWorkspace()
    # applyWorkspace()
except ApiException as ae:
    log.error("Workspace operation failed.")
    log.error(" - status code: " + str(ae.code))
    log.error(" - error message: " + ae.message)
    if ("reason" in ae.http_response.json()):
        log.error(" - reason: " + ae.http_response.json()["reason"])