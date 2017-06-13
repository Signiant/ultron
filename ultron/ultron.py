import json
import os, sys
import imp, argparse
import logging
import requests
import pprint

#project modules
import plugin
import output


def read_config_file(path):
    config_map = []

    try:
        config_file_handle = open(path)
        config_map = json.load(config_file_handle)
        config_file_handle.close()
    except Exception as e:
        print "unable to load file" + str(e)

    return config_map

def does_key_exist(thearray,thestring):
    if thearray[thestring]:
        return thearray[thestring]
    else:
        return ""

#retrieve json data from super jenkins for build urls
def get_superjenkins_data(superjenkins_link,beginning_script_tag,ending_script_tag):

    # get json to get individual services/application build links
    cached_items = ""
    cached_array = ""

    try:
        returned_data = requests.get(superjenkins_link)
        returned_data_iterator = returned_data.iter_lines()

        for items in returned_data_iterator:
            if beginning_script_tag in items:
                cached_items = items.replace(beginning_script_tag, "").replace(ending_script_tag, "")
                break

        for items in json.loads(cached_items):
            cached_array = json.loads(cached_items)[items]

    except Exception, e:
        print "Error in retrieving and creating json for build urls ==> " + str(e)

    return cached_array


#main
def main(argv):

    masterdata = {}
    teamdata = {}

    log_level = logging.INFO

    # Add our folder to the system path
    sys.path.append(os.path.abspath(os.path.join(os.path.dirname(__file__), '..')))

    parser = argparse.ArgumentParser(description='Check versions')
    parser.add_argument('-d','--debug', help='Enable debug output',action='store_true')
    parser.add_argument('-c','--config', help='Full path to a config file',required=True)
    args = parser.parse_args()

    if args.debug:
        print("verbose selected - Debug logging turned on")
        log_level = logging.DEBUG

    logger = logging.getLogger()
    logger.setLevel(logging.DEBUG)
    # create file handler which logs even debug messages
    fh = logging.FileHandler('prerequisite-checker.log')
    fh.setLevel(logging.DEBUG)
    # create console handler using level set in log_level
    ch = logging.StreamHandler()
    ch.setLevel(log_level)
    console_formatter = logging.Formatter('%(levelname)8s: %(message)s')
    ch.setFormatter(console_formatter)
    file_formatter = logging.Formatter('%(asctime)s - %(levelname)8s: %(message)s')
    fh.setFormatter(file_formatter)
    # Add the handlers to the logger
    logger.addHandler(fh)
    logger.addHandler(ch)

    config_map = read_config_file(args.config)

    if config_map:
        team_list = config_map["Teams"]

        #get superjenkins data
        superjenkins_data = get_superjenkins_data(config_map["General"]["build_link"],
                                 config_map["General"]["script_tags"]["beginning_tag"],
                                 config_map["General"]["script_tags"]["ending_tag"])

        if superjenkins_data:

            master_array = dict()
            team_array = dict()

            for team in team_list:
                plugins_list = team_list[team]["plugins"]
                for aplugin in plugins_list:
                    plugin_name = aplugin["pluginname"]

                    # agregate desginated master team data for plugin

                    for m_team in team_list:
                        if team_list[m_team]["master"]:
                            m_plugins_list = team_list[m_team]["plugins"]
                            for m_aplugin in m_plugins_list:
                                m_plugin_name = m_aplugin["pluginname"]
                                if master_array.has_key(m_plugin_name):
                                    master_array[m_plugin_name].update({m_team: m_aplugin})
                                else:
                                    master_array[m_plugin_name] = ({m_team: m_aplugin})
                        else:
                            tm_plugins_list = team_list[m_team]["plugins"]
                            for tm_aplugin in tm_plugins_list:
                                tm_plugin_name = tm_aplugin["pluginname"]
                                if team_array.has_key(tm_plugin_name):
                                    team_array[tm_plugin_name].update({m_team: tm_aplugin})
                                else:
                                    team_array[tm_plugin_name] = ({m_team: tm_aplugin})


            #contains team plugin data before output
            all_team_data = dict()

            for tdata in team_array:
                for mdata in master_array:
                    if tdata == mdata:
                        # Load the plugin from the plugins folder
                        plugin_handle = plugin.loadPlugin(tdata)

                        plugin_data = plugin_handle.check_versions(master_array[mdata],
                                                                   team_array[tdata],
                                                                   superjenkins_data,
                                                                   config_map["General"]["jenkins"]["branch_equivalent_tags"])


                        if plugin_data:
                            for plugin_team in plugin_data:
                                #all_plugin_temp.append(plugin_data)
                                if all_team_data.has_key(plugin_team):
                                    all_team_data[plugin_team].update(plugin_data[plugin_team])
                                else:
                                    all_team_data[plugin_team] = (plugin_data[plugin_team])

            for indteam in all_team_data:
                output.output_slack_payload(all_team_data[indteam], config_map["General"]["webhook_url"], indteam)

            logging.info("ULTRON PROGRAM TERMINATED")


if __name__ == "__main__":
   main(sys.argv[1:])

