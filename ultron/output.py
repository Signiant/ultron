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

def display_results(data_array):

    for value in data_array:
        themessage = get_themessage(value["Match"])
        print("M_Environment = [" + value['master_env'] + "] *  M_Version = " + value['master_version'] +"master updated on "
              + value["master_updateddate"].strftime('%m/%d/%Y %H:%M:%S')
              + " * Team: " +value['team']+ " T_Environment = ["+value['team_env'] + "] * T_Version " + value['team_version']
              + "master updated on "+ value["team_updateddate"].strftime('%m/%d/%Y %H:%M:%S')
              +" === "+ themessage+"\n")

def form_the_time(thetime):

    if thetime == "":
        time_updated =""
    else:
        time_updated = "\nUpdated On: "+thetime.strftime('%m/%d/%Y %H:%M:%S')

    return time_updated

def shorten_input(thestring):
    if len(thestring) > 30:
        thestring = thestring[:20]+"..."
        return thestring
    else:
        return thestring

def format_version(thestring):
    if thestring.find(":") != -1:
        colon_index = thestring.find(":")
        outputstring = "ver: "+thestring[:colon_index]+"\nver#: "+thestring[(colon_index+1):]
        return outputstring
    else:
        thestring = "ver: "+thestring
        return thestring

def append_to_field(fields, value, match_type):

    if match_type == 1:
        emojicon = ":relaxed:"
    elif match_type == 2:
        emojicon = ":cry:"
    elif match_type == 3:
        emojicon = ":thinking_face: "

    fields.append({
        # adding team data
            "title": "\n\n" +shorten_input(value['team_env']),
            "value": emojicon+format_version(value['team_version'])
                     + form_the_time(value["team_updateddate"]),
            "short": "true"
        })
    # adding master data
    fields.append({


        #removed from title --> value['mastername']+" env: "
        'title': "\n\n"+ shorten_input(value['master_env']),
        'value': emojicon+format_version(value['master_version'])
                 + form_the_time(value["team_updateddate"]),
        'short': "true"
    })
    return 1

def output_slack_payload(data_array, webhook_url, eachplugin, eachteam):

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

    if eachplugin == "eb":
        thetitle_beginning = "Beanstalk environments"
    elif eachplugin == "ecs":
        thetitle_beginning = "ECS services"

    #append not matching
    if field_not_matching:
        thetitle = thetitle_beginning+"  not matching "+themaster
        the_color = "#ec1010"
        attachments.append({'title':thetitle,'fields': field_not_matching,'color':the_color})
    #append repos
    if field_repo:
        thetitle = thetitle_beginning+" running dev branches"
        the_color = "#fef65b"
        attachments.append({'title': thetitle, 'fields': field_repo, 'color': the_color})
    # append matching
    if field_matching:
        thetitle = thetitle_beginning+" matching " + themaster
        the_color = "#7bcd8a"
        attachments.append({'title': thetitle, 'fields': field_matching, 'color': the_color})

    pretext = "*Region:* " + value["regionname"] + ", " + eachteam
    attachments.insert(0,{'pretext':pretext, "mrkdwn_in": ["pretext"] })

    logging.debug("printing attachments")
    logging.debug(attachments)

    pprint.pprint(attachments)


    #creating payload, CHANNEL WILL NEED TO BE DIFFERENT FOR EACH TEAM
    result = {
        'as_user': False,
        "channel": str(eachteam),
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


    return  1#response.status_code










