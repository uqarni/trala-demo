import openai
import os
import re
import random
import json
import smtplib
from email.mime.multipart import MIMEMultipart
from email.mime.base import MIMEBase
from email import encoders
import icalendar
from datetime import datetime, timedelta
import pytz
import requests
from zoneinfo import ZoneInfo

#functions for openai
functions=[
            {
                "name": "send_calendar_invite",
                "description": "Send a calendar invite to a given email address at a given time",
                "parameters": {
                    "type": "object",
                    "properties": {
                        "attendee_email":{
                            "type": "string",
                            "description": "The email address of the person to send the invite to. If you don't know, ask.",
                        },
                        "start_year":{
                            "type": "integer",
                            "description": "The four-digit year of the event, such as 2023",
                        },
                        "start_month":{
                            "type": "integer",
                            "description": "The two-digit month of the event, such as 04 for April",
                        },
                        "start_day":{
                            "type": "integer",
                            "description": "The date of the event, such as 27 if taking place on th 27th",
                        },
                        "start_hour":{
                            "type": "integer",
                            "description": "The hour of the event in 24-hour time, such as 14 if taking place at 2pm",
                        },
                        "start_minute":{
                            "type": "integer",
                            "description": "The two-digit minute of the event",
                        },
                        "timezone":{
                            "type": "string",
                            "enum": ["America/New_York", "America/Chicago", "America/Denver", "America/Los_Angeles"],
                            "description": "The timezone of the event based on the lead's local timezone. Ask if you don't know.",
                        },
                    },
                    "required": ["attendee_email", "start_year", "start_month", "start_day", "start_hour", "start_minute", "timezone"]
                }

            }
        ]

def send_calendar_invite(attendee_email, start_year, start_month, start_day, start_hour, start_minute, timezone):
    print('start hour: ' + str(start_hour))
    print('start minute: ' + str(start_minute))
    print('timezone: ' + str(timezone))
    """Sends a calendar invite to the specified attendees.

    Args:
    attendee_email: Email address of the lead.
    start_year: The start year of the invite, default to current year.
    start_month: The start month of the invite
    start_day: The start day of the invite
    start_hour: The start hour of the invite
    start_minute: The start minute of the invite
    timezone: The timezone of the invite

    Returns:
    success or error.
    """
    organizer_email = 'scheduler@trala.com'
    password = 'jluluyybzsvsfjqu'
    email_subject = "Trala Interest Call Scheduled!"
    invite_subject = "Trala Interest Call"
    description = "Hi there! Looking forward to our call to discuss violin lessons with Trala. If you have any questions or thoughts before this call, contact us from our website."
    
    tz = pytz.timezone(timezone)
    start_time = datetime(start_year, start_month, start_day, start_hour, start_minute, tzinfo=tz)
    end_time = start_time + timedelta(minutes=30)
    attendee_emails = [attendee_email]
    bcc_emails = ['uzair@hellogepeto.com', 'mert@hellogepeto.com']

    # Convert start_time to CST for easier comparison
    cst = pytz.timezone('America/Chicago')
    current_time_cst = datetime.now(cst)
    start_time_cst = start_time.astimezone(cst)

    # Check if the event is in the past
    if start_time_cst < current_time_cst:
        return "Error: Event is in the past; we can't do that"

    # Check if the event is within the next hour
    if start_time_cst < current_time_cst + timedelta(hours=1):
        return "Error: Event is within the next hour; we can't do that"

    # Check if the event is outside of 9 am - 5 pm CST, Monday - Friday
    if start_time_cst.weekday() >= 5 or start_time_cst.hour < 9 or start_time_cst.hour >= 17:

        return "Error: Event is outside of 9 am - 5 pm CST, Monday - Friday, which are our working hours"
    url = "https://hooks.zapier.com/hooks/catch/15188930/3z3tc0k/"
    data = {
        "attendee_email": attendee_email,
        "start_year": start_year,
        "start_month": start_month,
        "start_day": start_day,
        "start_hour": start_hour,
        "start_minute": start_minute,
        "timezone": timezone,

   }
    start_time = dict_to_iso_format(data)
    #add 30 minutes to start time to get end time
    end_time = datetime.fromisoformat(start_time) + timedelta(minutes=15)
    data = {
        "attendee_email": attendee_email,
        "start_time": start_time,
        "end_time": end_time,
        "human_readable_start_time": str(start_time_cst)[11:-6] + ' CST ' +  str(start_day) + "/" + str(start_month),
    }
    
    requests.post(url, data=data)
    #return message with normal invite date and time and timezone
    return "Success! Calendar invite sent to " + attendee_email + " for meeting at " + start_time + " " + timezone + "."


