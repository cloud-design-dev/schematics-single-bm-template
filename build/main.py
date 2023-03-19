import sys
import json
import base64
import os
from ibm_cloud_sdk_core.authenticators import IAMAuthenticator
from ibm_cloud_sdk_core import ApiException
from ibm_schematics.schematics_v1 import SchematicsV1
from dotenv import load_dotenv

load_dotenv()
# Set up IAM authenticator and pull refresh token
authenticator = IAMAuthenticator(
    apikey=os.environ.get('IBMCLOUD_API_KEY'),
    client_id='bx',
    client_secret='bx'
    )

refreshToken = authenticator.token_manager.request_token()['refresh_token']

workspaceId = os.environ.get('WORKSPACE_ID')
# Set up Schematics service client and declare workspace ID
def schematicsClient():
    schClient = SchematicsV1(authenticator=authenticator)
    schematicsURL = "https://us.schematics.cloud.ibm.com"
    schClient.set_service_url(schematicsURL)
    return schClient

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

    instanceIdOutput = wsOutputs[0]['output_values'][0]['instance_id']

    return instanceIdOutput

try:
    pullInstanceIdOutput = pullInstanceId()
    print("Var type is: " + str(type(pullInstanceIdOutput)))
    print(pullInstanceIdOutput)
except ApiException as ae:
    print("Pull of outputs failed.")
    print(" - status code: " + str(ae.code))
    print(" - error message: " + ae.message)
    if ("reason" in ae.http_response.json()):
        print(" - reason: " + ae.http_response.json()["reason"])
