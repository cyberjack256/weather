#!/bin/python3
import requests
import json
import argparse
from datetime import datetime

# Function to fetch current weather data from OpenWeatherMap One Call API
def fetch_current_weather(api_key, lat, lon):
    url = f"https://api.openweathermap.org/data/3.0/onecall?lat={lat}&lon={lon}&exclude=minutely,hourly,daily,alerts&appid={api_key}&units=imperial"
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

# Test locations with interesting weather events
test_locations = [
    {'name': 'Death Valley, USA', 'lat': 36.2468, 'lon': -116.8143, 'timezone': 'America/Los_Angeles'},
    {'name': 'Mount Everest, Nepal', 'lat': 27.9881, 'lon': 86.9250, 'timezone': 'Asia/Kathmandu'},
    {'name': 'Cherrapunji, India', 'lat': 25.3000, 'lon': 91.7000, 'timezone': 'Asia/Kolkata'},
    {'name': 'Barrow (Utqiagvik), Alaska, USA', 'lat': 71.2906, 'lon': -156.7886, 'timezone': 'America/Anchorage'},
    {'name': 'Amazon Rainforest, Brazil', 'lat': -3.4653, 'lon': -62.2159, 'timezone': 'America/Manaus'}
]

# Fetch current weather data for each location
weather_data = []
for location in test_locations:
    data = fetch_current_weather(api_key, location['lat'], location['lon'])
    weather_data.append({'location': location['name'], 'data': data})

# Debugging: Print the API responses to understand their structures
for entry in weather_data:
    print(f"Weather API Response for {entry['location']}:")
    print(json.dumps(entry['data'], indent=4))

# Convert current weather data to ECS compliant fields and send to LogScale
for entry in weather_data:
    location = entry['location']
    current_weather_data = entry['data']['current']
    ecs_weather_data = {
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
                "lat": entry['data']['lat'],
                "lon": entry['data']['lon']
            },
            "name": location
        },
        "weather": {
            "temperature": current_weather_data['temp'],
            "feels_like": current_weather_data['feels_like'],
            "pressure": current_weather_data['pressure'],
            "humidity": current_weather_data['humidity'],
            "dew_point": current_weather_data['dew_point'],
            "uvi": current_weather_data.get('uvi', None),
            "clouds": current_weather_data['clouds'],
            "visibility": current_weather_data.get('visibility', None),
            "wind_speed": current_weather_data['wind_speed'],
            "wind_deg": current_weather_data['wind_deg'],
            "wind_gust": current_weather_data.get('wind_gust', None),
            "weather": current_weather_data['weather'][0]['description'],
            "rain": current_weather_data.get('rain', {}).get('1h', None),
            "snow": current_weather_data.get('snow', {}).get('1h', None)
        },
        "tags": ["weather_data", location]
    }

    # Send the weather data to LogScale
    status_code, response_text = send_to_logscale(logscale_api_url, args.logscale_api_token, ecs_weather_data)
    print(f"Weather data for {location}: {ecs_weather_data}")
    print(f"Status Code: {status_code}, Response: {response_text}")