#split sms
def split_sms(message):
    # Use regular expressions to split the string at ., !, or ? followed by a space or newline
    sentences = re.split('(?<=[.!?]) (?=\\S)|(?<=[.!?])\n', message.strip())
    # Strip leading and trailing whitespace from each sentence
    sentences = [sentence.strip() for sentence in sentences if sentence.strip()]

    # Compute the total length of all sentences
    total_length = sum(len(sentence) for sentence in sentences)

    # Split the sentences into two parts such that the difference in their total lengths is minimized
    part1 = []
    part2 = []
    part1_length = 0
    i = 0
    while i < len(sentences) and part1_length + len(sentences[i]) <= total_length / 2:
        part1.append(sentences[i])
        part1_length += len(sentences[i])
        i += 1

    part2 = sentences[i:]

    # Join the sentences in each part back into strings
    #if part1 is empty, just return part2
    if len(part1) == 0:
        strings = [" ".join(part2)]
    else:
        #half the time, include both parts in two strings
        if random.random() < 0.5:
            strings = [" ".join(part1), " ".join(part2)]
        else:
            #add both part1 and part2 into one string
            strings = [" ".join(part1 + part2)]

    return strings


#generate openai response; returns messages with openai response
def ideator(messages):
  for i in range(5):
    try:
        key = os.environ.get("OPENAI_API_KEY")
        openai.api_key = key
        print('yo!')
        # Step 1, send model the user query and what functions it has access to
        result = openai.ChatCompletion.create(
            model="gpt-4-1106-preview",
            messages= messages,
            temperature = 0,
            # functions = functions,
            # function_call = "auto",
        )

        message = result["choices"][0]["message"]
        print('step 1 output: ' + str(message))

        # Step 2, check if the model wants to call a function
        if message.get("function_call"):
            print('function call')
            function_name = message["function_call"]["name"]
            function_args = json.loads(message["function_call"]["arguments"])

            # Step 3, call the function
            # Note: the JSON response from the model may not be valid JSON
            if function_name == "send_calendar_invite":
                function_response = send_calendar_invite(
                    attendee_email=function_args.get("attendee_email"),
                    start_year=function_args.get("start_year"),
                    start_month=function_args.get("start_month"),
                    start_day=function_args.get("start_day"),
                    start_hour=function_args.get("start_hour"),
                    start_minute=function_args.get("start_minute"),
                    timezone=function_args.get("timezone"),
                )
                print("function response: " + str(function_response))
            # Step 4, send model the info on the function call and function response
            messages.append(message)
            print('messages: ' + str(messages))
            messages.append({
                        "role": "function",
                        "name": function_name,
                        "content": function_response,
                    })

            second_response = openai.ChatCompletion.create(
                model="gpt-4",
                messages=messages)
            response = second_response["choices"][0]["message"]["content"]
        else: 
            print('non function call')
            response = message["content"]
        print('final response: ' + str(response))
        split_response = split_sms(response)
        count = len(split_response)
        for section in split_response:
            section = {
            "role": "assistant", 
            "content": section
            }
            messages.append(section)

        return messages, count
    except Exception as e:
        print('encountered an error, trying again: ', e)
        print(messages[1:])
        continue




def dict_to_iso_format(data: dict):
    # Create a naive datetime object
    naive_dt = datetime(
        data["start_year"],
        data["start_month"],
        data["start_day"],
        data["start_hour"],
        data["start_minute"]
    )
    
    # Localize the naive datetime object to the given timezone
    timezone = pytz.timezone(data["timezone"])
    localized_dt = timezone.localize(naive_dt)

    # Convert to ISO 8601 format without the seconds
    iso_format = localized_dt.isoformat(timespec='minutes')

    return iso_format

