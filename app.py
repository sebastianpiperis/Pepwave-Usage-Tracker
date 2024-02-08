from flask import Flask, render_template, request, session, redirect,  url_for
import pandas as pd # used to parse excel file
import requests
from datetime import datetime, timedelta
from dotenv import load_dotenv
import os
import re
import json



app = Flask(__name__) # creates a flask app instance in order to create routes for the app
app.secret_key = 'SITE_KEY' # gets the app's secret key from env

load_dotenv()


# excel variables 
file_path = '/home/pipe/projects/cellularUsage/script/deviceID.xlsx'
device_data_df = pd.read_excel(file_path, skiprows=3, usecols=["device_id", "device_name"]) # reads excel file using pandas 
device_data_df['device_id'] = device_data_df['device_id'].astype(str) # converts data in device_id column into a string because excel interprets IDs as numbers
device_name_to_id = dict(zip(device_data_df['device_id'], device_data_df['device_name'])) # creates dictionary from device data df dataframe, and zip pairs device idwith device name
all_device_ids = ','.join(device_name_to_id.keys()) # joins all device ids into one string in the dictionary to use in my api call to fetch data -
# - since that api call retrieves data for singular devices



@app.route('/', methods=['GET', 'POST'])
def index():
    global peplink_token_error, search_submitted, device_data, api_error, start_date, end_date, ie_token_error
    peplink_token_error = False
    search_submitted = False
    device_data = None
    api_error = None
    start_date = None
    end_date = None
    ie_token_error = False
    

    if request.method == 'POST':
        search_submitted = True
        start_date = request.form['start_date']
        end_date = request.form['end_date']
        token = fetch_peplink_token()
        accessToken = fetch_ie_token()

        if token and accessToken is None:
            peplink_token_error = True
            ie_token_error = True
        else:
            response = fetch_device_data(start_date, end_date)
            if isinstance(response, dict) and 'error' in response:
                api_error = response['error']
            else:
                device_data = response
    return render_template('index.html', devices=device_data, start_date=start_date, end_date=end_date, search_submitted=search_submitted, peplink_token_error=peplink_token_error, api_error=api_error, ie_token_error=ie_token_error)




@app.route('/logout', methods=['GET', 'POST'])
def logout():
    session.pop('username', None) 
    return redirect(url_for('login'))  # redirects to login page 
    


def fetch_peplink_token(): # this function fetches the data from the env and constantly regenerates access tokens from InControl2
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
        peplinkAccessToken = response.json().get('access_token')
        # Fetch the Peplink token
        return peplinkAccessToken
    else:
        log_message = f"Failed to fetch token. Status Code: {response.status_code}, Response: {response.text}"
        with open('token_fetch_log.txt', 'a') as log_file:  # 'a' opens the file in append mode to preserve existing data (errors can conccur as well)
            log_file.write(f"{datetime.now()}: {log_message}\n")  # writes the current datetime and log message

        return None
    


def fetch_ie_token():
    IDENT = os.getenv('IDENT')
    IE_USERNAME =os.getenv('IE_USERNAME')
    IE_PASSWORD = os.getenv('IE_PASSWORD')

    url = 'https://webapi1.ielightning.net/api/v1/Authentication/GetAccessToken'
    body = {
            'ident': IDENT,
            'username': IE_USERNAME,
            'password': IE_PASSWORD
            }
    
    headers = {'Content-Type': 'application/json'} 
    response = requests.post(url=url, data=json.dumps(body), headers=headers)

    
    if response.status_code == 200:
        ie_token = response.json().get('accessToken')
        # Print the access token for debugging
        #print("IE Access Token:", ie_token)
        return ie_token
        
    else:
        log_message = f"Failed to fetch IE token. Status code:{response.status_code}, Response: {response.text}"
        with open ('token_fetch_log.txt', 'a') as log_file:
            log_file.write(f"{datetime.now()}: {log_message}\n")
        return None




