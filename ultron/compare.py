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

                            print(team_info)



                        if t_array[ateam][tkey]['environment_mapping'] == m_array[amaster][mkey]['environment_mapping'] \
                                and m_array[amaster][mkey]['environment_mapping'] != "-1" \
                                and t_array[ateam][tkey]['environment_mapping'] != "-1":

                            amatch = compare_environment(t_array[ateam][tkey]['version'], m_array[amaster][mkey]['version'])

                            compared_array.append(  {"master_env":m_array[amaster][mkey]['environmentname'],
                                                     "master_version":m_array[amaster][mkey]['version'],
                                                     "master_updateddate":m_array[amaster][mkey]['dateupdated'],
                                                     "team_env":t_array[ateam][tkey]['environmentname'],
                                                     "team_version":t_array[ateam][tkey]['version'],
                                                     "team_updateddate":t_array[ateam][tkey]['dateupdated'],
                                                     "Match":amatch, "team":t_array[ateam][tkey]['team']} )
    return compared_array
