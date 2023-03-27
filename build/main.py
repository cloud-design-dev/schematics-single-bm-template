import sys
import json
import base64
import os
import time
from ibm_cloud_sdk_core.authenticators import IAMAuthenticator
from ibm_cloud_sdk_core import ApiException
from ibm_schematics.schematics_v1 import SchematicsV1
import ibm_boto3
from ibm_botocore.client import Config, ClientError

# Set up IAM authenticator and pull refresh token
authenticator = IAMAuthenticator(
    apikey=os.environ.get('IBMCLOUD_API_KEY'),
    client_id='bx',
    client_secret='bx'
    )

refreshToken = authenticator.token_manager.request_token()['refresh_token']

workspaceId = os.environ.get('WORKSPACE_ID')

# def logDnaLogger():
#     key = os.environ.get('LOGDNA_INGESTION_KEY')
#     log = logging.getLogger('logdna')
#     log.setLevel(logging.INFO)

#     options = {
#         'app': 'rolling-iaas',
#         'url': 'https://logs.us-south.logging.cloud.ibm.com/logs/ingest',
#     }

#     logger = LogDNAHandler(key, options)

#     log.addHandler(logger)

#     return log

def schematicsClient():
    schClient = SchematicsV1(authenticator=authenticator)
    schematicsURL = "https://us.schematics.cloud.ibm.com"
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
    client = schematicsClient()
    wsDestroy = client.destroy_workspace_command(
    w_id=workspaceId,
    refresh_token=refreshToken
    ).get_result()
    
    destroyActivityId = wsDestroy.get('activityid')
    while True:
        destroyStatus = client.get_job(job_id=destroyActivityId).get_result()['status']['workspace_job_status']['status_code']
        if (destroyStatus == 'job_in_progress' or destroyStatus == 'job_pending'):
            print("Workspace destroy in progress. Checking again in 2 minutes...")
            time.sleep(120)
        elif (destroyStatus == 'job_cancelled' or destroyStatus == 'job_failed'):
            print("Workspace apply failed. Please check the logs by running the following command: ibmcloud schematics job logs --id " + destroyActivityId)
            break
        else:
            print("Workspace apply complete. Gathering workspace outputs.")
            break

def planWorkspace():
    client = schematicsClient()
    # log = logDnaLogger()
    wsPlan = client.plan_workspace_command(
        w_id=workspaceId,
        refresh_token=refreshToken
    ).get_result()

    planActivityId = wsPlan.get('activityid')

    while True:
        planStatus = client.get_job(job_id=planActivityId).get_result()['status']['workspace_job_status']['status_code']
        if (planStatus == 'job_in_progress' or planStatus == 'job_pending'):
            print("Workspace apply in progress. Checking again in 2 minutes...")
            time.sleep(120)
        elif (planStatus == 'job_cancelled' or planStatus == 'job_failed'):
            print("Workspace apply failed. Please check the logs by running the following command: ibmcloud schematics job logs --id " + planActivityId)
            break
        else:
            print("Workspace apply complete. Gathering workspace outputs.")
            break

def applyWorkspace():
    client = schematicsClient()
    # log = logDnaLogger()
    wsApply = client.apply_workspace_command(
        w_id=workspaceId,
        refresh_token=refreshToken,
    ).get_result()

    applyActivityId = wsApply.get('activityid')

    while True:
        applyStatus = client.get_job(job_id=applyActivityId).get_result()['status']['workspace_job_status']['status_code']
        if (applyStatus == 'job_in_progress' or applyStatus == 'job_pending'):
            print("Workspace apply in progress. Checking again in 2 minutes...")
            time.sleep(120)
        elif (applyStatus == 'job_cancelled' or applyStatus == 'job_failed'):
            print("Workspace apply failed. Please check the logs by running the following command: ibmcloud schematics job logs --id " + applyActivityId)
            break
        else:
            print("Workspace apply complete. Gathering workspace outputs.")
            break

def pullInstanceId():
    client = schematicsClient()
    wsOutputs = client.get_workspace_outputs(
        w_id=workspaceId,
    ).get_result()

    instanceIdOutput = wsOutputs[0]['output_values'][0]['instance_id']['value']

    return instanceIdOutput

# def cosClient():
#     # Constants for IBM COS values
#     cosEndpoint = ("https://" + os.environ.get('COS_ENDPOINT'))
#     cosApiKey = os.environ.get('COS_API_KEY')
#     cosInstanceCrn    = os.environ.get('COS_INSTANCE_CRN')
#     cos = ibm_boto3.resource("s3",
#         ibm_api_key_id=cosApiKey,
#         ibm_service_instance_id=cosInstanceCrn,
#         config=Config(signature_version="oauth"),
#         endpoint_url=cosEndpoint
#     )
#     return cos

# def writeCosFile(instance, cosFile):
#     client = cosClient()
#     cosBucket = os.environ.get('COS_BUCKET')
#     cosFile = cosFile
#     cosFileContents = instance

#     client.Object(cosBucket, cosFile).put(Body=cosFileContents)


try:
    currentStatus = getWorkspaceStatus()
    print("Current workspace status: " + currentStatus)
    planWorkspace()
    applyWorkspace()
    # if (currentStatus == 'INACTIVE'):
    #     print("Workspace is INACTIVE state, no resources need to be destroyed.")
    #     print("Running plan to deploy new resources.")
    #     print("I would run planWorkspace() here")
    #     print("Workspace plan complete. Running apply to deploy new resources.")
    #     print("I would run applyWorkspace() here")
    #     print("Workspace apply complete. New resources deployed.")
    # else:
    #     print("Workspace is in ACTIVE state, running destroy command to remove resources.")
    #     print("I would run deleteWorkspaceResources() here")
    #     print("Workspace cancelled. Running plan to deploy new resources.")
    #     print("I would run planWorkspace() here")
    #     print("Workspace plan complete. Running apply to deploy new resources.")
    #     print("I would run applyWorkspace() here")
    #     print("Workspace apply complete. New resources deployed.")

    # print("Post Action 1: Pull current output for instance_id and write to COS cancellation bucket [future state].")
    # pullInstanceIdOutput = pullInstanceId()
    # print("Current instance ID is: " + str(pullInstanceIdOutput))
    # print("writing to COS bucket")
    # writeCosFile(instance=pullInstanceIdOutput, cosFile='cancel-queue/' + instance + '-cancel.txt')
    # print("File written to COS bucket.")

except ApiException as ae:
    print("Pull of outputs failed.")
    print(" - status code: " + str(ae.code))
    print(" - error message: " + ae.message)
    if ("reason" in ae.http_response.json()):
        print(" - reason: " + ae.http_response.json()["reason"])
