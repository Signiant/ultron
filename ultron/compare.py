import pprint

def id():
    return "compare"

def log(message):
    print id() + ": " + message


def score_teams(the_array,the_env):

    for env in the_env:
        for elements in env:

            for team_list in the_array:
                for team in the_array[team_list]:

                    if env["team"] == team:
                        for environments in env["environments"]:
                            for team_environments in the_array[team_list][team]:

                                if env["environments"][environments]["name"] in team_environments['environmentname']:
                                    team_environments["environment_mapping"] = environments

                            if "environment_mapping" not in team_environments:
                                team_environments["environment_mapping"] = "-1"

    return the_array

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

def compare_teams(team_array,master_array,team_env):

    compared_array = []

    t_array = score_teams(team_array,team_env)
    m_array = score_teams(master_array,team_env)

    for amaster in m_array:
        for mkey in m_array[amaster]:
            for master_info in m_array[amaster][mkey]:

                for ateam in t_array:
                    for tkey in t_array[ateam]:
                        for team_info in t_array[ateam][tkey]:

                            if team_info['environment_mapping'] == master_info['environment_mapping'] \
                                    and master_info['environment_mapping'] != "-1" \
                                    and team_info['environment_mapping'] != "-1":

                                amatch = compare_environment(team_info['version'], master_info['version'])

                                compared_array.append( {"master_env":master_info['environmentname'],
                                                         "master_version":master_info['version'],
                                                         "master_updateddate":master_info['dateupdated'],
                                                         "team_env":team_info['environmentname'],
                                                         "team_version":team_info['version'],
                                                         "team_updateddate":team_info['dateupdated'],
                                                         "Match":amatch, "team":tkey})

    return compared_array

