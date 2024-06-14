import json
import os
import requests
from datetime import datetime
import logging

# Configure logging
logging.basicConfig(level=logging.DEBUG)

# Set the base directory relative to the script location
base_dir = os.path.dirname(__file__)

# Load and validate the configuration
def load_config():
    config_path = os.path.join(base_dir, 'config.json')
    with open(config_path, 'r') as file:
        config = json.load(file)
    if any(value == "REPLACEME" for value in config.values()):
        raise ValueError("Please replace all 'REPLACEME' fields in the config file.")
    return config

# Send data to LogScale
def send_to_logscale(logscale_api_url, logscale_api_token, data):
    headers = {
        "Authorization": f"Bearer {logscale_api_token}",
        "Content-Type": "application/json"
    }
    response = requests.post(logscale_api_url, json=data, headers=headers)
    logging.debug(f"Response from LogScale: Status Code: {response.status_code}, Response: {response.text}")
    return response.status_code, response.text

# Main function
def main():
    try:
        logging.debug("Starting script...")
        config = load_config()
        logging.debug(f"Config loaded: {config}")
        
        # Example log data
        example_data = [
            {
                "tags": {
                    "host": "weatherhost",
                    "source": "weatherdata"
                },
                "events": [
                    {
                        "timestamp": "2024-06-14T12:00:00+00:00",
                        "attributes": {
                            "observer.id": config["encounter_id"],
                            "observer.alias": config["alias"],
                            "weather.temperature": 25.6,
                            "weather.humidity": "60%",
                            "weather.precipitation": "0mm",
                            "weather.wind_speed": "15km/h"
                        }
                    }
                ]
            }
        ]

        # Send log data to LogScale
        status_code, response_text = send_to_logscale(
            config['logscale_api_url'],
            config['logscale_api_token_structured'],
            example_data
        )

        print(f"Status Code: {status_code}, Response: {response_text}")
        
        # Provide guidance to students
        print("\n### Important: Read the Output ###\n")
        print("Sample Log Entry Sent:")
        print(json.dumps(example_data, indent=4))
        print("\nLog Entry Structure:")
        print("The log entry includes fields such as 'timestamp', 'observer.id', 'observer.alias', 'weather.temperature', 'weather.humidity', 'weather.precipitation', and 'weather.wind_speed'.")
        print("\nUsing the LogScale Structured API:")
        print("The LogScale Structured API is used to ingest structured data directly. This means that the data being sent already has a predefined structure and does not require additional parsing.")
        print("\nSearch Hint:")
        print("To search for your data in LogScale, use the following query in your sandbox view:")
        print(f'observer.id = "{config["encounter_id"]}" AND observer.alias = "{config["alias"]}"')
        print("Make sure to adjust the time range to include the time when the logs were sent (e.g., '1m', '7d', etc.).")
        
    except Exception as e:
        logging.error(e)

if __name__ == "__main__":
    main()
