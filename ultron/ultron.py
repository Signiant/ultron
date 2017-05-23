import json, requests
import os, sys
import pprint
import imp, argparse
import logging
import collections

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
    except:
        print "unable to load file"

    return config_map

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
                        plugin_data = plugin_handle.ecs_check_versions(team_list[team]['profile_name'], aplugin['region_name'],
                                                               aplugin['cluster_name'],team_list[team]["slack_channel"])

                    logging.debug(plugin_data)
                    # Store the plugin output in an array
                    if team_list[team]["master"]:
                        #update dictionary if key exists
                        if masterdata.has_key(team):
                            masterdata[team].update({plugin_name: plugin_data})
                        else:
                            masterdata[team] = ({plugin_name: plugin_data})

                    else:
                        # update dictionary if key exists
                        if teamdata.has_key(team):
                            teamdata[team].update({plugin_name: plugin_data})
                        else:
                            teamdata[team] = ({ plugin_name : plugin_data })
                except Exception, e:
                    print str(e)

    logging.debug(masterdata)
    logging.debug(teamdata)

    #print "masterdata"
    #pprint.pprint(masterdata)
    #print "teamdata"
    #pprint.pprint(teamdata)


    for indteam in teamdata:
        compared_data = compare.compare_teams(teamdata[indteam],masterdata)
        #passing data for each team and the team name
        output.output_slack_payload(compared_data, config_map["General"]["webhook_url"], indteam)


if __name__ == "__main__":
   main(sys.argv[1:])

