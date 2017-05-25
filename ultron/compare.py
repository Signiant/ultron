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
        if team_env == master_env:
            result = 1
        else:
            result = 2

    logging.debug("comparing %s and %s result is %s"% (team_env,master_env,result))
    return result


def does_key_exist(thearray,thestring):
    if thearray[thestring]:
        return thearray[thestring]
    else:
        return ""


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

                            logging.debug( "original team " + get_service_name_ending(tkey["servicename"]) \
                                                   + "----------- original master " + get_service_name_ending(m_data["servicename"]))
                            if get_service_name_ending(tkey["servicename"]) == get_service_name_ending(m_data["servicename"]):
                                logging.debug( "matched")
                                tkey_edited = tkey['version'].replace("signiant/","")
                                team_dot_index = tkey_edited.find(':')
                                team_version_prefix = tkey_edited[:team_dot_index]
                                team_version_ending = tkey_edited[(team_dot_index+1):]

                                master_dot_index = m_data['version'].find(':')
                                master_version_prefix = m_data['version'][0:master_dot_index]
                                master_version_ending = m_data['version'][(master_dot_index+1):]

                                logging.debug(team_version_prefix +" == "+ master_version_prefix)

                                if team_version_prefix == master_version_prefix:

                                    amatch = compare_environment(team_version_ending, master_version_ending, eachteamplugin)
                                    logging.debug( team_version_ending+ " === " +master_version_ending+"\n" )

                                    ecs_data.append({"master_env": get_service_name_ending(m_data["servicename"]),
                                             "master_version": m_data['version'].replace("signiant/",""),
                                             "master_updateddate":"",
                                             "team_env": get_service_name_ending(tkey["servicename"]),
                                             "team_version": tkey['version'].replace("signiant/",""),
                                             "team_updateddate":"",
                                             "Match":amatch, "mastername": eachmaster,
                                             "regionname":tkey['regionname'],
                                             "slackchannel": does_key_exist(tkey,'slackchannel'),
                                             "pluginname": eachteamplugin
                                            })

    #adding to compared_array
    if eb_data:
        compared_array.update({'eb': eb_data})
    if ecs_data:
        compared_array.update({'ecs':ecs_data})

    #pprint.pprint(compared_array)

    return compared_array

