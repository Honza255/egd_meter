ean = "xxxxxxxxxxxxxxxxxx"
client_id = "cccccccccccccccccccccccccccccccc"
client_secret = "vvvvvvvvvvvvvvvvvvvvvvvvvvvvvvvv"

from datetime import datetime, timedelta
import requests
import json

day_delay=4
dnes = datetime.now().date()
start = dnes - timedelta(days=(day_delay))
end = dnes - timedelta(days=(day_delay-1))

dnes = dnes.isoformat()
start = start.isoformat()
end = end.isoformat()

# Get Access token - form
url = "https://idm.distribuce24.cz/oauth/token"
headers = {
    'Content-Type': 'application/json',
}
data = {
    "grant_type": "client_credentials",
    "client_id": client_id,
    "client_secret": client_secret,
    "scope": "namerena_data_openapi",
}

# Get Access token - action
response = requests.post(url, json=data)
#print(response)
#print(response.content)
access_token = json.loads(response.content)["access_token"]

# Get total consumption/generation - request form + sccess header
url = "https://data.distribuce24.cz/rest/spotreby"
headers = {
    "Authorization": f"Bearer {access_token}",
}
requests_eon = {
    "consumption": {
        "ean": ean,
        "profile": "ICH1",
        "from": f"{start}T00:01:00.000Z",
        "to":   f"{end}T00:00:00.000Z",
        "PageStart": 0,
        "PageSize": 24
    },
    "generation": {
        "ean": ean,
        "profile": "ISH1",
        "from": f"{start}T00:01:00.000Z",
        "to":   f"{end}T00:00:00.000Z",
        "PageStart": 0,
        "PageSize": 24,
    }
}

# Get total consumption/generation - action
chyba = 0
total = {"consumption":0, "generation":0, "error":0, "consumption_size:":-1, "generation_size:":-1}  
for request_eon in requests_eon:

    try:
        response_cons = requests.get(url, headers=headers, params=requests_eon[request_eon])
        #print("Request completed with status code:", response_cons.status_code)
        #print("Content:", response_cons.content)
        data = json.loads(response_cons.content)

        # Save
        with open(f'{request_eon}.txt', 'w') as file:
            file.write(json.dumps(data, indent=4))

        # Iterate through the data and sum the "value" field
        for entry in data:
            if(request_eon=="consumption"):
                total["consumption_size"] = entry['total']
            if(request_eon=="generation"):
                total["generation_size"] = entry['total']
                
            assert(entry['total'] == 24)
            
            for timestamp_data in entry['data']:
                total[request_eon] += timestamp_data['value']
    except:
        total[request_eon] = 0
        total["error"] = 1

print(json.dumps(total))
with open('egd_data.json', 'w') as file:
    file.write(json.dumps(total, indent=4))

## Available profiles
#profiles =  json.loads(requests.get(url="https://data.distribuce24.cz/rest/profily", headers=headers).content)
#print(json.dumps(profiles, indent=4))
