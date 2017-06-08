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
def compare_environment(team_env,master_env, eachplugin, b_tags):

    """""
    Return types
    1 - Matches Master
    2 - Does not match master
    3 - branch
    """""

    result = 0

    if eachplugin == "eb":
        if b_tags['1'] in master_env:
            if team_env == master_env:
                result = 1
            else:
                if b_tags['1'] in team_env:
                    result = 2
                else:
                    result = 3

    elif eachplugin == "ecs":
        if b_tags['2'] in master_env or b_tags['3'] in master_env: #or b_tags['9'] in master_env:
            if team_env == master_env:
                result = 1
            else:
                if b_tags['2'] in team_env or b_tags['3'] in team_env:
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

def finalize_service_name(service_name,service_def, environment_code_name, b_tags):

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
        elif b_tags['10'] in initial_def_name_list:
            result.append( (" ").join(initial_def_name_list[:-1]))

    return result


#get build url
def format_string_for_comparison(word):
    if "-" in word:
        word = word.replace("-","_")
    if " " in word:
        word = word.replace(" ","_")

    word = word.lower().split("_")

    return word

def build_compare_words(lookup,compareto, b_tags):

    result = False

    compareto = format_string_for_comparison(compareto)
    lookup = format_string_for_comparison(lookup)

    res = list(set(compareto) ^ set(lookup))

    #print lookup, " == ", compareto

    if len(res) == 2 and b_tags['2'] in res and b_tags['4'] in res:
        #print "\n\n"
        result = True
    elif len(res) == 1 and (b_tags['3'] in res or b_tags['2'] in res):
        #print "\n\n"
        result = True

    return result


def get_build_url(plugin, cached_array, lookup_word, prelim_version, b_tags):

    the_url = None

    for the_names in cached_array:
        if plugin == "eb":
            if build_compare_words(lookup_word, the_names['name'], b_tags):
                the_url =the_names['url']
        elif plugin == "ecs":
            if build_compare_words(lookup_word, the_names['name'], b_tags):
                the_url = the_names['url']


    symbols_array = [".","_","-"]

    build_num = []

    for symb in symbols_array:
        if symb in prelim_version:
            build_num = prelim_version.split(symb)
            break

    final_url = str(the_url)+build_num[-1]+"/"+b_tags['11']+"/"+" | ver: "+str(prelim_version)
    final_url =  "<"+final_url+ ">"
    #print "final url "+final_url
    return final_url



#main comparison function
def compare_teams(t_array,m_array, cached_array, b_tags):

    pprint.pprint(t_array)

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

                                amatch = compare_environment(team_version_ending, master_version_ending, eachteamplugin, b_tags)

                                #if the match is of type 2 where environment/service is not matching prod master
                                #   and not a dev branch get the build


                                if amatch != 5:
                                    prelim_master_version = get_version_output_string(m_data['version'])
                                    master_version_entry = get_build_url("eb",cached_array, m_data['build_master_tag'],
                                                                       prelim_master_version, b_tags )
                                else:
                                    master_version_entry = get_version_output_string(tkey['version'])


                                #formatting versions
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

                            if tkey['servicename'] == m_data['servicename']:

                                logging.debug("Printing comparison of service_definition")
                                logging.debug(tkey['service_definition'] + " == " + m_data['service_definition'])

                                the_team_service_name = finalize_service_name(tkey['servicename'],
                                                                              tkey['service_definition'],
                                                                              tkey['environment_code_name'],
                                                                              b_tags)

                                the_master_service_name = finalize_service_name(m_data['servicename'],
                                                                                m_data['service_definition'],
                                                                                m_data['environment_code_name'],
                                                                                b_tags)

                                logging.debug( the_team_service_name[0] + " == " + the_master_service_name[0] + "\n\n")

                                if the_team_service_name[0] == the_master_service_name[0]:

                                    amatch = compare_environment(tkey['version'], m_data['version'], eachteamplugin, b_tags)
                                    logging.debug( tkey['version']+ " === " +m_data['version']+"\n" )


                                    # if the match is of type 2 where environment/service is not matching prod master
                                    #   and not a dev branch get the build
                                    if amatch != 5:
                                        print "the_master_service_name_lookup "+the_master_service_name[0]
                                        if len(the_master_service_name) == 2:
                                            ecs_master_version_entry = get_build_url("ecs", cached_array,the_master_service_name[1],
                                                                                   m_data['version'], b_tags)
                                        elif len(the_master_service_name) == 1:
                                            ecs_master_version_entry = get_build_url("ecs", cached_array,
                                                                                     the_master_service_name[0],
                                                                                     m_data['version'], b_tags)
                                    else:
                                        ecs_master_version_entry = m_data['version']

                                    if amatch == 0:
                                        print "match is zero ",tkey['servicename']," task_def: ",tkey['service_definition'], " => ", the_team_service_name


                                    ecs_data.append({"master_env": the_master_service_name[0],
                                             "master_version": ecs_master_version_entry,
                                             "master_updateddate":"",
                                             "team_env": the_team_service_name[0],
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

    pprint.pprint(compared_array)

    return compared_array

