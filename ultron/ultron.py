import json
import os, sys
import imp, argparse
import logging
import requests

#project modules
import plugin
import compare
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
        for team in team_list:
            plugins_list = team_list[team]["plugins"]
            for aplugin in plugins_list:
                plugin_name = aplugin["pluginname"]
                logging.debug("Loading plugin %s" % plugin_name)

                # Load the plugin from the plugins folder
                plugin_handle = plugin.loadPlugin(plugin_name)

                try:
                    if plugin_name == "eb":
                        plugin_data = plugin_handle.eb_check_versions(team_list[team]['profile_name'], aplugin['region_name'],
                                                               aplugin['onlycheckifhealthy'], aplugin['environments'],
                                                               aplugin['onlylive'],team_list[team]["slack_channel"])
                    elif plugin_name == "ecs":

                        env_code_name = does_key_exist(team_list[team],'environment_code_name')

                        plugin_data = plugin_handle.ecs_check_versions(team_list[team]['profile_name'], aplugin['region_name'],
                                                               aplugin['cluster_name'],team_list[team]["slack_channel"], env_code_name)
                    else:
                        logging.debug("plugin "+plugin_name+" does not exist")

                    logging.debug(plugin_data)

                    # Store the plugin output in an array if data recieved from calls
                    if plugin_data:
                        if team_list[team]["master"]:
                            # update dictionary if key exists
                            if masterdata.has_key(team):
                                masterdata[team].update({plugin_name: plugin_data})
                            else:
                                masterdata[team] = ({plugin_name: plugin_data})

                        else:
                            # update dictionary if key exists
                            if teamdata.has_key(team):
                                teamdata[team].update({plugin_name: plugin_data})
                            else:
                                teamdata[team] = ({plugin_name: plugin_data})

                except Exception, e:
                    print str(e)
                except EOFError, e:
                    print "End of file reached and value " + e + " not found"
                except KeyError, e:
                    print "Key " + e + "not found"

    logging.debug(masterdata)
    logging.debug(teamdata)

    #get json to get individual services/application build links
    cached_items = ""
    cached_array = ""

    b_htags = config_map["General"]["build_tags"]

    returned_data = requests.get(config_map["General"]["build_link"])
    returned_data_iterator = returned_data.iter_lines()

    for items in returned_data_iterator:
        if b_htags['8'] in items:
            cached_items = items.replace(items[items.find(b_htags['5']):items.find(b_htags['6']) + 2], "").replace(b_htags['7'], "")
            break

    for items in json.loads(cached_items):
        cached_array = json.loads(cached_items)[items]

    #execute compare and output
    for indteam in teamdata:
        compared_data = compare.compare_teams(teamdata[indteam],masterdata, cached_array, b_htags)
        #passing data for each team and the team name
        output.output_slack_payload(compared_data, config_map["General"]["webhook_url"],indteam)

    logging.info("ULTRON PROGRAM TERMINATED")


if __name__ == "__main__":
   main(sys.argv[1:])

