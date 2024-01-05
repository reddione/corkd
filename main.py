# Download the helper library from https://www.twilio.com/docs/python/install
import os
from twilio.rest import Client
from pygooglenews import GoogleNews

# Find your Account SID and Auth Token at twilio.com/console
# and set the environment variables. See http://twil.io/secure
#account_sid = os.environ['TWILIO_ACCOUNT_SID']
#auth_token = os.environ['TWILIO_AUTH_TOKEN']
#client = Client(account_sid, auth_token)

#message = client.messages.create(
#         body='zamn!!!!',
#         from_='+447411225379',
#         to='+447583245104'
#     )

#print(message.sid)


def check_if_dead(name):
    gn = GoogleNews()

    news = [x['title'] for x in gn.search(f"allintitle: {name} dies", when="6h")['entries']]

    # TODO: This could be more refined - just because an article mentions "x dead" doesn't mean x is dead
    THRESHOLD = 2
    return len(news) > THRESHOLD

print(check_if_dead(""))