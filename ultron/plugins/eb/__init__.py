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
    except KeyError, e:
        print "Key " + e + "not found"

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
    except KeyError, e:
        print "Key " + e + "not found"

    return endpoint

#eb do boto call and retrieve data
def eb_check_versions(profile_name, region_name, chealth, env_array, onlyiflive,slack_channel):

    appversions = []

    mysession = boto3.session.Session(profile_name=profile_name, region_name=region_name)
    client = mysession.client('elasticbeanstalk')
    response = client.describe_environments(
        IncludeDeleted=False,
    )

    for env in response['Environments']:

        c_version = env['VersionLabel']
        c_app = env['ApplicationName']
        c_env = env['EnvironmentName']
        c_solstack = env['SolutionStackName']
        c_health = env['Health']
        date_updated = env['DateUpdated']

        # set app version
        c_appversion = {('app'): c_app, ('version'): c_version, ('environmentname'): c_env,
                        ('solutionstack'): c_solstack, ('health'): c_health, ('dateupdated'):date_updated,
                        ('regionname'): region_name,('slackchannel'):slack_channel}

        for areas in env_array:

            if areas in c_app:
                logging.debug("MATCH: version label is %s app is %s environment is %s\n areas is %s checking app %s\n\n"%(c_version,c_app,c_env, areas,c_app))
            else:
                logging.debug("version label is %s app is %s environment is %s\n areas is %s checking app %s" % (
                c_version, c_app, c_env, areas, c_app))


            current_application_name =  c_app.replace(" ","").lower()
            current_application_keyword = areas.replace(" ","").lower()

            if current_application_keyword in current_application_name:

                # add the corresponding build name tag for each eb environment
                c_appversion.update({('build_master_tag'): env_array[areas]['build_master_tag']})

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
                else:
                    if chealth:
                        if env['Health'] == "Green":
                            appversions.append(c_appversion)
                    else:
                        appversions.append(c_appversion)

    return appversions

#version print out for eb environments
def get_version_output_string(thestring):

    team_dot_index = thestring.find('.')
    team_version_ending = thestring[team_dot_index:]
    version_isolate = team_version_ending.split('.')

    if version_isolate[-2].isdigit():
        e_str = ('.').join(version_isolate[:-1])
    elif version_isolate[-3].isdigit():
        e_str = ('.').join(version_isolate[:-2])
    else:
        e_str = ('.').join(version_isolate[:-1])

    return e_str[1:]

#extract the second part of service name to compare
def get_service_name_ending(thestring):
    slash_index = thestring.find('/')
    thestring = thestring[(slash_index+1):]
    slash_index = thestring.find('-')
    thestring = thestring[(slash_index + 1):]
    return thestring.replace('.json',"")

#Main comparing function
def compare_environment(team_env,master_env, j_tags):

    """""
    Return types
    1 - Matches Master
    2 - Does not match master
    3 - branch
    """""

    result = 0

    if (j_tags[0] in master_env):
        if team_env == master_env:
            result = 1
        else:
            if (j_tags[0] in team_env):
                result = 2
            else:
                result = 3

    #print " MATCH IS: "+team_env +" == " + master_env+" ==> "+str(result)

    logging.debug("comparing %s and %s result is %s"% (team_env,master_env,result))
    return result


def does_key_exist(thearray,thestring):
    if thearray[thestring]:
        return thearray[thestring]
    else:
        return ""

#compress string is larger than 30 length
def shorten_input(thestring):
    if len(thestring) > 30:
        thestring = thestring[:27]+"..."
        return thestring
    else:
        return thestring


#get build url
def format_string_for_comparison(word):
    if "-" in word:
        word = word.replace("-","_")
    if " " in word:
        word = word.replace(" ","_")

    word = word.lower().split("_")

    return word

def build_compare_words(lookup,compareto, j_tags):

    result = False

    compareto = format_string_for_comparison(compareto)
    lookup = format_string_for_comparison(lookup)

    res = list(set(compareto) ^ set(lookup))

    if len(res) == 2 and j_tags[0] in res and j_tags[2] in res:
        result = True
    elif len(res) == 1 and (j_tags[0] in res or j_tags[1] in res):
        result = True

    return result


