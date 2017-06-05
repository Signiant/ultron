import pprint
import logging

def id():
    return "compare"

def log(message):
    print id() + ": " + message

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
def compare_environment(team_env,master_env, eachplugin):

    """""
    Return types
    1 - Matches Master
    2 - Does not match master
    3 - branch
    """""

    result = 0

    if eachplugin == "eb":
        if ".master." in master_env:
            if team_env == master_env:
                result = 1
            else:
                if ".master." in team_env:
                    result = 2
                else:
                    result = 3

    elif eachplugin == "ecs":
        if "master" in master_env or "trunk" in master_env:
            if team_env == master_env:
                result = 1
            else:
                if "master" in team_env or "trunk" in team_env:
                    result = 2
                else:
                    result = 3

    logging.debug("comparing %s and %s result is %s"% (team_env,master_env,result))
    return result


def does_key_exist(thearray,thestring):
    if thearray[thestring]:
        return thearray[thestring]
    else:
        return ""

def finalize_service_name(service_name,service_def):

    def_name_mod = service_def.lower().replace("-","+").replace("_", "+")
    service_name_mod = service_name.lower().replace("-","+").replace("_", "+")

    def_name_list = def_name_mod.split("+")
    service_name_list = service_name_mod.split("+")

    for sname in service_name_list:
        if sname in def_name_list:
            def_name_list.remove(sname)

    if len(def_name_list) > 3:
        result = def_name_list[-3]+service_name
    else:
        result = service_name

    return result


def compare_teams(t_array,m_array):

    compared_array = {}
    eb_data = []
    ecs_data = []

    for eachmaster in m_array:
        for eachmasterplugin in m_array[eachmaster]:
            for m_data in m_array[eachmaster][eachmasterplugin]:

                for eachteamplugin in t_array:

                    if eachmasterplugin == "eb" and eachteamplugin == "eb":
                        for tkey in t_array[eachteamplugin]:
                            logging.debug(tkey['regionname'] +" "+tkey['version'])

                            team_dot_index = tkey['version'].find('.')
                            team_version_prefix = tkey['version'][:team_dot_index]
                            team_version_ending = tkey['version'][team_dot_index:]

                            master_dot_index = m_data['version'].find('.')
                            master_version_prefix = m_data['version'][0:master_dot_index]
                            master_version_ending = m_data['version'][master_dot_index:]


                            if team_version_prefix == master_version_prefix:

                                amatch = compare_environment(team_version_ending, master_version_ending, eachteamplugin)

                                #formatting versions
                                master_version_entry = get_version_output_string(m_data['version'])
                                team_version_entry = get_version_output_string(tkey['version'])


                                eb_data.append({"master_env":m_data['environmentname'],
                                         "master_version": master_version_entry,
                                         "master_updateddate":m_data['dateupdated'],
                                         "team_env":tkey['environmentname'],
                                         "team_version": team_version_entry,
                                         "team_updateddate":tkey['dateupdated'],
                                         "Match":amatch, "mastername": eachmaster,
                                         "regionname":tkey['regionname'],
                                         "slackchannel": does_key_exist(tkey,'slackchannel'),
                                         "pluginname": eachteamplugin
                                        })

                    elif eachmasterplugin == "ecs" and eachteamplugin == "ecs":
                        for tkey in t_array[eachteamplugin]:

                            team_service_definition = tkey['service_definition']
                            master_service_definition = m_data['service_definition']

                            if tkey['servicename'] == m_data['servicename']:

                                logging.debug("Printing comparison of service_definition")
                                logging.debug(tkey['service_definition'] + " == " + m_data['service_definition'])

                                the_team_service_name = finalize_service_name(tkey['servicename'],
                                                                              tkey['service_definition'])
                                the_master_service_name = finalize_service_name(m_data['servicename'],
                                                                                m_data['service_definition'])

                                logging.debug( the_team_service_name + " == " + the_master_service_name + "\n\n")

                                if the_team_service_name == the_master_service_name:

                                    amatch = compare_environment(tkey['version'], m_data['version'], eachteamplugin)
                                    logging.debug( tkey['version']+ " === " +m_data['version']+"\n" )

                                    ecs_data.append({"master_env": the_master_service_name,
                                             "master_version": m_data['version'],
                                             "master_updateddate":"",
                                             "team_env": the_team_service_name,
                                             "team_version": tkey['version'],
                                             "team_updateddate":"",
                                             "Match":amatch, "mastername": eachmaster,
                                             "regionname":tkey['regionname'],
                                             "slackchannel": does_key_exist(tkey,'slackchannel'),
                                             "pluginname": eachteamplugin
                                            })

    #adding to compared_array
    if eb_data:
        compared_array.update({'Beanstalk environments': eb_data})
    if ecs_data:
        compared_array.update({'ECS services':ecs_data})


    #pprint.pprint(compared_array)

    return compared_array

