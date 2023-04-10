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


def slClient():
    client = SoftLayer.create_client_from_env(
        username='apikey',
        api_key=os.environ.get('IBMCLOUD_API_KEY')
    )
    return client

def getServiceInstances():
    client = searchService()
    classicClient = slClient()
    tagQuery = '(family:ims) AND (tags:"project:rolling-iaas")'
    result = client.search(
        query=tagQuery,
        fields=["*"]
    ).get_result()
    resources = result['items']
    
    instances_to_update = []
    for resource in resources:
        # Check if the instance has an open cancellation ticket
        instance_id = resource['resource_id']
        open_ticket_id = getOpenTicket(instance_id)
        if open_ticket_id is not None:
            instances_to_update.append(resource)
    
    return instances_to_update


## failing if the instance does not have an open cancellation ticket. In this case we have 1 machine that does not have an open cancellation ## ticket

def getInstanceIds():
    client = slClient()
    svcs = getServiceInstances()
    for svc in svcs:
        openTicketId = client['Hardware_Server'].getOpenCancellationTicket(id=svc)
        getTicketUpdates = client['Ticket'].getUpdates(id=openTicketId)
        print(getTicketUpdates)

# def getOpenTicket(instanceId):
#     client = slClient()
#     openTicketId = client['Hardware_Server'].getOpenCancellationTicket(id=instanceId)
#     ticketId = openTicketId['id']
#     return str(ticketId) if ticketId else print()

def getOpenTicket(instanceId):
    client = slClient()
    tickets = client['Hardware_Server'].getActiveTickets(filter={
        'hardwareId': {'operation': instanceId},
        'status': {'operation': 'open'},
        'title': {'operation': 'Cancellation Request'}
    })
    if tickets:
        return tickets[0]['id']
    else:
        return None

try:
    instances = getServiceInstances()
    # for instance in instances:
    #     print(instance['resource_id'])
except ApiException as ex:
    print("Method failed with status code " + str(ex.code) + ": " + ex.message)
