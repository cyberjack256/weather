import random
import json
import time
from datetime import datetime
import logging
from typing import List, Dict

# Set up logging
logging.basicConfig(level=logging.DEBUG)

def load_config() -> Dict[str, str]:
    """Load and validate the configuration from the config.json file."""
    config_path = 'config.json'
    try:
        with open(config_path, 'r') as file:
            config = json.load(file)
    except FileNotFoundError:
        logging.error("Configuration file not found.")
        raise
    except json.JSONDecodeError:
        logging.error("Error decoding JSON from the configuration file.")
        raise

    required_keys = ['encounter_id']
    for key in required_keys:
        if key not in config or config[key] == "REPLACEME":
            raise ValueError(f"Please replace all 'REPLACEME' fields in the config file. Missing: {key}")

    return config

def generate_random_data(min_val: float, max_val: float) -> float:
    """Generate random float value within the specified range."""
    return round(random.uniform(min_val, max_val), 2)

def generate_atmospheric_event(encounter_id: str, units: str) -> str:
    """Generate a single atmospheric event log entry."""
    timestamp = (datetime.now()).isoformat() + 'Z'
    
    pm10 = generate_random_data(0, 150)
    pm2_5 = generate_random_data(0, 100)
    no2 = generate_random_data(0, 150)
    so2 = generate_random_data(0, 100)
    co = generate_random_data(0, 50)
    o3 = generate_random_data(0, 100)
    aqi = random.randint(0, 500)

    message = f"Atmospheric data recorded at {timestamp}. PM10: {pm10} µg/m³, PM2.5: {pm2_5} µg/m³, NO2: {no2} µg/m³, SO2: {so2} µg/m³, CO: {co} ppm, O3: {o3} µg/m³, AQI: {aqi}."
    
    abnormal_conditions = []
    if pm10 > 50:
        abnormal_conditions.append(f"PM10 level of {pm10} µg/m³ is high, can cause respiratory issues.")
    if pm2_5 > 35:
        abnormal_conditions.append(f"PM2.5 level of {pm2_5} µg/m³ is high, can penetrate lungs and affect heart.")
    if no2 > 100:
        abnormal_conditions.append(f"NO2 level of {no2} µg/m³ is high, can cause lung inflammation and decrease immunity.")
    if so2 > 20:
        abnormal_conditions.append(f"SO2 level of {so2} µg/m³ is high, can irritate airways and exacerbate asthma.")
    if co > 10:
        abnormal_conditions.append(f"CO level of {co} ppm is high, can cause headache, dizziness, and confusion.")
    if o3 > 70:
        abnormal_conditions.append(f"O3 level of {o3} µg/m³ is high, can cause respiratory issues and decrease lung function.")
    
    if abnormal_conditions:
        message += " Conditions out of normal range. " + " ".join(abnormal_conditions)

    raw_log_line = f"[{timestamp}] \"{pm10} µg/m³\" \"{pm2_5} µg/m³\" \"{no2} µg/m³\" \"{so2} µg/m³\" \"{co} ppm\" \"{o3} µg/m³\" \"{aqi}\" \"{message}\" {encounter_id}\n"

    return raw_log_line

def write_to_log_file(events: List[str], log_file_path: str):
    """Write the list of events to the specified log file."""
    with open(log_file_path, 'a') as file:
        file.writelines(events)

def main():
    """Main function to load configuration, generate events, and write them to a log file."""
    try:
        config = load_config()
        logging.debug(f"Config loaded: {config}")

        encounter_id = config['encounter_id']
        units = config.get('units', 'metric')
        log_file_path = 'atmospheric_data.log'

        start_time = datetime.now()
        while (datetime.now() - start_time).total_seconds() < 900:  # Run for 15 minutes
            atmospheric_event = generate_atmospheric_event(encounter_id, units)
            write_to_log_file([atmospheric_event], log_file_path)
            logging.debug(f"Data written to {log_file_path}: {atmospheric_event}")
            time.sleep(random.randint(60, 300))  # Sleep between 1 and 5 minutes

    except Exception as e:
        logging.error("An error occurred: ", exc_info=True)

if __name__ == "__main__":
    from multiprocessing import Process
    p = Process(target=main)
    p.start()
    p.join()
