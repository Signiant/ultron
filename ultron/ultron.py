import json
import os, sys
import pprint
import imp, argparse
import logging

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

    mdata = dict()
    masterdata = dict()

    tdata = dict()
    teamdata = dict()

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
                    plugin_data = plugin_handle.check_versions(team_list[team]['profile_name'], aplugin['region_name'],
                                                           aplugin['onlycheckifhealthy'], aplugin['environments'],
                                                           aplugin['onlylive'])
                    logging.debug(plugin_data)
                    # Store the plugin output in a dict
                    if team_list[team]["master"]:
                        mdata[team] = plugin_data
                        masterdata[plugin_name] = mdata
                    else:
                        tdata[team] = plugin_data
                        teamdata[plugin_name] = tdata

                except Exception, e:
                    print str(e)

    #logging.debug(masterdata)
    #logging.debug(teamdata)
    #logging.debug(team_env)

    compared_data = compare.compare_teams(teamdata,masterdata)
    output.display_results(compared_data)



if __name__ == "__main__":
   main(sys.argv[1:])

