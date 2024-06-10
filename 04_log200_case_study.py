import requests
import json
import logging
from datetime import datetime, timedelta
from meteostat import Stations, Daily
import pandas as pd
from astral import LocationInfo
from astral.sun import sun
from astral.moon import phase

logging.basicConfig(level=logging.DEBUG)

def load_config():
    with open('config.json', 'r') as file:
        config = json.load(file)
    return config

def get_station(latitude, longitude):
    stations = Stations()
    nearby_stations = stations.nearby(latitude, longitude)
    station = nearby_stations.fetch(1)
    return station

def fetch_weather_data(station_id, date_start, date_end):
    data = Daily(station_id, start=date_start, end=date_end)
    data = data.fetch()
    return data

def send_to_logscale(logscale_api_url, logscale_api_token, data):
    headers = {
        "Authorization": f"Bearer {logscale_api_token}",
        "Content-Type": "application/json"
    }
    response = requests.post(logscale_api_url, json=data, headers=headers, verify=False)  # Disabling SSL verification for quick testing
    return response.status_code, response.text

def main():
    try:
        config = load_config()
        latitude = float(config['latitude'])
        longitude = float(config['longitude'])
        date_start = datetime.strptime(config['date_start'], '%Y-%m-%d')
        date_end = datetime.strptime(config['date_end'], '%Y-%m-%d')

        station = get_station(latitude, longitude)
        if station.empty:
            raise ValueError("No weather station found near the specified location.")

        station_id = station.index[0]
        weather_data = fetch_weather_data(station_id, date_start, date_end)
        
        # Log data for debugging
        logging.debug(f"Weather data fetched: {weather_data}")

        logscale_api_url = config['logscale_api_url']
        logscale_api_token = config['logscale_api_token_case_study']
        
        structured_data = [{
            "tags": {
                "host": "weatherhost",
                "source": "weatherdata"
            },
            "events": weather_data.to_dict(orient='records')
        }]
        
        status_code, response_text = send_to_logscale(logscale_api_url, logscale_api_token, structured_data)
        logging.debug(f"Status Code: {status_code}, Response: {response_text}")
        print(f"Status Code: {status_code}, Response: {response_text}")
    except Exception as e:
        logging.error(e)
        print(e)

if __name__ == "__main__":
    main()