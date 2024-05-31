###Explanation of ECS Fields
## @timestamp: The UTC timestamp of the event.
## event.id: The falcon encounter ID provided as a command-line argument.
## event.created: The timestamp when the event was created.
## event.kind: The type of event, here set to "event".
## event.category: The category of the event, here set to "weather".
## event.type: The type of event, here set to "info".
## observer.type: The type of observer, here set to "weather_station".
## observer.name: The name of the observer, here set to "OpenWeatherMap".
## geo.location: The geographical location (latitude and longitude) of the observation.
## geo.name: The name of the location.
## weather: The weather-specific data including temperature, humidity, pressure, wind speed, wind direction, and condition.
## tags: Tags associated with the event, including the timezone.

#Download the script:
## $ curl -o ecs_weather.py https://raw.githubusercontent.com/cyberjack256/weather/main/weather.py

#Run the script with the necessary parameters:
## $ python3 ecs_weather.py <event_id> <logscale_api_token>


#!/bin/python3
import requests
import json
import argparse
from datetime import datetime, timedelta

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

# Fetch weather data for the current hour
date = datetime.now() - timedelta(hours=1)
weather_data = fetch_weather(api_key, test_location['lat'], test_location['lon'], date)

# Convert weather data to ECS compliant fields
ecs_weather_data = {
    "@timestamp": date.strftime("%Y-%m-%dT%H:%M:%S.%fZ"),  # UTC timestamp
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
        "temperature": weather_data['current']['temp'],
        "humidity": weather_data['current']['humidity'],
        "pressure": weather_data['current']['pressure'],
        "wind": {
            "speed": weather_data['current']['wind_speed'],
            "direction": weather_data['current']['wind_deg']
        },
        "condition": weather_data['current']['weather'][0]['description']
    },
    "tags": ["weather_data", test_location['timezone']]
}

# Send the weather data to LogScale
status_code, response_text = send_to_logscale(logscale_api_url, args.logscale_api_token, ecs_weather_data)

print(f"Weather data for {test_location['name']} on {date.strftime('%Y-%m-%d %H:%M:%S')}: {ecs_weather_data}")
print(f"Status Code: {status_code}, Response: {response_text}")
