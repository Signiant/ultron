import pprint
import requests
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

def add_indent_fields(fields):
    fields.append({
            "title": "",
            "value": "",
            "short": "true"
        })
    fields.append({
        'title': "",
        'value': "",
        'short': "true"
    })
    return 1

def form_the_time(thetime):

    if thetime == "":
        time_updated =""
    else:
        time_updated = "\nUpdated On: "+thetime.strftime('%m/%d/%Y %H:%M:%S')

    return time_updated


def shorten_input(thestring):
    if len(thestring) > 30:
        thestring = thestring[:27]+"..."
        return thestring
    else:
        return thestring


#format the version info displayed depending on ecs or eb data
def format_version(thestring):
    if thestring.find(":") != -1:
        colon_index = thestring.find(":")
        outputstring = shorten_input("ver: "+thestring[:colon_index])+"\nver#: "+thestring[(colon_index+1):]
        return outputstring
    else:
        thestring = "ver: "+thestring
        return thestring

#adding emojis to fields
def append_to_field(fields, value, match_type, mastername):
    if match_type == 1:
        emojicon = ":relaxed:"
    elif match_type == 2:
        emojicon = ":cry:"
    elif match_type == 3:
        emojicon = ":thinking_face: "

    fields.append({
        # adding team data
            "title": "\n\n"+emojicon+shorten_input(value['team_env']),
            "value": format_version(value['team_version'])
                     + form_the_time(value["team_updateddate"]),
            "short": "true"
        })

    fields.append({
        # adding master data
        'title': "\n\n"+emojicon+shorten_input(mastername+": "+value['master_env']),
        'value': format_version(value['master_version'])
                 + form_the_time(value["team_updateddate"]),
        'short': "true"
    })

    add_indent_fields(fields)
    add_indent_fields(fields)

    return 1

#create attachment for each plugin
def create_plugin_format(data_array,theplugin, theattachment, thetitle_beginning):

    field_matching = []
    field_not_matching = []
    field_repo = []

    some_data = dict()

    for value in data_array[theplugin]:
        if value["Match"] == 1:
            append_to_field(field_matching, value, value["Match"], value['mastername'])
        if value["Match"] == 2:
            append_to_field(field_not_matching, value, value["Match"], value['mastername'])
        if value["Match"] == 3:
            append_to_field(field_repo, value, value["Match"], value['mastername'])

        some_data.update({'slack_channel':value['slackchannel']})
        some_data.update({'region_name':value['regionname']})

    # append not matching
    if field_not_matching:
        thetitle = thetitle_beginning + "  not matching " + value['mastername']
        the_color = "#ec1010"
        theattachment.append({'title': thetitle, 'fields': field_not_matching, 'color': the_color})
    # append repos
    if field_repo:
        thetitle = thetitle_beginning + " running dev branches"
        the_color = "#fef65b"
        theattachment.append({'title': thetitle, 'fields': field_repo, 'color': the_color})
    # append matching
    if field_matching:
        thetitle = thetitle_beginning + " matching " + value['mastername']
        the_color = "#7bcd8a"
        theattachment.append({'title': thetitle, 'fields': field_matching, 'color': the_color})

    return some_data


#main output to slack function
def output_slack_payload(data_array, webhook_url, eachteam):

    attachments = []

    eb_attachments = []
    ecs_attachments = []

    required_data = []

    logging.debug("printing data array in output_slack_payload")
    logging.debug(data_array)

    for theplugin in data_array:
        if theplugin == "eb":
            required_data = create_plugin_format(data_array,theplugin, eb_attachments,"Beanstalk environments")
        elif theplugin == "ecs":
            required_data = create_plugin_format(data_array, theplugin, ecs_attachments,"ECS services")

    attachments = eb_attachments + ecs_attachments

    theregionname = required_data['region_name']
    theslackchannel = required_data['slack_channel']

    print "the team is " + eachteam + " slack channel " + theslackchannel

    pretext = "*Region:* " + theregionname + ", " + eachteam
    attachments.insert(0,{'pretext':pretext, "mrkdwn_in": ["pretext"] })

    logging.debug("printing attachments")
    logging.debug(attachments)

    #pprint.pprint(attachments)

    try:
        #creating payload, CHANNEL WILL NEED TO BE DIFFERENT FOR EACH TEAM
        result = {
            'as_user': False,
            "channel": theslackchannel,
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

    except Exception, e:
        print str(e)



    return  response.status_code

