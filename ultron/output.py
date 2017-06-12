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

#format time if data available
def form_the_time(thetime):

    if thetime == "":
        time_updated =""
    else:
        time_updated = "\nUpdated On: "+thetime.strftime('%m/%d/%Y %H:%M:%S')

    return time_updated

#compress string is larger than 30 length
def shorten_input(thestring):
    if len(thestring) > 30:
        thestring = thestring[:27]+"..."
        return thestring
    else:
        return thestring


def append_to_field(fields, value, mastername):

    fields.append({
        # adding team data
            "title": "\n\n"+shorten_input(value['team_env']),
            "value": value['team_version'] + form_the_time(value["team_updateddate"]),
            "short": "true"
        })

    fields.append({
        # adding master data
        'title': "\n\n"+shorten_input(mastername+": "+value['master_env']),
        'value': value['master_version'] + form_the_time(value["master_updateddate"]),
        'short': "true"
    })
    #adding more slack fields to create vertical spacing
    add_indent_fields(fields)
    add_indent_fields(fields)

    return 1


#get the slack channel and region for slack post
def get_item_from_array(data_array,item_string):

    result = "Not Found"

    try:
        if data_array:
            for the_data in data_array:
                for items in data_array[the_data]:
                    if item_string in items:
                        result = items[item_string]
                        break
    except Exception,e:
        print "error in get_item_from_array function "+str(e)

    return result


#create attachment for each plugin
def create_plugin_format(thedata, thetitle_beginning):

    field_matching = []
    field_not_matching = []
    field_repo = []

    theattachment = []

    for value in thedata:
        if value["Match"] == 1:
            append_to_field(field_matching, value, value['mastername'])
        if value["Match"] == 2:
            append_to_field(field_not_matching, value, value['mastername'])
        if value["Match"] == 3:
            append_to_field(field_repo, value, value['mastername'])

    # append not matching
    if field_not_matching:
        thetitle = thetitle_beginning + "s not matching " + value['mastername']
        the_color = "#ec1010"
        theattachment.append({'title': thetitle, 'fields': field_not_matching, 'color': the_color})
    # append repos
    if field_repo:
        thetitle = thetitle_beginning + "s running dev branches"
        the_color = "#fef65b"
        theattachment.append({'title': thetitle, 'fields': field_repo, 'color': the_color})
    # append matching
    if field_matching:
        thetitle = thetitle_beginning + "s matching " + value['mastername']
        the_color = "#7bcd8a"
        theattachment.append({'title': thetitle, 'fields': field_matching, 'color': the_color})

    return theattachment

#plugin data array is empty
def no_elements_found(thetitle_beginning):

    theattachment = []

    thetitle = thetitle_beginning+" not found"
    the_color = "#9B30FF"

    theattachment.append({'title': thetitle, 'color': the_color})

    return theattachment



#main output to slack function
def output_slack_payload(data_array, webhook_url, eachteam):

    attachments = []

    logging.debug("printing data array in output_slack_payload")
    logging.debug(data_array)

    for theplugin in data_array:
        if data_array[theplugin]:
            attachments = attachments + create_plugin_format(data_array[theplugin], theplugin)
        else:
            attachments = attachments + no_elements_found(theplugin)

    theregionname = get_item_from_array(data_array,'regionname')
    theslackchannel = get_item_from_array(data_array,'slackchannel')

    logging.debug( "the team is " + eachteam + " slack channel " + theslackchannel+" the region is "+theregionname)

    pretext = "*Region:* " + theregionname + ", " + eachteam
    attachments.insert(0,{'pretext':pretext, "mrkdwn_in": ["pretext"] })

    logging.debug("printing attachments")
    logging.debug(attachments)

    #logging.debug(pprint.pprint(attachments))

    try:
        #creating json payload
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

