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
    """Sends a calendar invite to the specified attendees.

    Args:
    attendee_email: A list of email addresses of the attendees.
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

    msg = MIMEMultipart()
    msg['From'] = f"Trala <{organizer_email}>"
    msg['To'] = ', '.join(attendee_emails)
    msg['Subject'] = email_subject

    cal = icalendar.Calendar()
    event = icalendar.Event()
    event.add('summary', invite_subject)
    event.add('description', description)
    event.add('dtstart', start_time)
    event.add('dtend', end_time)
    event.add('organizer', icalendar.vCalAddress(f"mailto:{organizer_email}"))
    event['organizer'].params['cn'] = icalendar.vText('Trala')
    cal.add_component(event)
    ical_str = cal.to_ical().decode("utf-8")

    ical_part = MIMEBase('text', 'calendar', method="REQUEST", charset="UTF-8")
    ical_part.set_payload(ical_str)
    encoders.encode_base64(ical_part)
    ical_part.add_header('Content-Disposition', 'attachment; filename="invite.ics"')
    msg.attach(ical_part)

    smtp_server = 'smtp.gmail.com'
    smtp_port = 587
    smtp_username = organizer_email
    smtp_password = password

    try:
        server = smtplib.SMTP(smtp_server, smtp_port)
        server.ehlo()
        server.starttls()
        server.login(smtp_username, smtp_password)
        server.sendmail(msg['From'], attendee_emails + bcc_emails, msg.as_string())
        server.quit()
        return "success"
    except Exception as e:
        return "Error: " + str(e)


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
    for sentence in sentences:
        if part1_length + len(sentence) <= total_length / 2:
            part1.append(sentence)
            part1_length += len(sentence)
        else:
            part2.append(sentence)

    # Join the sentences in each part back into strings
    #if part2 is empty, just return part1
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

        # Step 1, send model the user query and what functions it has access to
        result = openai.ChatCompletion.create(
            model="gpt-4",
            messages= messages,
            functions = functions,
            function_call = "auto",
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
    except:
        print('encountered an error, trying again')
        continue





