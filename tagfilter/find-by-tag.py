import os
import json
import sys
import SoftLayer
from SoftLayer import TicketManager, Client
from ibm_platform_services import ResourceManagerV2, GlobalSearchV2, GlobalTaggingV1
from ibm_cloud_sdk_core.authenticators import IAMAuthenticator
from ibm_cloud_sdk_core import ApiException

## Construct IAM Authentication using IBMCLOUD_API_KEY Environment variable
authenticator = IAMAuthenticator(os.environ.get('IBMCLOUD_API_KEY'))

def tagService():
    tagService = GlobalTaggingV1(authenticator=authenticator)
    tagService.set_service_url('https://tags.global-search-tagging.cloud.ibm.com')
    return tagService

def searchService():
    searchService = GlobalSearchV2(authenticator=authenticator)
    searchService.set_service_url('https://api.global-search-tagging.cloud.ibm.com')
    return searchService

def classicIaasTags():
    client = tagService()
    tag_list = client.list_tags(
        tag_type='user',
        attached_only=True,
        full_data=True,
        providers=['ims'],
        order_by_name='asc').get_result()

    print(json.dumps(tag_list, indent=2))

def getServiceInstances():
    client = searchService()
    tagQuery = '(family:ims) AND (tags:"project:rolling-iaas")'
    result = client.search(
        query=tagQuery,
        fields=["*"]
    ).get_result()
    resources = result['items']

    return list(resources)
# ##    print(str(len(resources)) + " bare metal instances match your search:")
#     for resource in resources:
#         print(resource['doc']['id'])

def slClient():
    client = SoftLayer.create_client_from_env(
        username=os.environ.get('IAAS_CLASSIC_USERNAME'),
        api_key=os.environ.get('IAAS_CLASSIC_API_KEY')
    )
    return client

## failing if the instance does not have an open cancellation ticket. In this case we have 1 machine that does not have an open cancellation ## ticket

def getOpenCancelTicket(instanceId):
    client = slClient()
    listinstances = getServiceInstances()
    for instance in listinstances:
        instanceId = instance['doc']['id']
        getOpenTicket = client['Hardware_Server'].getOpenCancellationTicket(id=instanceId)
        ticketId = getOpenTicket['id']
    
    print(ticketId)


try:
    listinstances = getServiceInstances()
    for instance in listinstances:
        instanceId = instance['doc']['id']
        getOpenCancelTicket(instanceId)


    # getOpenCancelTicket()
    # listInstances = getServiceInstances()
    # for instance in listInstances:
    #     print(instance['doc']['id'])
except ApiException as ex:
    print("Method failed with status code " + str(ex.code) + ": " + ex.message)
