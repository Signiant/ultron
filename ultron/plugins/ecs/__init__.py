import boto3
import json
import pprint

def log (message):
    print id() + ": " + message

def id():
    return "ecs"

def ecs_check_versions(profile_name, region_name, cluster_name,slack_channel):

    service_versions = []
    team_service_name = ""

    try:
        mysession = boto3.session.Session(profile_name=profile_name, region_name=region_name)
        client = mysession.client('ecs')
        service_paginator = client.get_paginator('list_services')
        service_iterator = service_paginator.paginate(cluster=cluster_name)
    except Exception, e:
        print("Error obtaining list of ECS services for " + cluster_name + " (" + str(e) + ")")
    except KeyError, e:
        print "Key " + e + "not found"

    try:
        for service in service_iterator:
            # Get the service info for each batch
            services_descriptions = client.describe_services(cluster=cluster_name, services=service['serviceArns'])
            for service_desc in services_descriptions['services']:
                image = client.describe_task_definition(taskDefinition=service_desc['taskDefinition'])

                #getting ecs service version and name
                version_output = image['taskDefinition']['containerDefinitions'][0]['image']
                version_parsed = version_output.replace("signiant/", "")
                service_dot_index = version_parsed.find(':')

                service_version_prefix = version_parsed[0:service_dot_index]
                service_version_ending = version_parsed[(service_dot_index + 1):]

                #detailed ecs service
                team_service_definition = image['taskDefinition']['family']

                # version_parsed, team_service_name, region_name
                if len(version_output) > 1:
                    c_service = {"version":service_version_ending,
                                 "servicename": service_version_prefix,
                                 "service_definition": team_service_definition,
                                 "regionname":region_name,
                                 "slackchannel":slack_channel}

                    service_versions.append(c_service)

    except Exception, e:
        print("Error obtaining paginated services for " + cluster_name + " (" + str(e) + ")")

    return service_versions


