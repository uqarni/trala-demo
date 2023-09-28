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
                    }
                }

            }
        ]

def send_calendar_invite(attendee_email, start_year, start_month, start_day, start_hour, start_minute, timezone):
    organizer_email = 'scheduler@trala.com'
    password = 'jluluyybzsvsfjqu'
    email_subject = "Trala Interest Call Scheduled!"
    invite_subject = "Trala Interest Call"
    description = "Hi there! Looking forward to our call to discuss violin lessons with Trala. If you have any questions or thoughts before this call, contact us from our website."
    tz = pytz.timezone(timezone)
    start_time = datetime(start_year, start_month, start_day, start_hour, start_minute, tzinfo=tz)
    end_time = start_time + timedelta(minutes = 30)
    attendee_emails = [attendee_email]
    cc_emails = []
    bcc_emails = ['uzair@hellogepeto.com', 'mert@hellogepeto.com']


    """Sends a calendar invite to the specified attendees.

    Args:
        organizer_email: The email address of the organizer.
        attendee_emails: A list of email addresses of the attendees.
        subject: The subject of the invite.
        description: The description of the invite.
        start_time: The start time of the invite (datetime.datetime object).
        end_time: The end time of the invite (datetime.datetime object).

    Returns:
        None.
    """
    # Create the MIMEMultipart message.
    msg = MIMEMultipart()
    msg['From'] = f"Trala <{organizer_email}>"
    msg['To'] = ', '.join(attendee_emails)
    #msg['Bcc'] = ', '.join(bcc_emails)
    msg['Subject'] = email_subject

    # Create the iCalendar event.
    cal = icalendar.Calendar()
    event = icalendar.Event()
    event.add('summary', invite_subject)
    event.add('description', description)
    event.add('dtstart', start_time)
    event.add('dtend', end_time)

    # Add the organizer to the event.
    event.add('organizer', icalendar.vCalAddress(f"mailto:{organizer_email}"))
    event['organizer'].params['cn'] = icalendar.vText('Trala')

    cal.add_component(event)
    # Convert the iCalendar object to a string.
    ical_str = cal.to_ical().decode("utf-8")

    # Attach the iCalendar event to the MIMEMultipart message.
    ical_part = MIMEBase('text', 'calendar', method="REQUEST", charset="UTF-8")
    ical_part.set_payload(ical_str)
    encoders.encode_base64(ical_part)
    ical_part.add_header('Content-Disposition', 'attachment; filename="invite.ics"')
    msg.attach(ical_part)

    # Send the email message.
    smtp_server = 'smtp.gmail.com'
    smtp_port = 587
    smtp_username = organizer_email
    smtp_password = password

    try:
        server = smtplib.SMTP(smtp_server, smtp_port)
        server.ehlo()
        server.starttls()
        server.login(smtp_username, smtp_password)
        response = server.sendmail(msg['From'], attendee_emails + bcc_emails,msg.as_string())
        server.quit()
        return "success"
    except Exception as e:
        print("Failed to send invite.")
        print(f"Error: {e}")
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

  # Step 2, check if the model wants to call a function
  if message.get("function_call"):
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

      # Step 4, send model the info on the function call and function response
      messages.append(message)
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
      response = message["content"]
  
  split_response = split_sms(response)
  count = len(split_response)
  for section in split_response:
    section = {
      "role": "assistant", 
      "content": section
    }
    messages.append(section)

  return messages, count