def fetch_device_data(start_date_str, end_date_str):
    # Fetch the Peplink token inside the function
    peplinkAccessToken = fetch_peplink_token()
    if not peplinkAccessToken:
        # print("Failed to fetch Peplink token. Cannot proceed with API calls.")
        return None
    # start and end_date these functions iterate over each day, then it checks if device ID is present in dictionary. if it is not -
    # - present it means its the first time this devices data is being processed for that date range. In that case, it will create a new entry in the dictionary.
    # if present, it processes data for each day and updates the data accordingly 
    start_date = datetime.strptime(start_date_str, '%Y-%m-%d') - timedelta(days=1) # subtracts day  
    end_date = datetime.strptime(end_date_str, '%Y-%m-%d') - timedelta(days=1) # subtracts day so that the end date can be set to the exact date the user inputs
    # Assuming start_date_str and end_date_str are defined elsewhere in your script
    devices_data = {} 

    while start_date <= end_date:
        print(f"Processing date: {start_date}")
        formatted_date = start_date.strftime('%Y-%m-%d') + "T00:00:01"
        api_url = f'https://api.ic.peplink.com/rest/o/t00nnt/bandwidth_per_device?type=daily&report_date={formatted_date}&wan_id=2&device_ids={all_device_ids}&include_details=true&show_devices_with_usages_only=true'
        print(f"Using Token Pepwave: '{peplinkAccessToken}'")
        headers = {
                    'Authorization': f'Bearer {peplinkAccessToken}', 
                    'Content-Type': 'application/json', 
                    'Accept': 'application/json',
                }

        try:
            response = requests.get(api_url, headers=headers) # getting data 

            if response.status_code != 200: # this will catch any server, client, network, limitations, parameters, and/or deprication errors in the api call
                return {'error': 'Oops, we have failed to retrieve any device data, please contact IT.', 'status_code': response.status_code}

            daily_data = response.json().get('data', []) # processes data if api call is successful, if not data provides an empty list
            
            for device in daily_data: # iterates through each device entry in daily data, retrieving the device_id from the api and gets assigned device name 
                device_id = str(device.get('device_id', 'Unknown'))
                device_name = device_name_to_id.get(device_id, 'Unknown')
                if device_id not in devices_data:
                    devices_data[device_id] = {'name': device_name, 'total_up': 0, 'total_down': 0}

                for usage in device.get('usages', []): # converts MB to GB and adds download and upload usage
                    up = float(usage.get('up', 0)) / 1024
                    down = float(usage.get('down', 0)) / 1024
                    devices_data[device_id]['total_up'] += up
                    devices_data[device_id]['total_down'] += down

        except requests.RequestException as e: # exception error in the api call
            return {'error': 'Oops, an API exception error has occurred. Please contact IT.', 'exception': str(e)}

        start_date += timedelta(days=1) # increments the start date by one day in each iteration within the loop
    #print(devices_data)
    return prepare_display_data(devices_data)


def fetch_location_name(device_name):
        
        ieAccessToken = fetch_ie_token() # get ie access token from fetch token function
        if not ieAccessToken:
            print("Failed to fetch IE token. Cannot proceed with API calls.")
            return None
    # Check if the current user is an 'admin'
        api_url = f'https://webapi1.ielightning.net/api/v1/Inventory/StockItemsPage/StockItem/GetStockItemByBarCode?barCode={device_name}'
        #print(f"Using token: '{ieAccessToken}'")
        headers = {
            'Authorization': f'Bearer {ieAccessToken}',
            'Content-Type': 'application/json',
            'Accept': 'application/json',
        }
        try:
            response = requests.get(api_url, headers=headers)
            response.raise_for_status()

            data = response.json()
            print(data)
            location_name = data.get('locationName', 'Unknown')
            job_number = location_name
            return location_name[0:12], job_number[6:12]

        except requests.HTTPError as http_err:
            print(f"HTTP error occurred: {http_err}")
            return 'Unknown', 'Unknown'
        except Exception as err:
            print(f"An error occurred: {err}")
            return 'Unknown', 'Unknown'

def prepare_display_data(devices_data):
    # processes devices_data dictionary to prepare it for display
    display_data = []
    #print(devices_data) 
    
    # filtering conditions in this for loop for displaying data 
    for device_id, data in devices_data.items():
        total_gb = round(data['total_up'] + data['total_down'], 2)
        if total_gb >= 3.0:
            # checks if user is an admin before calling fetch_location_name
            location_name, job_number = fetch_location_name( data['name']) # makes argument to call location name function
            print(job_number)
            display_data.append((data['name'], total_gb, location_name, job_number))

    display_data.sort(key=lambda x: x[1], reverse=True) # sorts in ascending in order
    return display_data #returns sorted list 



if __name__ == '__main__':
    app.run(host='0.0.0.0', port=5000, debug=True, threaded=False)