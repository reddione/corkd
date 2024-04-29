# Download the helper library from https://www.twilio.com/docs/python/install
import os
import json

import schedule
import requests
from twilio.rest import Client
from pygooglenews import GoogleNews

from openai import OpenAI

# ----- local info storage -----

players = {}
FILE_LOCATION = os.environ['FILE_STORE']

# ----- GoogleNews Config -----

gn_client = GoogleNews()

# ----- Twilio Config -----
account_sid = os.environ['TWILIO_ACCOUNT_SID']
auth_token = os.environ['TWILIO_AUTH_TOKEN']
twilio_client = Client(account_sid, auth_token)

# ----- OpenAI Config -----

PRE_PROMPT = {"role": "system", "content": "You are the back-end of an app, designed to notify users when a notable "
                                           "figure has passed away. To do this, you will be given two pieces of "
                                           "information: on the first line, the person you are looking for will be "
                                           "specified in the format 'Subject: <Person>'. From that point in the prompt "
                                           "onwards, you will be given a list of recent headlines that contain this "
                                           "person's name, and you will determine from these headlines whether the "
                                           "person is deceased, and then respond simply 'true' if they are dead or "
                                           "'false' if they are fortunately still alive. It is imperative that you "
                                           "only reply with these words and nothing else, as your response will go "
                                           "directly back into the app's model. No yapping."}

openai_client = OpenAI()


def notify(phone: str, message: str):
    message = twilio_client.messages.create(
            body=message,
            from_=os.environ["TWILIO_AGENT_PHONE_NUM"],
            to=phone
        )


def notify_all(message: str):
    global players

    phones = [players[x]['phone'] for x in players]
    for phone in phones:
        notify(phone, message)


def check_if_dead(name):

    news = [x['title'] for x in gn_client.search(f"allintitle: {name}", when="8h")['entries']]

    if len(news) >= 5:
        news = news[0:4]

    prompt_string = f"Subject: {name}"

    for hl in news:
        prompt_string += f"\n- {hl}"

    prompt = {"role": "user", "content": prompt_string}

    response = openai_client.chat.completions.create(
        model="gpt-3.5-turbo",
        messages=[
            PRE_PROMPT,
            prompt
        ],
        temperature=0.75,
        max_tokens=10
    )

    return response.choices[0].message.content


def load_players():
    global players
    with open('players.json', 'r') as f:
        players = json.load(f)


def save_players():
    global players
    with open('players.json', 'w') as f:
        json.dump(players, f)


def check_all():
    for player in players:
        for name in player['names']:
            if check_if_dead(name):

                players[player]['names'].remove(name)
                players[player]['score'] += 1
                notify_all(f"Ouch! Looks like {name} died, leaving {player}'s score at {players[player]['score']}")


def notify_scores():
    out = "Checking in! The current scores are:"
    for player in players:
        out += f"\n{player}: {player['score']}"
    notify_all(out)


if __name__ == "__main__":

    if os.path.exists('players.json'):
        load_players()
    else:
        players = requests.get(os.environ["PLAYERS_GET_URL"]).json()
        save_players()

    with open("conf.json", "rw") as file_conf:
        conf = json.load(file_conf)
    if conf["first_time"]:
        notify_all("Welcome to Corkd - your number one text-based source for finding out whether your favourites have"
                   "corked it. You'll be receiving weekly updates on the score of the game at 10am every Wednesday, "
                   "along with little updates any time the score changes.")
        conf["first_time"] = False

    schedule.every(8).hours.do(check_all)
    schedule.every().tuesday.at("11:00", "Europe/London").do(notify_scores)

