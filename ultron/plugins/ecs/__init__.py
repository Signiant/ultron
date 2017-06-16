import boto3
import json
import pprint
import logging

def log (message):
    print id() + ": " + message

def id():
    return "ecs"

#get ecs data from boto call
def ecs_check_versions(profile_name, region_name, cluster_name,slack_channel,env_code_name):

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
                version_parsed = version_output.split("/")[-1]
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
                                 "slackchannel":slack_channel,
                                 "environment_code_name":env_code_name}

                    service_versions.append(c_service)

    except Exception, e:
        print("Error obtaining paginated services for " + cluster_name + " (" + str(e) + ")")

    return service_versions


#Main comparing function
def compare_environment(team_env,master_env, j_tags):

    """""
    Return types
    1 - Matches Master
    2 - Does not match master
    3 - branch
    """""

    result = 0

    if j_tags[0] in master_env or j_tags[1] in master_env:
        if team_env == master_env:
            result = 1
        else:
            if j_tags[0] in master_env or j_tags[1] in master_env:
                result = 2
            else:
                result = 3

    #print " MATCH IS: "+team_env +" == " + master_env+" ==> "+str(result)
    logging.debug("comparing %s and %s result is %s"% (team_env,master_env,result))
    return result


def finalize_service_name(service_name,service_def, environment_code_name):

    result = []

    def_name_mod = service_def.lower().replace("-","+").replace("_", "+")
    service_name_mod = service_name.lower().replace("-","+").replace("_", "+")

    def_name_list = def_name_mod.split("+")
    service_name_list = service_name_mod.split("+")

    initial_def_name_list = def_name_list

    for sname in service_name_list:
        if sname in def_name_list:
            def_name_list.remove(sname)

    if environment_code_name:
        if environment_code_name in def_name_list:
            def_name_list.remove(environment_code_name)
            if len(def_name_list) > 2:
                result.append( def_name_list[0] + "_" + service_name)
                result.append(service_name)
            else:
                result.append(service_name)

    return result


#get build url
def format_string_for_comparison(word):
    if "-" in word:
        word = word.replace("-","_")
    if " " in word:
        word = word.replace(" ","_")

    word = word.lower().split("_")

    return "_".join(word)

def build_compare_words(lookup,compareto, j_tags):

    result = False

    if compareto:
        if "-" in compareto:
            compareto = compareto.replace("-", "_")
        if " " in compareto:
            compareto = compareto.replace(" ", "_")
        compareto = compareto.lower().split("_")
    else:
        compareto = []

    if lookup:
        if "-" in lookup:
            lookup = lookup.replace("-", "_")
        if " " in lookup:
            lookup = lookup.replace(" ", "_")
        lookup = lookup.lower().split("_")
    else:
        lookup = []

    #compareto = format_string_for_comparison(compareto)
    #lookup = format_string_for_comparison(lookup)

    res = list(set(compareto) ^ set(lookup))

    if len(res) == 2 and j_tags[0] in res and j_tags[2] in res:
        result = True
    elif len(res) == 1 and (j_tags[0] in res or j_tags[1] in res):
        result = True

    return result


def get_build_url(cached_array, lookup_word, prelim_version, j_tags):

    the_url = None

    for the_names in cached_array:
        if build_compare_words(lookup_word, the_names['name'], j_tags):
            the_url = the_names['url']


    symbols_array = [".","_","-"]

    build_num = []

    for symb in symbols_array:
        if symb in prelim_version:
            build_num = prelim_version.split(symb)
            break

    if len(build_num) > 1 and the_url:
        final_url = str(the_url)+build_num[-1]+"/promotion/ | ver: "+str(prelim_version)
        final_url =  "<"+final_url+ ">"
    else:
        # build url corresponding to service was not found
        final_url = "ver: "+str(prelim_version)

    return final_url

