import requests

api_url = ''
headers = {
    'Content-Type': 'application/json',
    'Accept': 'application/json',
    'Authorization': 'Bearer '
}

try:
    response = requests.get(api_url, headers=headers)
    if response.status_code == 200:
        print("status code:", response.status_code)
        
        data = response.json()

        if 'data' in data:  # i know data sting exists within the response but i have to do an if statement because i kept getting an error 
            for item in data['data']:  # iterates through items in data string
                device_id = item['id'] # extracts device_id which is named id in data string
                device_name = item['name'] # extracts device_name which is named name in data string
                print(f'Device ID: {device_id}, Device Name: {device_name}')
        else:
            print("data is not present in json response")
    else:
        print("statuse:", response.status_code)
        print("error response:", response.text)
except requests.exceptions.RequestException as e:
    print("request has failed", e)
