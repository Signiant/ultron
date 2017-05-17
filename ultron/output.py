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
        return "Does not match Master"
    elif value == 3:
        return "Branch repo"

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


def append_to_field(fields, value, match_type):

    team_version_ending = get_version_output_string(value['team_version'])
    master_version_ending = get_version_output_string(value['master_version'])

    if match_type == 1:
        emojicon = ":relaxed:"
    elif match_type == 2:
        emojicon = ":cry:"
    elif match_type == 3:
        emojicon = ":thinking_face: "


    fields.append(
        # adding team data
        {
            "title": "\n\nenv:  " + value['team_env'],
            "value": emojicon+" ver: "+team_version_ending
                     + "\nUpdated On: "+ value["team_updateddate"].strftime('%m/%d/%Y %H:%M:%S'),
            "short": "true"
        })
    # adding master data
    fields.append({
        'title': "\n\n"+value['mastername']+" env: " + value['master_env'],
        'value': emojicon+" ver: "+ master_version_ending
                 + "\nUpdated On: "+ value["master_updateddate"].strftime('%m/%d/%Y %H:%M:%S'),
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
        themaster = value['mastername']
        if value["Match"] == 1:
            append_to_field(field_matching, value, value["Match"])
        if value["Match"] == 2:
            append_to_field(field_not_matching, value, value["Match"])
        if value["Match"] == 3:
            append_to_field(field_repo, value, value["Match"])

    #append not matching
    if field_not_matching:
        thetitle = "Beanstalk environments not matching "+themaster
        the_color = "#ec1010"
        attachments.append({'title':thetitle,'fields': field_not_matching,'color':the_color})
    #append repos
    if field_repo:
        thetitle = "Beanstalk environments running dev branches"
        the_color = "#fef65b"
        attachments.append({'title': thetitle, 'fields': field_repo, 'color': the_color})
    # append matching
    if field_matching:
        thetitle = "Beanstalk environments matching " + themaster
        the_color = "#7bcd8a"
        attachments.append({'title': thetitle, 'fields': field_matching, 'color': the_color})


    pretext = "*Region:* " + value["regionname"] + ", " + teamname
    attachments.insert(0,{'pretext':pretext, "mrkdwn_in": ["pretext"] })

    logging.debug("printing attachments")
    logging.debug(attachments)

    pprint.pprint(attachments)

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