def get_build_url(cached_array, lookup_word, prelim_version, j_tags, match_num, ismaster):

    the_url = None
    build_detail = None

    for the_names in cached_array:
        if build_compare_words(lookup_word, the_names['name'], j_tags):
            the_url =the_names['url']
            build_detail = the_names['name']

    symbols_array = [".","_","-"]

    build_num = []
    build_detail = shorten_input(build_detail)

    for symb in symbols_array:
        if symb in prelim_version:
            build_num = prelim_version.split(symb)
            break

    if match_num == 2 and ismaster:
        if len(build_num) > 1 and the_url:
            final_url = str(the_url)+build_num[-1]+"/promotion/ | ver: "+str(prelim_version)
            final_url =  "build: "+ build_detail+"\n<"+final_url+ ">"
        else:
            # build url corresponding to service was not found
            final_url = "build: "+ build_detail+"\nver: "+str(prelim_version)
    else:
        final_url = "build: " + build_detail + "\nver: " + str(prelim_version)

    return final_url


def eb_compare_master_team(tkey,m_array, cached_array, jenkins_build_tags):

    compared_array = dict()

    eb_data = []

    for eachmaster in m_array:
        for m_data in m_array[eachmaster]:

            for t_array in tkey:

                logging.debug(t_array['regionname'] +" "+t_array['version'])

                team_dot_index = t_array['version'].find('.')
                team_version_prefix = t_array['version'][:team_dot_index]
                team_version_ending = t_array['version'][team_dot_index:]

                master_dot_index = m_data['version'].find('.')
                master_version_prefix = m_data['version'][0:master_dot_index]
                master_version_ending = m_data['version'][master_dot_index:]


                if team_version_prefix == master_version_prefix:

                    amatch = compare_environment(team_version_ending, master_version_ending, jenkins_build_tags)

                    prelim_master_version = get_version_output_string(m_data['version'])
                    master_version_entry = get_build_url(cached_array, m_data['build_master_tag'],
                                                         prelim_master_version, jenkins_build_tags,
                                                         amatch, ismaster=True)

                    prelim_team_version = get_version_output_string(t_array['version'])
                    team_version_entry = get_build_url(cached_array, t_array['build_master_tag'],
                                                         prelim_team_version, jenkins_build_tags,
                                                         amatch, ismaster=False)


                    eb_data.append({"master_env":m_data['environmentname'],
                             "master_version": master_version_entry,
                             "master_updateddate":m_data['dateupdated'],
                             "team_env":t_array['environmentname'],
                             "team_version": team_version_entry,
                             "team_updateddate":t_array['dateupdated'],
                             "Match":amatch, "mastername": eachmaster,
                             "regionname":t_array['regionname'],
                             "slackchannel": does_key_exist(t_array,'slackchannel'),
                             "pluginname": "eb"
                            })

                    #print " master version entry"


    compared_array.update({'Elastic Beanstalk environment': eb_data})
    return compared_array

#main eb plugin function
def check_versions(master_array, team_array, superjenkins_data, jenkins_build_tags):
    masterdata = dict()

    #master data preparation
    for master_items in master_array:
        for m_items in master_items:
            get_master_data = master_items[m_items]
            #print get_master_data['profile_name'], get_master_data['region_name'],get_master_data['cluster_name'], get_master_data["slack_channel"],get_master_data['environment_code_name']

            master_plugin_data = eb_check_versions(get_master_data['profile_name'], get_master_data['region_name'],
                                                    get_master_data['onlycheckifhealthy'], get_master_data['environments'],
                                                    get_master_data['onlylive'], get_master_data['slack_channel'])

            if master_plugin_data:
                masterdata[m_items] = master_plugin_data

    #team data preparation
    logging.debug(team_array['profile_name'], team_array['region_name'],team_array['cluster_name'], team_array["slack_channel"],team_array['environment_code_name'])

    team_plugin_data = eb_check_versions(team_array['profile_name'], team_array['region_name'],
                                          team_array['onlycheckifhealthy'], team_array['environments'],
                                          team_array['onlylive'], team_array['slack_channel'])




    compared_data = eb_compare_master_team(team_plugin_data, masterdata, superjenkins_data, jenkins_build_tags)

    return compared_data
