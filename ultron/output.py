import pprint
from operator import itemgetter


def id():
    return "compare"

def log(message):
    print id() + ": " + message

def display_results(data_array):

    sorted_array = sorted(data_array, key=itemgetter('team'))

    for value in sorted_array:
        print("M_Environment = [" + value['master_env'] + "] *  M_Version = " + value['master_version'] +"master updated on "
              + value["master_updateddate"].strftime('%m/%d/%Y %H:%M:%S')
              + " * Team: " +value['team']+ " T_Environment = ["+value['team_env'] + "] * T_Version " + value['team_version']
              + "master updated on "+ value["team_updateddate"].strftime('%m/%d/%Y %H:%M:%S')
              +" === " +value["Match"]+"\n")




