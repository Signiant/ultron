import pprint

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
            return "Matches Master"
        else:
            if ".master." in team_env:
                return "Does not match master"
            else:
                return "Branch repo"

def compare_teams(t_array,m_array):

    compared_array = []

    for amaster in m_array:
        for mkey in m_array[amaster]:
            for master_info in m_array[amaster][mkey]:

                for ateam in t_array:
                    for tkey in t_array[ateam]:
                        for team_info in t_array[ateam][tkey]:

                            team_dot_index = team_info['version'].find('.')
                            team_version_prefix = team_info['version'][:team_dot_index]
                            team_version_ending = team_info['version'][team_dot_index:]

                            master_dot_index = master_info['version'].find('.')
                            master_version_prefix = master_info['version'][0:master_dot_index]
                            master_version_ending = master_info['version'][master_dot_index:]

                            if team_version_prefix == master_version_prefix:

                                amatch = compare_environment(team_version_ending, master_version_ending)

                                compared_array.append( {"master_env":master_info['environmentname'],
                                                         "master_version":master_info['version'],
                                                         "master_updateddate":master_info['dateupdated'],
                                                         "team_env":team_info['environmentname'],
                                                         "team_version":team_info['version'],
                                                         "team_updateddate":team_info['dateupdated'],
                                                         "Match":amatch, "team":tkey})

    return compared_array

