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

                version_output = image['taskDefinition']['containerDefinitions'][0]['image']
                version_parsed = version_output.replace("signiant/", "")

                team_service = image['taskDefinition']['containerDefinitions'][0]['environment']

                for envs in team_service:
                    if envs['name'] == 'CONFIG_FILE':
                        team_service_name = envs['value']

                # version_parsed, team_service_name, region_name
                if len(team_service_name) > 1:
                    c_service = {"version":version_parsed,
                                 "servicename":team_service_name,
                                 "regionname":region_name,
                                 "slackchannel":slack_channel}

                    service_versions.append(c_service)

    except Exception, e:
        print("Error obtaining paginated services for " + cluster_name + " (" + str(e) + ")")

    return service_versions