#compare master to teams
def ecs_compare_master_team(tkey,m_array, cached_array, jenkins_build_tags, excluded_services=None):

    compared_array = {}
    ecs_data = []

    for eachmaster in m_array:
        for m_data in m_array[eachmaster]:

            for t_array in tkey:

                #format service names to be lower case and words seperated by underscores
                t_array['servicename'] = format_string_for_comparison(t_array['servicename'])

                m_data['servicename'] = format_string_for_comparison(m_data['servicename'])


                if t_array['servicename'] == m_data['servicename']:

                    logging.debug("Printing comparison of service_definition")
                    logging.debug(t_array['service_definition'] + " == " + m_data['service_definition'])

                    #check if service_name is on excluded services list
                    do_not_exclude_service = True
                    for ex_service in excluded_services:
                        if ex_service in t_array['servicename']:
                            do_not_exclude_service = False


                    if do_not_exclude_service:


                        the_team_service_name = finalize_service_name(t_array['servicename'],
                                                                      t_array['service_definition'],
                                                                      t_array['environment_code_name'])

                        the_master_service_name = finalize_service_name(m_data['servicename'],
                                                                        m_data['service_definition'],
                                                                        m_data['environment_code_name'])



                        if  the_team_service_name and the_master_service_name:
                            if the_team_service_name[0] == the_master_service_name[0]:

                                amatch = compare_environment(t_array['version'], m_data['version'], jenkins_build_tags)
                                #logging.debug(t_array['version'] + " === " + m_data['version'] + "\n")

                                # if the match is of type 2 where environment/service is not matching prod master
                                #   and not a dev branch get the build

                                if amatch == 2:

                                    if len(the_master_service_name) == 2:
                                        ecs_master_version_entry = get_build_url(cached_array,
                                                                                 the_master_service_name[1],
                                                                                 m_data['version'], jenkins_build_tags)
                                    elif len(the_master_service_name) == 1:
                                        ecs_master_version_entry = get_build_url(cached_array,
                                                                                 the_master_service_name[0],
                                                                                 m_data['version'], jenkins_build_tags)
                                else:
                                    ecs_master_version_entry = "ver: "+m_data['version']

                                ecs_team_version_entry = "ver: "+t_array['version']

                                if amatch == 0:
                                    print "match is zero ", t_array['servicename'], " task_def: ", t_array[
                                        'service_definition'], " => ", the_team_service_name

                                #see if a slackchannel is available for team
                                if t_array.has_key('slackchannel') == False:
                                    t_array['slackchannel'] = ""

                                ecs_data.append({"master_env": the_master_service_name[0],
                                                 "master_version": ecs_master_version_entry,
                                                 "master_updateddate": "",
                                                 "team_env": the_team_service_name[0],
                                                 "team_version": ecs_team_version_entry,
                                                 "team_updateddate": "",
                                                 "Match": amatch, "mastername": eachmaster,
                                                 "regionname": t_array['regionname'],
                                                 "slackchannel": t_array['slackchannel'],
                                                 "pluginname": "ecs"
                                                 })

    compared_array.update({'ecs service': ecs_data})
    return compared_array


#main ecs plugin function
def check_versions(master_array, team_array, superjenkins_data, jenkins_build_tags):

    masterdata = dict()
    teamdata = dict()

    for master_items in master_array:
        get_master_data = master_array[master_items]
        master_plugin_data = ecs_check_versions(get_master_data['profile_name'], get_master_data['region_name'],
                                                get_master_data['cluster_name'], get_master_data["slack_channel"],
                                                get_master_data['environment_code_name'])

        if master_plugin_data:
            masterdata[master_items] = master_plugin_data

    for team_items in team_array:
        get_team_data = team_array[team_items]
        team_plugin_data = ecs_check_versions(get_team_data['profile_name'], get_team_data['region_name'],
                                              get_team_data['cluster_name'], get_team_data["slack_channel"],
                                              get_team_data['environment_code_name'])

        compared_data = ecs_compare_master_team(team_plugin_data,
                                                masterdata,
                                                superjenkins_data,
                                                jenkins_build_tags,
                                                get_team_data['service_exclude_list'])

        teamdata[team_items] = compared_data

    return teamdata

