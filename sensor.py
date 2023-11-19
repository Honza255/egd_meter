"""
Script stáhne 7 dní starý záznam o generaci a spotřebě elektřiny od EGD

Ve formátu JSON který je možno zpracovat pomocí Home Assistant
EGD má pouze stará data, což je promblém pro HA, který umí nativně
zaznamenávat pouze aktuální data

Příklad výstupu scriptu:
    {
        "error": 0,
        "data": "2023-11-12",
        "ICH1": 21.91,
        "ICH1_size": 24,
        "ISH1": 1.7925000000000002,
        "ISH1_size": 24
    }

EGD OpenApi přiručka – vzdálený přístup
https://portal.distribuce24.cz/download/Uzivatelsky_navod_OpenApi.pdf
"""

# Fill in/Vypln
##################################################
EAN = "xxxxxxxxxxxxxxxxxx"
CLIENT_ID = "xxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxx"
CLIENT_SECRET = "xxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxx"
##################################################

from datetime import datetime, timedelta
import requests
import json

# EGD ma velke zpozdeni a nebo nemaji vsechna data pro cely den
# Proto predleva 7 dnu
day_delay = 7
dnes = datetime.now().date()
start = (dnes - timedelta(days=day_delay)).isoformat()
end = (dnes - timedelta(days=day_delay - 1)).isoformat()

# Get Access token
url = "https://idm.distribuce24.cz/oauth/token"
data = {
    "grant_type": "client_credentials",
    "client_id": CLIENT_ID,
    "client_secret": CLIENT_SECRET,
    "scope": "namerena_data_openapi",
}
response = requests.post(url, json=data)
#print(url, data, response, response.status_code, response.content)
access_token = json.loads(response.content)["access_token"]

# Authorization header for data polling
url = "https://data.distribuce24.cz/rest/spotreby"
headers = {
    "Authorization": "Bearer {}".format(access_token),
}

#Hourly electricity consumption - ICH1"
#Hourly electricity generation - ISH1"
profiles = ["ICH1","ISH1"]

#Create egd poll requests
requests_eon = {}
for profile in profiles:
    requests_eon[profile] = {
        "ean": EAN,
        "profile": profile,
        "from": "{}T00:01:00.000Z".format(start),
        "to":   "{}T00:00:00.000Z".format(end),
        "pagestart": 0,
        "pagesize": 24*4
    }

# Set inital values in case of error
total = {"error": 0, "date": start}
for request_eon in requests_eon:
    total[request_eon] = 0
    total['{}_size'.format(request_eon)] = -1

# Get data points and sum for profiles of selected day
for request_eon in requests_eon:
    try:
        response = requests.get(url, headers=headers, params=requests_eon[request_eon])
        #print("\n", url, headers, requests_eon[request_eon], response, response.status_code, response.content)
        response.raise_for_status()  # Raise HTTPError for bad responses
        data = json.loads(response.content)

        # Save all data for given profile
        with open('{}.txt'.format(request_eon), 'w') as file:
            file.write(json.dumps(data, indent=4))

        # Iterate through the data and sum the "value" field
        for entry in data:
            total['{}_size'.format(request_eon)] = entry['total']
            assert(entry['total'] in {24, 24*4})
            for timestamp_data in entry['data']:
                total[request_eon] += timestamp_data['value']
                
    except Exception as e:
        #print("Fail:", e)
        total["error"] = 1

print(json.dumps(total, indent=4))
with open('egd_data.json', 'w') as file:
    file.write(json.dumps(total, indent=4))

## Available profiles
#profiles =  json.loads(requests.get(url="https://data.distribuce24.cz/rest/profily", headers=headers).content)
#print(json.dumps(profiles, indent=4))

