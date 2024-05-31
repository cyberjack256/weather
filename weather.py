#!/bin/python3
import requests
import json
import argparse
from datetime import datetime, timedelta
import random

# Function to fetch weather data from OpenWeatherMap API
def fetch_weather(api_key, lat, lon, date):
    url = f"http://api.openweathermap.org/data/2.5/onecall/timemachine?lat={lat}&lon={lon}&dt={int(date.timestamp())}&appid={api_key}&units=imperial"
    response = requests.get(url)
    return response.json()

# Function to send data to LogScale
def send_to_logscale(logscale_api_url, logscale_api_token, data):
    headers = {
        "Authorization": f"Bearer {logscale_api_token}",
        "Content-Type": "application/json"
    }
    response = requests.post(logscale_api_url, json=data, headers=headers)
    return response.status_code, response.text

# Parse command-line arguments
parser = argparse.ArgumentParser(description="Weather data collection script")
parser.add_argument("event_id", help="Falcon encounter ID")
parser.add_argument("logscale_api_token", help="LogScale API token")
args = parser.parse_args()

# LogScale API URL
logscale_api_url = 'https://cloud.us.humio.com/api/v1/ingest/json'

# API key for OpenWeatherMap API
api_key = 'REPLACEME'

# Locations dictionary with latitudes, longitudes, and their respective timezones
locations = {
    'Oymyakon, Russia': {'lat': 63.4641, 'lon': 142.7737, 'timezone': 'Asia/Kamchatka'},  # Asia/Kamchatka
    'Fairbanks, Alaska': {'lat': 64.8378, 'lon': -147.7164, 'timezone': 'America/Anchorage'},  # America/Anchorage
    'Death Valley, California': {'lat': 36.2468, 'lon': -116.8143, 'timezone': 'America/Los_Angeles'},  # America/Los_Angeles
    'Cherrapunji, India': {'lat': 25.30005, 'lon': 91.5822, 'timezone': 'Asia/Kolkata'},  # Asia/Kolkata
    'Ushuaia, Argentina': {'lat': -54.8019, 'lon': -68.3030, 'timezone': 'America/Argentina/Ushuaia'},  # America/Argentina/Ushuaia
    'Nuuk, Greenland': {'lat': 64.1835, 'lon': -51.7216, 'timezone': 'America/Godthab'},  # America/Godthab
    'Queenstown, New Zealand': {'lat': -45.0312, 'lon': 168.6626, 'timezone': 'Pacific/Auckland'},  # Pacific/Auckland
    'Timbuktu, Mali': {'lat': 16.7735, 'lon': -3.0074, 'timezone': 'Africa/Bamako'}  # Africa/Bamako
}

# Function to generate random dates over the past two years across all seasons
def generate_random_dates(num_dates):
    end_date = datetime.now()
    start_date = end_date - timedelta(days=730)
    dates = [start_date + (end_date - start_date) * random.random() for _ in range(num_dates)]
    return dates

# Fetch and send weather data for random dates over the past two years
for name, coords in locations.items():
    random_dates = generate_random_dates(4 * 4)  # 4 dates per season for 2 years
    for date in random_dates:
        weather_data = fetch_weather(api_key, coords['lat'], coords['lon'], date)
        weather_data['event_id'] = args.event_id
        weather_data['location'] = name
        weather_data['date'] = date.strftime("%Y-%m-%d")
        weather_data['timezone'] = coords['timezone']
        status_code, response_text = send_to_logscale(logscale_api_url, args.logscale_api_token, weather_data)
        print(f"Weather data for {name} on {date.strftime('%Y-%m-%d')}: {weather_data}")
        print(f"Status Code: {status_code}, Response: {response_text}")

# Fetch hourly weather data for the next day after the class
for name, coords in locations.items():
    for hour in range(24):
        date = datetime.now() + timedelta(hours=hour)
        weather_data = fetch_weather(api_key, coords['lat'], coords['lon'], date)
        weather_data['event_id'] = args.event_id
        weather_data['location'] = name
        weather_data['datetime'] = date.strftime("%Y-%m-%d %H:%M:%S")
        weather_data['timezone'] = coords['timezone']
        status_code, response_text = send_to_logscale(logscale_api_url, args.logscale_api_token, weather_data)
        print(f"Hourly weather data for {name} on {date.strftime('%Y-%m-%d %H:%M:%S')}: {weather_data}")
        print(f"Status Code: {status_code}, Response: {response_text}")
