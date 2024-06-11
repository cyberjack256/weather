import json
import random
from datetime import datetime, timedelta
import requests
import logging

# Set up logging
logging.basicConfig(level=logging.DEBUG)

# Set the base directory relative to the script location
base_dir = os.path.dirname(__file__)

def load_config():
    """
    Load and validate the configuration from the config.json file.
    Returns:
        Dict[str, str]: The loaded configuration.
    """
    config_path = os.path.join(base_dir, 'config.json')
    try:
        with open(config_path, 'r') as file:
            config = json.load(file)
    except FileNotFoundError:
        logging.error("Configuration file not found.")
        raise
    except json.JSONDecodeError:
        logging.error("Error decoding JSON from the configuration file.")
        raise

    if any(value == "REPLACEME" for value in config.values()):
        raise ValueError("Please replace all 'REPLACEME' fields in the config file.")

    return config

def generate_raw_log(encounter_id, alias, units):
    """
    Generate a raw log message with random weather data.
    Args:
        encounter_id (str): The encounter ID.
        alias (str): The alias.
        units (str): The units of measurement, either 'imperial' or 'metric'.
    Returns:
        str: The generated raw log message.
    """
    timestamp = (datetime.utcnow() - timedelta(minutes=random.randint(1, 5))).isoformat() + "Z"
    
    if units == "imperial":
        temperature = random.randint(14, 95)  # °F
        wind_speed = random.randint(0, 62)  # mph
    else:
        temperature = random.randint(-10, 35)  # °C
        wind_speed = random.randint(0, 100)  # km/h

    humidity = random.randint(20, 90)  # %
    precipitation = random.choice([0, 1, 2, 5, 10, 20])  # mm

    raw_log = f"[{timestamp}] Temp: {temperature}{units}, Humidity: {humidity}%, Precipitation: {precipitation}mm, Wind Speed: {wind_speed}{units}, Encounter ID: {encounter_id}, Alias: {alias}"
    
    return raw_log

def send_to_logscale(logscale_api_url, logscale_api_token, raw_log):
    """
    Send raw log data to LogScale.
    Args:
        logscale_api_url (str): The LogScale API URL.
        logscale_api_token (str): The LogScale API token.
        raw_log (str): The raw log message.
    Returns:
        Tuple[int, str]: The HTTP status code and response text.
    """
    logging.info("Sending raw log data to LogScale...")
    headers = {
        "Authorization": f"Bearer {logscale_api_token}",
        "Content-Type": "text/plain"
    }
    try:
        response = requests.post(logscale_api_url, data=raw_log, headers=headers)
        response.raise_for_status()
        logging.info(f"Response from LogScale: Status Code: {response.status_code}, Response: {response.text}")
        return response.status_code, response.text
    except requests.RequestException as e:
        logging.error(f"Failed to send raw log data to LogScale: {e}")
        raise

def main():
    """Main function to load configuration, generate raw logs, and send them to LogScale."""
    try:
        config = load_config()
        logscale_api_url = config['logscale_api_url'].replace("humio-structured", "raw")
        logscale_api_token = config['logscale_api_token_raw']
        encounter_id = config['encounter_id']
        alias = config['alias']
        units = config.get('units', 'metric')

        for _ in range(5):  # Generate 5 log entries
            raw_log = generate_raw_log(encounter_id, alias, units)
            logging.info(f"Generated raw log: {raw_log}")
            status_code, response_text = send_to_logscale(logscale_api_url, logscale_api_token, raw_log)
            logging.info(f"Status Code: {status_code}, Response: {response_text}")
    except Exception as e:
        logging.error("An error occurred: ", exc_info=True)
        print(e)

if __name__ == "__main__":
    main()
