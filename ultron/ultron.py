import json
import os, sys
import pprint
import imp, argparse
import pprint

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

    #mdata = []
    mdata = dict()
    masterdata = dict()

    #tdata = []
    tdata = dict()
    teamdata = dict()

    team_env = []


    # Add our folder to the system path
    sys.path.append(os.path.abspath(os.path.join(os.path.dirname(__file__), '..')))

    parser = argparse.ArgumentParser(description='Check versions')
    parser.add_argument('-d','--debug', help='Enable debug output',action='store_true')
    parser.add_argument('-c','--config', help='Full path to a config file',required=True)
    args = parser.parse_args()

    debug = args.debug

    config_map = read_config_file(args.config)

    if config_map:

        team_list = config_map["Teams"]
        for team in team_list:

            plugins_list = team_list[team]["plugins"]
            for aplugin in plugins_list:
                plugin_name = aplugin["pluginname"]

                if team_list[team]["master"] == "TRUE":
                    # add master environment mapping elements
                    team_env.append({"team": "master", "environments": aplugin["environments"]})
                elif team_list[team]["master"] == "FALSE":
                    # add team environment mapping elements
                    team_env.append({"team":team, "environments" : aplugin["environments"]})

                if debug: print "Loading plugin %s" % plugin_name
                # Load the plugin from the plugins folder
                plugin_handle = plugin.loadPlugin(plugin_name)

                try:
                    plugin_data = plugin_handle.check_versions(team_list[team]['profile_name'], aplugin['region_name'],
                                                           aplugin['onlycheckifhealthy'], aplugin['environments'],
                                                           aplugin['onlylive'])
                except Exception, e:
                    print str(e)

                if debug:   pprint.pprint(plugin_data)
                # Store the plugin output in a dict
                if team_list[team]["master"] == "TRUE":
                    """""
                    mdata = plugin_data
                    for m in mdata:
                        m.update({"team": "master"})
                    """""
                    mdata[team] = plugin_data
                    masterdata[plugin_name] = mdata

                elif team_list[team]["master"] == "FALSE":
                    """""
                    tdata = plugin_data
                    for t in tdata:
                        t.update({"team":team})
                    """""
                    tdata[team] = plugin_data
                    teamdata[plugin_name] = tdata

    #pprint.pprint(masterdata)
    #pprint.pprint(teamdata)
    #pprint.pprint(team_env)

    compared_data = compare.compare_teams(teamdata,masterdata,team_env)
    output.display_results(compared_data)



if __name__ == "__main__":
   main(sys.argv[1:])



















