import pandas as pd
import requests
import json


file_path = '/home/pipe/projects/cellularUsage/script/bar_code_data.csv'
csv_data = pd.read_csv(file_path)  # corrected the method name from read.csv to read_csv

# extract the "bar_code" column from the DataFrame and convert it to a list
barcode_ids = csv_data["bar_code"].tolist()

# API base URL
api_base_url = 'https://webapi1.ielightning.net/api/v1/Inventory/StockItemsPage/StockItem/GetStockItemByBarCode?barCode={}'

# corrected indentation for the 'headers' dictionary
headers = {
    'Authorization': 'Bearer ',
    'Content-Type': 'application/json',
    'Accept': 'application/json',
}

# create an empty list to store location data
locations = []

# make API requests for each barcode ID
for barcode_id in barcode_ids:

    api_url = api_base_url.format(barcode_id)
    response = requests.get(api_url)
    data = response.json()

    if "location" in data:
        location = data["location"]
        locations.append(location)

# print locations ie. miami warehouse or on a job 
print(locations)
