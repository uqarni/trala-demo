import openai
import os
import re
import random

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

  result = openai.ChatCompletion.create(
    model="gpt-4",
    messages= messages
  )
  response = result["choices"][0]["message"]["content"]
  
  split_response = split_sms(response)
  count = len(split_response)
  for section in split_response:
    section = {
      "role": "assistant", 
      "content": section
    }
    messages.append(section)

  return messages, count





