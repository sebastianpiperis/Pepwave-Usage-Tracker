from flask import Flask, render_template, request
import pandas as pd # used to parse excel file
import requests
from datetime import datetime, timedelta
from dotenv import load_dotenv
from pepwavetoken import fetch_token



load_dotenv() #calls env
app = Flask(__name__) # creates a flask app instance in order to create routes for the app





# excel variables 
file_path = '/home/pipe/projects/cellularUsage/script/deviceID.xlsx'
device_data_df = pd.read_excel(file_path, skiprows=3, usecols=["device_id", "device_name"]) # reads excel file using pandas 
device_data_df['device_id'] = device_data_df['device_id'].astype(str) # converts data in device_id column into a string because excel interprets IDs as numbers
device_name_to_id = dict(zip(device_data_df['device_id'], device_data_df['device_name'])) # creates dictionary from device data df dataframe, and zip pairs device idwith device name
all_device_ids = ','.join(device_name_to_id.keys()) # joins all device ids into one string in the dictionary to use in my api call to fetch data -
# - since that api call retrieves data for singular devices






@app.route('/', methods=['GET', 'POST'])
def index():

    token_error = False
    search_submitted = False
    device_data = None
    api_error = None
    start_date = None
    end_date = None


    if request.method == 'POST':
        search_submitted = True
        start_date = request.form['start_date']
        end_date = request.form['end_date']

        token = fetch_token()
        if token is None:
            token_error = True
        else:
            response = fetch_device_data(start_date, end_date, token)
            if isinstance(response, dict) and 'error' in response:
                api_error = response['error']
            else:
                device_data = response

    return render_template('index.html', devices=device_data, start_date=start_date, end_date=end_date, search_submitted=search_submitted, token_error=token_error, api_error=api_error)

    



def fetch_device_data(start_date_str, end_date_str, token):
    # start and end_date these functions iterate over each day, then it checks if device ID is present in dictionary. if it is not -
    # - present it means its the first time this devices data is being processed for that date range. In that case, it will create a new entry in the dictionary.
    # if present, it processes data for each day and updates the data accordingly 
    start_date = datetime.strptime(start_date_str, '%Y-%m-%d') - timedelta(days=1) # subtracts day  
    end_date = datetime.strptime(end_date_str, '%Y-%m-%d') - timedelta(days=1) # subtracts day so that the end date can be set to the exact date the user inputs
    devices_data = {} 

    while start_date <= end_date:
        formatted_date = start_date.strftime('%Y-%m-%d') + "T00:00:01"
        api_url = f'api_url'
        headers = {
                    'Authorization': f'Bearer {token}', 
                    'Content-Type': 'application/json', 
                    'Accept': 'application/json',
                }

        try:
            response = requests.get(api_url, headers=headers) 

            if response.status_code != 200: 
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
    return prepare_display_data(devices_data)
    
    

def prepare_display_data(devices_data):
    # processes devices_data dictionary to prepare it for display
    display_data = []
    
    # filtering conditions in this for loop for displaying data 
    for device_id, data in devices_data.items():
        total_gb = round(data['total_up'] + data['total_down'], 2)
        if total_gb >= 3.0: 
            display_data.append((data['name'], total_gb))

    display_data.sort(key=lambda x: x[1], reverse=True) # sorts list in descending order 
    return display_data #returns sorted list 


