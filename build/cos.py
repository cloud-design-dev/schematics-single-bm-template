import sys
import json
import base64
import os
import time
from ibm_schematics.schematics_v1 import SchematicsV1
from ibm_cloud_sdk_core.authenticators import IAMAuthenticator
from ibm_cloud_sdk_core import ApiException
import logging
from logdna import LogDNAHandler
import ibm_boto3
from ibm_botocore.client import Config, ClientError
from dotenv import load_dotenv

load_dotenv()
authenticator = IAMAuthenticator(
    apikey=os.environ.get('IBMCLOUD_API_KEY'),
    client_id='bx',
    client_secret='bx'
    )

refreshToken = authenticator.token_manager.request_token()['refresh_token']

# Future: Use this to set anything that needs the IBM IAM API authenicator
# def ibmClient():
# # Set up IAM authenticator and pull refresh token
#     authenticator = IAMAuthenticator(
#         apikey=os.environ.get('IBMCLOUD_API_KEY'),
#         client_id='bx',
#         client_secret='bx'
#         )

#     refreshToken = authenticator.token_manager.request_token()['refresh_token']

#     return authenticator, refreshToken

def cosClient():
    # Constants for IBM COS values
    cosEndpoint = ("https://" + os.environ.get('COS_ENDPOINT'))
    cosApiKey = os.environ.get('COS_API_KEY_ID')
    cosInstanceCrn    = os.environ.get('COS_INSTANCE_CRN')
    cos = ibm_boto3.resource("s3",
        ibm_api_key_id=cosApiKey,
        ibm_service_instance_id=cosInstanceCrn,
        config=Config(signature_version="oauth"),
        endpoint_url=cosEndpoint
    )

    return cos

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

def cosPullBuckets():
    client = cosClient()
    buckets = client.buckets.all()
    for bucket in buckets:
        print(bucket.name)

def schematicsClient():
    schClient = SchematicsV1(authenticator=authenticator)
    schematicsURL = "https://us.schematics.cloud.ibm.com"
    schClient.set_service_url(schematicsURL)
    return schClient

def getWsOutput():
    client = schematicsClient()
    workspaceId = os.environ.get('WORKSPACE_ID')
    wsOutput = client.get_workspace_outputs(
        w_id=workspaceId,
    ).get_result()

    instanceId = (wsOutput[0]['output_values'][0]['instance_id']['value'])
    return instanceId

def writeCosFile(instance):
    client = cosClient()
    cosBucket = os.environ.get('COS_BUCKET')
    cosFile = os.environ.get('WORKSPACE_ID') + "-cancel.txt"
    cosFileContents = instance

    client.Object(cosBucket, cosFile).put(Body=cosFileContents)

    # return cosFile

def listBucketContents():
    client = cosClient()
    cosBucket = os.environ.get('COS_BUCKET')
    for obj in client.Bucket(cosBucket).objects.all():
        print(obj.key)

def get_item():
    client = cosClient()
    cosFile = os.environ.get('WORKSPACE_ID') + "-cancel.txt"
    cosBucket = os.environ.get('COS_BUCKET')
    print("Retrieving item from bucket: {0}, key: {1}".format(cosBucket, cosFile))
    try:
        file = client.Object(cosBucket, cosFile).get()
        transformed = file["Body"].read().decode("utf-8")
        print("File Contents: {0}".format(transformed))
        # print("File Contents: {0}".format(file["Body"].read()))
    except ClientError as be:
        print("CLIENT ERROR: {0}\n".format(be))
    except Exception as e:
        print("Unable to retrieve file contents: {0}".format(e))

try:
    getInstanceId = getWsOutput()
    writeCosFile(instance=getInstanceId)
    getItem = get_item()
    print(getItem)
except Exception as e:
    logging.error(e)

## workspaceId = os.environ.get('WORKSPACE_ID')