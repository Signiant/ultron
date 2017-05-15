import boto3,json,imp,pprint
from botocore.exceptions import ClientError
import logging

appversions = []

def log (message):
    print id() + ": " + message

def id():
    return "eb"

def get_env_elb(envname,region, current_session):
    client = current_session.client('elasticbeanstalk')
    response = ""
    elb_name = ""

    try:
        response = client.describe_environment_resources(
            EnvironmentName=envname
        )
    except Exception, e:
        log("Error describing the EB environment resources for " + envname + " (" + str(e) + ")")

    if response:
        # Eb only uses a single load balancer so grab the first
        elb_name = response['EnvironmentResources']['LoadBalancers'][0]['Name']

    return elb_name

def is_current_eb_env_live(env_lb,switchable_dns_entry,zoneid,region, current_session):
    isLive = False
    current_live_elb = get_r53_alias_entry(switchable_dns_entry, zoneid, current_session).rstrip('.').lower()

    if current_live_elb.startswith(env_lb.lower()):
        isLive = True

    return isLive

#
# Get the route53 Alias entry for a given name
#
def get_r53_alias_entry(query_name,zoneid, current_session):

    try:
        endpoint = ""

        client = current_session.client('route53')
        response = client.list_resource_record_sets(
            HostedZoneId=zoneid,
            StartRecordName=query_name,
            StartRecordType='A',
            MaxItems='1'
        )
        if response:
            endpoint = response['ResourceRecordSets'][0]['AliasTarget']['DNSName']
    except Exception, e:
        print str(e)

    return endpoint

def check_versions(profile_name, region_name, chealth, env_array, onlyiflive):

    mysession = boto3.session.Session(profile_name=profile_name, region_name=region_name)
    client = mysession.client('elasticbeanstalk')
    response = client.describe_environments(
        IncludeDeleted=False,
    )

    #logging.debug(pprint.pprint(response))
    for env in response['Environments']:

        c_version = env['VersionLabel']
        c_app = env['ApplicationName']
        c_env = env['EnvironmentName']
        c_solstack = env['SolutionStackName']
        c_health = env['Health']
        date_updated = env['DateUpdated']

        # set app version
        c_appversion = {('app'): c_app, ('version'): c_version, ('environmentname'): c_env,
                        ('solutionstack'): c_solstack, ('health'): c_health, ('dateupdated'):date_updated}

        for areas in env_array:
            if areas in c_app:
                if onlyiflive:
                    current_dns_name = env_array[areas]['dns_name']
                    current_zone_id = env_array[areas]['zone_id']

                    if current_dns_name != "" and current_zone_id != "":

                        env_lb = get_env_elb(c_env, region_name, mysession)
                        checklive = is_current_eb_env_live(env_lb, current_dns_name, current_zone_id, region_name,mysession)

                    else:
                        checklive = False

                    if checklive:
                        if chealth:
                            if env['Health'] == "Green":
                                appversions.append(c_appversion)
                        else:
                            appversions.append(c_appversion)
                #if check is false
                else:
                    if chealth:
                        if env['Health'] == "Green":
                            appversions.append(c_appversion)
                    else:
                        appversions.append(c_appversion)

        # print("Application = "+current_app+"// Environment = "+current_env+"// Version = "+current_version+"// last updated = "+str(env['DateUpdated']))

    return appversions




