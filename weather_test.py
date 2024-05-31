#!/bin/python3
import requests
import json
import argparse
from datetime import datetime, timedelta

# Function to fetch current weather data from OpenWeatherMap One Call API
def fetch_current_weather(api_key, lat, lon):
    url = f"http://api.openweathermap.org/data/3.0/onecall?lat={lat}&lon={lon}&exclude=minutely,daily,alerts&appid={api_key}&units=imperial"
    response = requests.get(url)
    return response.json()

# Function to fetch air pollution data from OpenWeatherMap API
def fetch_air_pollution(api_key, lat, lon):
    url = f"http://api.openweathermap.org/data/2.5/air_pollution?lat={lat}&lon={lon}&appid={api_key}"
    response = requests.get(url)
    return response.json()

# Function to fetch historical weather data from OpenWeatherMap One Call API
def fetch_historical_weather(api_key, lat, lon, date):
    url = f"http://api.openweathermap.org/data/3.0/onecall/timemachine?lat={lat}&lon={lon}&dt={int(date.timestamp())}&appid={api_key}&units=imperial"
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

# Fetch air pollution data
air_pollution_data = fetch_air_pollution(api_key, test_location['lat'], test_location['lon'])

# Fetch historical weather data for the same hour each day for the last 30 days
historical_weather_data = []
for day in range(31):
    date = datetime.now() - timedelta(days=day)
    historical_weather_data.append(fetch_historical_weather(api_key, test_location['lat'], test_location['lon'], date))

# Debugging: Print the API responses to understand their structures
print("Current Weather API Response:", json.dumps(current_weather_data, indent=4))
print("Air Pollution API Response:", json.dumps(air_pollution_data, indent=4))
for idx, data in enumerate(historical_weather_data):
    print(f"Historical Weather API Response for {datetime.now() - timedelta(days=idx)}:", json.dumps(data, indent=4))

# Convert current weather data to ECS compliant fields
ecs_current_weather_data = {
    "@timestamp": datetime.utcfromtimestamp(current_weather_data['current']['dt']).strftime("%Y-%m-%dT%H:%M:%S.%fZ"),  # UTC timestamp
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
        "temperature": current_weather_data['current']['temp'],
        "feels_like": current_weather_data['current']['feels_like'],
        "pressure": current_weather_data['current']['pressure'],
        "humidity": current_weather_data['current']['humidity'],
        "dew_point": current_weather_data['current']['dew_point'],
        "uvi": current_weather_data['current']['uvi'],
        "clouds": current_weather_data['current']['clouds'],
        "visibility": current_weather_data['current']['visibility'],
        "wind_speed": current_weather_data['current']['wind_speed'],
        "wind_deg": current_weather_data['current']['wind_deg'],
        "wind_gust": current_weather_data['current'].get('wind_gust', None),
        "weather": current_weather_data['current']['weather'][0]['description'],
        "rain": current_weather_data['current'].get('rain', {}).get('1h', None),
        "snow": current_weather_data['current'].get('snow', {}).get('1h', None)
    },
    "tags": ["weather_data", test_location['timezone']]
}

# Send the current weather data to LogScale
status_code, response_text = send_to_logscale(logscale_api_url, args.logscale_api_token, ecs_current_weather_data)
print(f"Current weather data for {test_location['name']}: {ecs_current_weather_data}")
print(f"Status Code: {status_code}, Response: {response_text}")

# Convert air pollution data to ECS compliant fields
ecs_air_pollution_data = {
    "@timestamp": datetime.utcfromtimestamp(air_pollution_data['list'][0]['dt']).strftime("%Y-%m-%dT%H:%M:%S.%fZ"),  # UTC timestamp
    "event": {
        "id": args.event_id,
        "created": datetime.now().strftime("%Y-%m-%dT%H:%M:%S.%fZ"),
        "kind": "event",
        "category": ["environment"],
        "type": ["info"]
    },
    "observer": {
        "type": "air_quality_station",
        "name": "OpenWeatherMap"
    },
    "geo": {
        "location": {
            "lat": test_location['lat'],
            "lon": test_location['lon']
        },
        "name": test_location['name']
    },
    "air_quality": {
        "aqi": air_pollution_data['list'][0]['main']['aqi'],
        "components": air_pollution_data['list'][0]['components']
    },
    "tags": ["air_pollution_data", test_location['timezone']]
}

# Send the air pollution data to LogScale
status_code, response_text = send_to_logscale(logscale_api_url, args.logscale_api_token, ecs_air_pollution_data)
print(f"Air pollution data for {test_location['name']}: {ecs_air_pollution_data}")
print(f"Status Code: {status_code}, Response: {response_text}")

# Convert historical weather data to ECS compliant fields and send to LogScale
for day, historical_data in enumerate(historical_weather_data):
    for hourly_data in historical_data['hourly']:
        if datetime.utcfromtimestamp(hourly_data['dt']).hour == datetime.now().hour:
            ecs_historical_weather_data = {
                "@timestamp": datetime.utcfromtimestamp(hourly_data['dt']).strftime("%Y-%m-%dT%H:%M:%S.%fZ"),  # UTC timestamp
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
                    "temperature": hourly_data['temp'],
                    "feels_like": hourly_data['feels_like'],
                    "pressure": hourly_data['pressure'],
                    "humidity": hourly_data['humidity'],
                    "dew_point": hourly_data['dew_point'],
                    "uvi": hourly_data['uvi'],
                    "clouds": hourly_data['clouds'],
                    "visibility": hourly_data.get('visibility', None),
                    "wind_speed": hourly_data['wind_speed'],
                    "wind_deg": hourly_data['wind_deg'],
                    "wind_gust": hourly_data.get('wind_gust', None),
                    "weather": hourly_data['weather'][0]['description'],
                    "rain": hourly_data.get('rain', {}).get('1h', None),
                    "snow": hourly_data.get('snow', {}).get('1h', None)
                },
                "tags": ["historical_weather_data", test_location['timezone']]
            }

            # Send the historical weather data to LogScale
            status_code, response_text = send_to_logscale(logscale_api_url, args.logscale_api_token, ecs_historical_weather_data)
            print(f"Historical weather data for {test_location['name']} on {datetime.utcfromtimestamp(hourly_data['dt']).strftime('%Y-%m-%d %H:%M:%S')}: {ecs_historical_weather_data}")
            print(f"Status Code: {status_code}, Response: {response_text}")
