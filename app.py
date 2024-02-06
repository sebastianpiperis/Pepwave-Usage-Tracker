from flask import Flask, render_template, request, redirect, url_for, session
from flask_login import LoginManager, UserMixin, login_user, login_required, current_user, logout_user
import pandas as pd # used to parse excel file
import requests
from datetime import datetime, timedelta
from dotenv import load_dotenv
import os
import re



load_dotenv() #calls env
app = Flask(__name__) # creates a flask app instance in order to create routes for the app
app.secret_key = 'SITE_KEY' # gets the app's secret key from env



# excel variables 
file_path = '/home/pipe/projects/cellularUsage/script/deviceID.xlsx'
device_data_df = pd.read_excel(file_path, skiprows=3, usecols=["device_id", "device_name"]) # reads excel file using pandas 
device_data_df['device_id'] = device_data_df['device_id'].astype(str) # converts data in device_id column into a string because excel interprets IDs as numbers
device_name_to_id = dict(zip(device_data_df['device_id'], device_data_df['device_name'])) # creates dictionary from device data df dataframe, and zip pairs device idwith device name
all_device_ids = ','.join(device_name_to_id.keys()) # joins all device ids into one string in the dictionary to use in my api call to fetch data -
# - since that api call retrieves data for singular devices



login_manager = LoginManager()
login_manager.init_app(app)
# user database with username, password, and role
users = {
    'c2r': {'password': 'c2r', 'role': 'user'},
    'admin': {'password': 'c2r', 'role': 'admin'}
}



class User(UserMixin): # flask's user model
    def __init__ (self, username): # initializes the user class, its called when a new instance is created of User
        self.id = username # sets users id to their username
        self.role = users[username]['role'] # based on the users dictionary, it assigns their role 



@login_manager.user_loader
def load_user(user_id):
    return User(user_id)



@app.route('/form_login', methods=['POST', 'GET']) # route can handle both types of request. might just leave it as ['POST']
def login():
    if request.method == 'POST': # checks if the method is a POST request, essentially determines if the user submits the form
        username = request.form['username'] # gets the information user submits for their username credentials
        password = request.form['password'] # gets the information user submits for their password credentials

        # the following if else checks to see if the usrname and password the user submits is in the database, if not it will recieve an error message as shown in line 28
        if username in users and users[username]['password'] == password:
            user = User(username)
            login_user(user)  
            return redirect(url_for('index'))  
        else:
            return render_template('login.html', info='Invalid Credentials. Please contact IT.')
    return render_template("index.html") # renders login page for smooth request 



@app.route('/', methods=['GET', 'POST'])
def index():

    if 'username' not in session:  # Check if the user is authenticated
        return redirect(url_for('login'))

    if request.method == 'POST':
        start_date = request.form['start_date']
        end_date = request.form['end_date']
        token, token_error = fetch_token_with_error_handling()

        if token_error:
            return render_template('index.html', token_error=True)

        device_data, api_error = fetch_device_data_with_error_handling(start_date, end_date, token)

        return render_template('index.html', devices=device_data, start_date=start_date, end_date=end_date, search_submitted=True, api_error=api_error)

    # GET request or initial page load
    return render_template('index.html')



@app.route('/logout', methods=['GET', 'POST'])
def logout():
    logout_user()
    return redirect(url_for('login'))  # redirects to login page 

    


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
        log_message = f"Failed to fetch token. Status Code: {response.status_code}, Response: {response.text}"
        with open('token_fetch_log.txt', 'a') as log_file:  # 'a' opens the file in append mode to preserve existing data (errors can conccur as well)
            log_file.write(f"{datetime.now()}: {log_message}\n")  # writes the current datetime and log message

        return None


def fetch_token_with_error_handling(): # wrapper function for error handling. it calls fetch_token(), then used in index which then determined how the page will render if True
    token = fetch_token()
    if token is None:
        return None, True # if token is None then token_error is True
    return token, False  # if token is returned then token_error is False



