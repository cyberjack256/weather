#!/bin/python3
import requests
import json
import pytz
from datetime import datetime, timedelta

# Function to fetch weather data from OpenWeatherMap API
def fetch_weather(api_key, lat, lon):
    url = f"http://api.openweathermap.org/data/2.5/weather?lat={lat}&lon={lon}&appid={api_key}&units=imperial"
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

# Function to validate timezone
def is_valid_timezone(timezone):
    return timezone in pytz.all_timezones

# List of acceptable timezones
acceptable_timezones = ["UTC", "America/New_York", "Europe/London", "Asia/Tokyo", "Australia/Sydney"]

# API key for OpenWeatherMap API
api_key = 'REPLACEME'

# Locations dictionary with latitudes and longitudes and their respective timezones
locations = {
    'Oymyakon, Russia': {'lat': 63.4641, 'lon': 142.7737, 'timezone': 'Asia/Kamchatka'}, # Asia/Kamchatka
    'Fairbanks, Alaska': {'lat': 64.8378, 'lon': -147.7164, 'timezone': 'America/Anchorage'}, # America/Anchorage
    'Death Valley, California': {'lat': 36.2468, 'lon': -116.8143, 'timezone': 'America/Los_Angeles'}, # America/Los_Angeles
    'Cherrapunji, India': {'lat': 25.30005, 'lon': 91.5822, 'timezone': 'Asia/Kolkata'}, # Asia/Kolkata
    'Ushuaia, Argentina': {'lat': -54.8019, 'lon': -68.3030, 'timezone': 'America/Argentina/Ushuaia'}, # America/Argentina/Ushuaia
    'Nuuk, Greenland': {'lat': 64.1835, 'lon': -51.7216, 'timezone': 'America/Godthab'}, # America/Godthab
    'Queenstown, New Zealand': {'lat': -45.0312, 'lon': 168.6626, 'timezone': 'Pacific/Auckland'}, # Pacific/Auckland
    'Timbuktu, Mali': {'lat': 16.7735, 'lon': -3.0074, 'timezone': 'Africa/Bamako'} # Africa/Bamako
}

# LogScale API URL and token
logscale_api_url = 'https://cloud.us.humio.com/api/v1/ingest/json'
logscale_api_token = 'REPLACEME'

# Fetch and send weather data for each location
for name, coords in locations.items():
    weather_data = fetch_weather(api_key, coords['lat'], coords['lon'])
    pretty_weather = json.dumps(weather_data)
    # Validate timezone
    if is_valid_timezone(coords['timezone']):
        status_code, response_text = send_to_logscale(logscale_api_url, logscale_api_token, weather_data)
        print(f"Weather data for {name}: {weather_data}")
        print(f"Status Code: {status_code}, Response: {response_text}")
    else:
        print(f"Invalid timezone for location {name}: {coords['timezone']}")
