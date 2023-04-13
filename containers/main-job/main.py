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
from SoftLayer import HardwareManager, Client



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
        'index_meta': True,
        'tags': 'rolling-iaas',
        'url': 'https://logs.private.us-south.logging.cloud.ibm.com/logs/ingest',
        'log_error_response': True,
        'level': 'info',
        'app': 'rolling-iaas-ce',
    }

    logger = LogDNAHandler(key, options)

    log.addHandler(logger)

    return log

def slClient():
    client = SoftLayer.create_client_from_env(
        username='apikey',
        api_key=os.environ.get('IBMCLOUD_API_KEY')
    )
    return client

def attachTag():
    client = slClient()
    hardwareManager = HardwareManager(client)
    instanceId = getDeployedServerId()
    hardwareManager.edit(hardware_id=instanceId, userdata=None, hostname=None, domain=None, notes=None, tags='reclaim_immediately')
    
def schematicsClient():
    client = SchematicsV1(authenticator=authenticator)
    schematicsURL = 'https://private-us-east.schematics.cloud.ibm.com'
    client.set_service_url(schematicsURL)
    return client

def getDeployedServerId():
    client = schematicsClient()
    wsOutputs = client.get_workspace_outputs(w_id=workspaceId).get_result()
    deployedServerId = wsOutputs[0]['output_values'][0]['instance_id']['value']
    return str(deployedServerId)

def deleteWorkspaceResources():
    log = logDnaLogger()
    client = schematicsClient()
    wsDestroy = client.destroy_workspace_command(
        w_id=workspaceId,
        refresh_token=refreshToken
    ).get_result()
    
    destroyActivityId = wsDestroy.get('activityid')

    while True:
        destroyStatus = client.get_job(job_id=destroyActivityId).get_result()['status']['workspace_job_status']['status_code']
        print("Current destroy status:", destroyStatus)
        log.info(destroyStatus)
        if destroyStatus == 'job_finished':
            log.info("Workspace resources successfully destroyed.")
            break
        elif destroyStatus in ['job_in_progress', 'job_pending']:
            log.info("Workspace destroy in progress. Checking again in 2 minutes...")
            time.sleep(120)
        elif destroyStatus in ['job_failed', 'job_cancelled']:
            log.error("Workspace destroy failed. Please check the logs by running the following command: ibmcloud schematics job logs --id " + destroyActivityId)
            break
        else:
            log.error("Unknown status code received from Schematics API: " + destroyStatus)
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
        print("Current plan status:", planStatus)
        if planStatus == 'job_finished':
            log.info("Workspace plan complete.")
            break
        elif planStatus in ['job_in_progress', 'job_pending']:
            log.info("Workspace plan in progress. Checking again in 2 minutes...")
            time.sleep(120)
        elif planStatus in ['job_failed', 'job_cancelled']:
            log.error("Workspace plan failed. Please check the logs by running the following command: ibmcloud schematics job logs --id " + planActivityId)
            break
        else:
            log.error("Unknown status code received from Schematics API: " + planActivityId)
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
        print("Current apply status:", applyStatus)
        if applyStatus == 'job_finished':
            log.info("Workspace plan complete.")
            break
        elif applyStatus in ['job_in_progress', 'job_pending']:
            log.info("Workspace apply in progress. Checking again in 10 minutes...")
            time.sleep(600)
        elif applyStatus in ['job_failed', 'job_cancelled']:
            log.error("Workspace apply failed. Please check the logs by running the following command: ibmcloud schematics job logs --id " + applyActivityId)
            break
        else:
            log.error("Unknown status code received from Schematics API: " + applyActivityId)
            break

try:
    log = logDnaLogger()
    log.info(":: Starting refresh for Workspace ID: " + workspaceId)
    deployedServerId = getDeployedServerId()
    if deployedServerId:
        log.info(":: Attaching 'reclaim_immediately' tag to server instance: " + str(deployedServerId))
        attachTag()
    else:
        log.warning("Deployed server ID is null or empty. Skipping tag attachment.")
    log.info(":: Starting workspace destroy.")
    deleteWorkspaceResources()
    log.info(":: Starting workspace plan.")
    planWorkspace()
    log.info(":: Starting workspace apply.")
    applyWorkspace()
    log.info(":: Workspace refresh complete.")

except ApiException as ae:
    log.error("Workspace operation failed.")
    log.error(" - status code: " + str(ae.code))
    log.error(" - error message: " + ae.message)
    if ("reason" in ae.http_response.json()):
        log.error(" - reason: " + ae.http_response.json()["reason"])