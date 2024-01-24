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
    'Authorization': 'Bearer eyJhbGciOiJIUzI1NiIsInR5cCI6IkpXVCJ9.eyJJbnRlcm5hbENvbnRhY3RJZCI6IjMzNjQiLCJDb21wYW55SWQiOiI3NzQiLCJJZGVudCI6ImNob29zZTJyZW50IiwiQnVpbGRVbmlxdWVJZCI6IjQ1MDEiLCJSZWZyZXNoVG9rZW4iOiJWSTNkdG54cjVDdVJiNkhmSFlnREFnPT0iLCJPZmZpY2VBY2Nlc3NJZHMiOiI0NTMsNDU0IiwibmJmIjoxNzA1NjcxMTMyLCJleHAiOjE3MDU3NTc1MzIsImlhdCI6MTcwNTY3MTEzMiwiaXNzIjoiaWVsaWdodG5pbmcubmV0In0.E0Vv4m7zWnDiS7ZWYejUvLjjhzCMP2u51XoSbr_zYmY',
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
