import pprint
import logging

def id():
    return "compare"

def log(message):
    print id() + ": " + message

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

def compare_teams(t_array,m_array, eachplugin):

    compared_array = []

    for amaster in m_array:
        for mkey in m_array[amaster]:

            if eachplugin == "eb":
                for master_info in m_array[amaster][mkey]:
                        for tkey in t_array:

                                team_dot_index = tkey['version'].find('.')
                                team_version_prefix = tkey['version'][:team_dot_index]
                                team_version_ending = tkey['version'][team_dot_index:]

                                master_dot_index = master_info['version'].find('.')
                                master_version_prefix = master_info['version'][0:master_dot_index]
                                master_version_ending = master_info['version'][master_dot_index:]

                                if team_version_prefix == master_version_prefix:

                                    amatch = compare_environment(team_version_ending, master_version_ending, eachplugin)

                                    #formatting versions
                                    master_version_entry = get_version_output_string(master_info['version'])
                                    team_version_entry = get_version_output_string(tkey['version'])

                                    compared_array.append( {"master_env":master_info['environmentname'],
                                                             "master_version": master_version_entry,
                                                             "master_updateddate":master_info['dateupdated'],
                                                             "team_env":tkey['environmentname'],
                                                             "team_version": team_version_entry,
                                                             "team_updateddate":tkey['dateupdated'],
                                                             "Match":amatch, "mastername": amaster,
                                                             "regionname":tkey['regionname']})

            elif eachplugin == "ecs":
                for master_info in m_array[amaster][mkey]:
                    for tkey in t_array:
                            team_dot_index = tkey['version'].find(':')
                            team_version_prefix = tkey['version'][:team_dot_index]
                            team_version_ending = tkey['version'][team_dot_index:]

                            master_dot_index = master_info['version'].find(':')
                            master_version_prefix = master_info['version'][0:master_dot_index]
                            master_version_ending = master_info['version'][master_dot_index:]

                            if team_version_prefix == master_version_prefix:

                                amatch = compare_environment(team_version_ending, master_version_ending, eachplugin)

                                compared_array.append( {"master_env":master_version_prefix,
                                                         "master_version":master_version_ending,
                                                         "master_updateddate":"",
                                                         "team_env": team_version_prefix,
                                                         "team_version": team_version_ending,
                                                         "team_updateddate":"",
                                                         "Match":amatch, "mastername": amaster,
                                                         "regionname":tkey['regionname']})


    #pprint.pprint(compared_array)

    return compared_array

