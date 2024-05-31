#!/bin/python3
import requests
import json
import argparse
from datetime import datetime

# Function to fetch current weather data from OpenWeatherMap API
def fetch_current_weather(api_key, lat, lon):
    url = f"http://api.openweathermap.org/data/2.5/weather?lat={lat}&lon={lon}&appid={api_key}&units=imperial"
    response = requests.get(url)
    return response.json()

# Function to fetch forecast weather data from OpenWeatherMap API
def fetch_forecast_weather(api_key, lat, lon):
    url = f"http://api.openweathermap.org/data/2.5/forecast?lat={lat}&lon={lon}&appid={api_key}&units=imperial"
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
parser = argparse.ArgumentParser(description="Weather data test script")
parser.add_argument("event_id", help="Falcon encounter ID")
parser.add_argument("logscale_api_token", help="LogScale API token")
args = parser.parse_args()

# LogScale API URL
logscale_api_url = 'https://cloud.us.humio.com/api/v1/ingest/json'

# API key for OpenWeatherMap API
api_key = 'REPLACEME'

# Test location (Fairbanks, Alaska) and timezone
test_location = {
    'name': 'Fairbanks, Alaska',
    'lat': 64.8378,
    'lon': -147.7164,
    'timezone': 'America/Anchorage'
}

# Fetch current weather data
current_weather_data = fetch_current_weather(api_key, test_location['lat'], test_location['lon'])

# Fetch forecast weather data
forecast_weather_data = fetch_forecast_weather(api_key, test_location['lat'], test_location['lon'])

# Debugging: Print the API response to understand its structure
print("Current Weather API Response:", json.dumps(current_weather_data, indent=4))
print("Forecast Weather API Response:", json.dumps(forecast_weather_data, indent=4))

# Convert current weather data to ECS compliant fields
ecs_current_weather_data = {
    "@timestamp": datetime.utcfromtimestamp(current_weather_data['dt']).strftime("%Y-%m-%dT%H:%M:%S.%fZ"),  # UTC timestamp
    "event": {
        "id": args.event_id,
        "created": datetime.now().strftime("%Y-%m-%dT%H:%M:%S.%fZ"),
        "kind": "event",
        "category": ["weather"],
        "type": ["info"]
    },
    "observer": {
        "type": "weather_station",
        "name": "OpenWeatherMap"
    },
    "geo": {
        "location": {
            "lat": test_location['lat'],
            "lon": test_location['lon']
        },
        "name": test_location['name']
    },
    "weather": {
        "temperature": current_weather_data['main']['temp'],
        "feels_like": current_weather_data['main']['feels_like'],
        "temp_min": current_weather_data['main']['temp_min'],
        "temp_max": current_weather_data['main']['temp_max'],
        "pressure": current_weather_data['main']['pressure'],
        "sea_level_pressure": current_weather_data['main'].get('sea_level', None),
        "ground_level_pressure": current_weather_data['main'].get('grnd_level', None),
        "humidity": current_weather_data['main']['humidity'],
        "wind": {
            "speed": current_weather_data['wind']['speed'],
            "direction": current_weather_data['wind']['deg'],
            "gust": current_weather_data['wind'].get('gust', None)
        },
        "condition": current_weather_data['weather'][0]['description'],
        "visibility": current_weather_data.get('visibility', None),
        "clouds": current_weather_data['clouds']['all'],
        "rain": current_weather_data.get('rain', {}).get('1h', None),
        "snow": current_weather_data.get('snow', {}).get('1h', None)
    },
    "tags": ["weather_data", test_location['timezone']]
}

# Send the current weather data to LogScale
status_code, response_text = send_to_logscale(logscale_api_url, args.logscale_api_token, ecs_current_weather_data)
print(f"Current weather data for {test_location['name']}: {ecs_current_weather_data}")
print(f"Status Code: {status_code}, Response: {response_text}")

# Convert forecast weather data to ECS compliant fields and send to LogScale
for forecast in forecast_weather_data['list']:
    ecs_forecast_weather_data = {
        "@timestamp": datetime.utcfromtimestamp(forecast['dt']).strftime("%Y-%m-%dT%H:%M:%S.%fZ"),  # UTC timestamp
        "event": {
            "id": args.event_id,
            "created": datetime.now().strftime("%Y-%m-%dT%H:%M:%S.%fZ"),
            "kind": "event",
            "category": ["weather"],
            "type": ["info"]
        },
        "observer": {
            "type": "weather_station",
            "name": "OpenWeatherMap"
        },
        "geo": {
            "location": {
                "lat": test_location['lat'],
                "lon": test_location['lon']
            },
            "name": test_location['name']
        },
        "weather": {
            "temperature": forecast['main']['temp'],
            "feels_like": forecast['main']['feels_like'],
            "temp_min": forecast['main']['temp_min'],
            "temp_max": forecast['main']['temp_max'],
            "pressure": forecast['main']['pressure'],
            "sea_level_pressure": forecast['main'].get('sea_level', None),
            "ground_level_pressure": forecast['main'].get('grnd_level', None),
            "humidity": forecast['main']['humidity'],
            "wind": {
                "speed": forecast['wind']['speed'],
                "direction": forecast['wind']['deg'],
                "gust": forecast['wind'].get('gust', None)
            },
            "condition": forecast['weather'][0]['description'],
            "visibility": forecast.get('visibility', None),
            "clouds": forecast['clouds']['all'],
            "rain": forecast.get('rain', {}).get('3h', None),
            "snow": forecast.get('snow', {}).get('3h', None),
            "pop": forecast.get('pop', None),
            "part_of_day": forecast['sys'].get('pod', None)
        },
        "tags": ["weather_data", test_location['timezone']]
    }

    # Send the forecast weather data to LogScale
    status_code, response_text = send_to_logscale(logscale_api_url, args.logscale_api_token, ecs_forecast_weather_data)
    print(f"Forecast weather data for {test_location['name']} at {datetime.utcfromtimestamp(forecast['dt']).strftime('%Y-%m-%d %H:%M:%S')}: {ecs_forecast_weather_data}")
    print(f"Status Code: {status_code}, Response: {response_text}")
