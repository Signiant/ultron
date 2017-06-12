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

            master_array = []

            # agregate desginated master team data
            for team in team_list:
                if team_list[team]["master"]:
                    master_array.append({team: team_list[team]})

            #pprint.pprint(master_array)

            for team in team_list:
                if not team_list[team]["master"]:
                    plugins_list = team_list[team]["plugins"]
                    for aplugin in plugins_list:
                        plugin_name = aplugin["pluginname"]
                        logging.debug("Loading plugin %s" % plugin_name)

                        # agregate desginated master team data for plugin
                        master_array = []
                        for m_team in team_list:
                            if team_list[m_team]["master"]:
                                m_plugins_list = team_list[m_team]["plugins"]
                                for m_aplugin in m_plugins_list:
                                    m_plugin_name = m_aplugin["pluginname"]
                                    if m_plugin_name == plugin_name:
                                        master_array.append({m_team: m_aplugin})

                        # Load the plugin from the plugins folder
                        plugin_handle = plugin.loadPlugin(plugin_name)

                        try:

                        #retrieve data from plugin data

                            logging.info("Reading "+str(team)+" data for ultron")

                            plugin_data = plugin_handle.check_versions(master_array,
                                                                       aplugin,
                                                                       superjenkins_data,
                                                                       config_map["General"]["jenkins"]["branch_equivalent_tags"])

                            if plugin_data:
                                # update dictionary if key exists
                                if teamdata.has_key(team):
                                    teamdata[team].update(plugin_data)
                                else:
                                    teamdata[team] = (plugin_data)

                        except Exception, e:
                            print "main ultron plugin error "+str(e)
                        except EOFError, e:
                           print "End of file reached and value " + e + " not found"
                        except KeyError, e:
                            print "Key " + e + "not found"

    for indteam in teamdata:
        output.output_slack_payload(teamdata[indteam], config_map["General"]["webhook_url"], indteam)

    logging.info("ULTRON PROGRAM TERMINATED")


if __name__ == "__main__":
   main(sys.argv[1:])

