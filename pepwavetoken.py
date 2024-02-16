from dotenv import load_dotenv
import requests
import os

load_dotenv() #calls env


def fetch_token(): # this function fetches the data from the env and constantly regenerates access tokens from InControl2
    client_id = os.getenv('client_id')
    client_secret = os.getenv('client_secret')

    data = {
        'client_id': client_id,
        'client_secret': client_secret,
        'grant_type': 'client_credentials'
    }

    url = 'https://api.ic.peplink.com/api/oauth2/token'
    response = requests.post(url, data=data)

    if response.status_code == 200:
        return response.json().get('access_token')
    else:
         return None 

