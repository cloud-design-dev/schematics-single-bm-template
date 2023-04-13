import os
import json
import sys
import SoftLayer
from SoftLayer import TicketManager, Client, IAMClient
from ibm_cloud_sdk_core.authenticators import IAMAuthenticator
from ibm_cloud_sdk_core import ApiException

## Construct IAM Authentication using IBMCLOUD_API_KEY Environment variable
authenticator = IAMAuthenticator(os.environ.get('IBMCLOUD_API_KEY'))
# accessToken = authenticator.token_manager.request_token()['access_token']
refreshToken = authenticator.token_manager.request_token()['refresh_token']
iamclient = SoftLayer.create_client_from_env(username='apikey', api_key=os.environ.get('IBMCLOUD_API_KEY'))

vsInstances = iamclient['Account'].getVirtualGuests()
print(vsInstances)
# def slClient():
#     client = SoftLayer.authenticate_with_iam_token(
#         username=os.environ.get('IAAS_CLASSIC_USERNAME'),
#         api_key=os.environ.get('IAAS_CLASSIC_API_KEY')
#     )
#     return client
