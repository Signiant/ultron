import pprint
from operator import itemgetter
import requests
import json
import logging

def id():
    return "output"

def log(message):
    print id() + ": " + message

def get_themessage(value):
    if value == 1:
        return "Matches Master"
    elif value == 2:
        return "Does not match master"
    elif value == 3:
        return "Branch repo"


def append_to_field(fields, value):
    fields.append(
        # adding team data
        {
            "title": "Env: " + value['team_env'],
            "value": "Ver: " + value['team_version'] + "\nupdated on: "
                     + value["team_updateddate"].strftime('%m/%d/%Y %H:%M:%S'),
            "short": "true"
        })
    # adding master data
    fields.append({
        'title': "Master Env: " + value['master_env'],
        'value': "Ver: " + value['master_version'] + "\nupdated on: "
                 + value["master_updateddate"].strftime('%m/%d/%Y %H:%M:%S'),
        'short': "true"
    })
    return 1


def display_results(data_array):

    for value in data_array:
        themessage = get_themessage(value["Match"])
        print("M_Environment = [" + value['master_env'] + "] *  M_Version = " + value['master_version'] +"master updated on "
              + value["master_updateddate"].strftime('%m/%d/%Y %H:%M:%S')
              + " * Team: " +value['team']+ " T_Environment = ["+value['team_env'] + "] * T_Version " + value['team_version']
              + "master updated on "+ value["team_updateddate"].strftime('%m/%d/%Y %H:%M:%S')
              +" === "+ themessage+"\n")

def output_slack_payload(data_array, teamname, webhook_url):

    attachments = []
    field_matching = []
    field_not_matching = []
    field_repo = []

    logging.debug("printing data array in output_slack_payload")
    logging.debug(data_array)

    for value in data_array:
        if value["Match"] == 1:
            append_to_field(field_matching, value)
        if value["Match"] == 2:
            append_to_field(field_not_matching, value)
        if value["Match"] == 3:
            append_to_field(field_repo, value)

    #append not matching
    if field_not_matching:
        thetitle = "Environments that are different from Master"# + value["mastername"]
        the_color = "#ab3456"
        attachments.append({'title':thetitle,'fields': field_not_matching,'color':the_color})
    #append repos
    if field_repo:
        thetitle = "Environments that are branch repositories"# + value["mastername"]
        the_color = "#e65c00"
        attachments.append({'title': thetitle, 'fields': field_repo, 'color': the_color})
    # append matching
    if field_matching:
        thetitle = "Environments that match Master"# + value["mastername"]
        the_color = "#7bcd8a"
        attachments.append({'title': thetitle, 'fields': field_matching, 'color': the_color})

    pretext = "Region name: " + value["regionname"] + ", " + teamname
    attachments.insert(0,{'pretext':pretext})

    logging.debug("printing attachments")
    logging.debug(attachments)

    #creating payload, CHANNEL WILL NEED TO BE DIFFERENT FOR EACH TEAM
    result = {
        'as_user': False,
        "channel":str(teamname),
        "attachments":attachments
    }

    #sending json payload
    response = requests.post(
        webhook_url, json=result
    )

    if response.status_code != 200:
        raise ValueError(
            'Slack returned status code %s, the response text is %s'%(response.status_code,response.text)
        )

    return  response.status_code










