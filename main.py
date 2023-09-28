import streamlit as st
from functions import ideator
import json
import os
import sys
from datetime import datetime
from supabase_client import SupabaseConnection

#connect to supabase

supabase = SupabaseConnection()
data, count = supabase.table("bots_dev").select("*").eq("id", "mel").execute()
bot_info = data[1][0]

def main():
    
    name = st.text_input('lead name', value = 'Jeremy')
    booking_link = "bookinglink.com/trala"
    lead_email = st.text_input('lead email', value = 'uzair@hellogepeto.com')
    now = datetime.now().strftime("%Y-%m-%d %H:%M:%S")

    system_prompt = bot_info['system_prompt']
    system_prompt = system_prompt.format(lead_email = lead_email, datetime = now)
    initial_text = bot_info['initial_text']

    # Create a title for the chat interface
    st.title("Mel - Trala")
    st.write("To test or reset, first click the button below.")
    
    if st.button('Click to Start or Restart'):
        st.write(initial_text)
        restart_time = datetime.now().strftime('%Y-%m-%d %H:%M:%S')
        with open('database.jsonl', 'r') as db, open('archive.jsonl','a') as arch:
        # add reset 
            arch.write(json.dumps({"restart": restart_time}) + '\n')
        #copy each line from db to archive
            for line in db:
                arch.write(line)

        #clear database to only first two lines
        with open('database.jsonl', 'w') as f:
        # Override database with initial json files
            messages = [
                {"role": "system", "content": system_prompt},
                {"role": "assistant", "content": initial_text}            
            ]
            f.write(json.dumps(messages[0])+'\n')
            f.write(json.dumps(messages[1])+'\n')



    #initialize messages list and print opening bot message
    #st.write("Hi! This is Tara. Seems like you need help coming up with an idea! Let's do this. First, what's your job?")

    # Create a text input for the user to enter their message and append it to messages
    userresponse = st.text_input("Enter your message")
    

    # Create a button to submit the user's message
    if st.button("Send"):
        #prep the json
        newline = {"role": "user", "content": userresponse}

        #append to database
        with open('database.jsonl', 'a') as f:
        # Write the new JSON object to the file
            f.write(json.dumps(newline) + '\n')

        #extract messages out to list
        messages = []

        with open('database.jsonl', 'r') as f:
            for line in f:
                json_obj = json.loads(line)
                messages.append(json_obj)

        #generate OpenAI response
        messages, count = ideator(messages)

        #append to database
        with open('database.jsonl', 'a') as f:
                for i in range(count):
                    f.write(json.dumps(messages[-count + i]) + '\n')



        # Display the response in the chat interface
        string = ""

        for message in messages[1:]:
            try:
                string = string + message["role"] + ": " + message["content"] + "\n\n"
            except: 
                print('had trouble with this message: ' + str(message))
        st.write(string)
            

if __name__ == '__main__':
    main()


    
