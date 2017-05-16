import pprint
import logging

def id():
    return "compare"

def log(message):
    print id() + ": " + message

def compare_environment(team_env,master_env):

    """""
    Return types
    1 - Matches Master
    2 - Does not match master
    3 - branch
    """""

    if ".master." in master_env:
        if team_env == master_env:
            result = 1
        else:
            if ".master." in team_env:
                result = 2
            else:
                result = 3

    logging.debug("comparing %s and %s result is %s"% (team_env,master_env,result))
    return result

def compare_teams(t_array,m_array):

    compared_array = []

    for amaster in m_array:
        for mkey in m_array[amaster]:
            for master_info in m_array[amaster][mkey]:

                    for tkey in t_array:
                            team_dot_index = tkey['version'].find('.')
                            team_version_prefix = tkey['version'][:team_dot_index]
                            team_version_ending = tkey['version'][team_dot_index:]

                            master_dot_index = master_info['version'].find('.')
                            master_version_prefix = master_info['version'][0:master_dot_index]
                            master_version_ending = master_info['version'][master_dot_index:]

                            if team_version_prefix == master_version_prefix:

                                amatch = compare_environment(team_version_ending, master_version_ending)

                                compared_array.append( {"master_env":master_info['environmentname'],
                                                         "master_version":master_info['version'],
                                                         "master_updateddate":master_info['dateupdated'],
                                                         "team_env":tkey['environmentname'],
                                                         "team_version":tkey['version'],
                                                         "team_updateddate":tkey['dateupdated'],
                                                         "Match":amatch, "mastername":mkey,
                                                         "regionname":tkey['regionname']})
    return compared_array