def fetch_device_data(start_date_str, end_date_str, token):
    # start and end_date these functions iterate over each day, then it checks if device ID is present in dictionary. if it is not -
    # - present it means its the first time this devices data is being processed for that date range. In that case, it will create a new entry in the dictionary.
    # if present, it processes data for each day and updates the data accordingly 
    start_date = datetime.strptime(start_date_str, '%Y-%m-%d') - timedelta(days=1) # subtracts day  
    end_date = datetime.strptime(end_date_str, '%Y-%m-%d') - timedelta(days=1) # subtracts day so that the end date can be set to the exact date the user inputs
    devices_data = {} 

    while start_date <= end_date:
        print(f"Processing date: {start_date}")
        formatted_date = start_date.strftime('%Y-%m-%d') + "T00:00:01"
        api_url = f'https://api.ic.peplink.com/rest/o/t00nnt/bandwidth_per_device?type=daily&report_date={formatted_date}&wan_id=2&device_ids={all_device_ids}&include_details=true&show_devices_with_usages_only=true'
        headers = {
                    'Authorization': f'Bearer {token}', 
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



def fetch_device_data_with_error_handling(start_date, end_date, token): # wrapper function which serves the same way as fetch_token_with_error_handling() 
    response = fetch_device_data(start_date, end_date, token)
    if isinstance(response, dict) and 'error' in response:
        return None, response['error']  # device data is None and api_error is the error message
    return response, None  # device data is returned and api_error is None



def fetch_location_name(device_name):
    # Check if the current user is an 'admin'
    if 'username' in session and users[session['username']]['role'] == 'admin':
        api_url = f'https://webapi1.ielightning.net/api/v1/Inventory/StockItemsPage/StockItem/GetStockItemByBarCode?barCode={device_name}'
        headers = {
            'Authorization': 'Bearer eyJhbGciOiJIUzI1NiIsInR5cCI6IkpXVCJ9.eyJJbnRlcm5hbENvbnRhY3RJZCI6IjMzNjQiLCJDb21wYW55SWQiOiI3NzQiLCJJZGVudCI6ImNob29zZTJyZW50IiwiQnVpbGRVbmlxdWVJZCI6IjQ1MDEiLCJSZWZyZXNoVG9rZW4iOiJCaWRvM3g0QnF5ek1pTEN1NENaaTBBPT0iLCJPZmZpY2VBY2Nlc3NJZHMiOiI0NTMsNDU0IiwibmJmIjoxNzA2NzkwMTY1LCJleHAiOjE3MDY4NzY1NjUsImlhdCI6MTcwNjc5MDE2NSwiaXNzIjoiaWVsaWdodG5pbmcubmV0In0.NA-uK0sHTQovuMMFxy8Whj_40oWGkmC5dsXQkG2MVTY',
            'Content-Type': 'application/json',
            'Accept': 'application/json',
        }
        try:
            response = requests.get(api_url, headers=headers)
            response.raise_for_status()

            data = response.json()
            location_name = data.get('locationName', 'Unknown')
            job_number = location_name
            return location_name[0:12], job_number[6:12]

        except requests.HTTPError as http_err:
            print(f"HTTP error occurred: {http_err}")
            return 'Unknown'
        except Exception as err:
            print(f"An error occurred: {err}")
            return 'Unknown'
    else:
        print("Access denied: User does not have permission to access this function.")
        return None, None  # or any appropriate response indicating access is denied


def prepare_display_data(devices_data):
    # processes devices_data dictionary to prepare it for display
    display_data = []
    #print(devices_data) 
    
    # filtering conditions in this for loop for displaying data 
    for device_id, data in devices_data.items():
        total_gb = round(data['total_up'] + data['total_down'], 2)
        if total_gb >= 3.0:
            # checks if user is an admin before calling fetch_location_name
            if 'username' in session and users[session['username']]['role'] == 'admin':
                location_name, job_number = fetch_location_name(data['name'])
                if location_name is not None and job_number is not None:
                    display_data.append((data['name'], total_gb, location_name, job_number))
            else:
                # non admin user roles can only see this information 
                display_data.append((data['name'], total_gb))

    display_data.sort(key=lambda x: x[1], reverse=True) # sorts in ascending in order
    return display_data #returns sorted list 






if __name__ == '__main__':
    app.run(host='0.0.0.0', port=5000, debug=True, threaded=False)