import json
import os
import subprocess

config_path = os.path.join(os.path.dirname(__file__), 'config.json')

def load_config():
    with open(config_path, 'r') as file:
        config = json.load(file)
    return config

def save_config(config):
    with open(config_path, 'w') as file:
        json.dump(config, file, indent=4)

def validate_config(config, required_fields):
    for field in required_fields:
        if not config.get(field):
            return False
    return True

def prompt_for_value(field_name, hint):
    while True:
        value = input(f"Enter {field_name} ({hint}): ")
        if value:
            return value
        else:
            print(f"{field_name} is required. Please enter a valid value.")

def set_option(config, script_name):
    required_fields = []
    if script_name == "01_log200_ingest_structured.py":
        required_fields = ["alias", "encounter_id", "logscale_api_token_structured"]
    elif script_name == "02_log200_ingest_raw.py":
        required_fields = ["alias", "encounter_id", "logscale_api_token_raw"]
    elif script_name == "04_log200_case_study.py":
        required_fields = ["alias", "encounter_id", "logscale_api_token_case_study", "city_name", "country_name", "latitude", "longitude", "date_start", "date_end"]
    elif script_name == "05_log200_periodic_fetch.py":
        required_fields = ["alias", "encounter_id", "logscale_api_token_case_study", "city_name", "country_name", "latitude", "longitude", "extreme_field", "high"]
    
    for field in required_fields:
        if not config.get(field):
            config[field] = prompt_for_value(field, "e.g. value or null")
    save_config(config)
    print("Configuration updated.")

def show_options(config, script_name):
    if script_name == "01_log200_ingest_structured.py":
        fields = ["alias", "encounter_id", "logscale_api_token_structured"]
    elif script_name == "02_log200_ingest_raw.py":
        fields = ["alias", "encounter_id", "logscale_api_token_raw"]
    elif script_name == "04_log200_case_study.py":
        fields = ["alias", "encounter_id", "logscale_api_token_case_study", "city_name", "country_name", "latitude", "longitude", "date_start", "date_end"]
    elif script_name == "05_log200_periodic_fetch.py":
        fields = ["alias", "encounter_id", "logscale_api_token_case_study", "city_name", "country_name", "latitude", "longitude", "extreme_field", "high"]
    
    for field in fields:
        print(f"{field}: {config.get(field, 'Not set')}")
            
def run_script(script_name):
    print(f"Running {script_name}...")
    subprocess.run(['python3', os.path.join(os.path.dirname(__file__), script_name)])

def set_cron_job():
    cron_command = "0 * * * * /usr/bin/python3 /home/ec2-user/weather/05_log200_periodic_fetch.py"
    cron_exists = False

    result = subprocess.run(['crontab', '-l'], stdout=subprocess.PIPE, stderr=subprocess.PIPE)
    if result.stdout:
        cron_jobs = result.stdout.decode()
        if cron_command in cron_jobs:
            cron_exists = True

    if not cron_exists:
        with open("temp_cron", "w") as f:
            if result.stdout:
                f.write(result.stdout.decode())
            f.write(cron_command + "\n")
        subprocess.run(['crontab', 'temp_cron'])
        os.remove("temp_cron")
        print("Cron job set to run every hour.")
    else:
        print("Cron job is already set.")

def menu():
    while True:
        print("\nMenu:")
        print("1. Run 01_log200_ingest_structured.py")
        print("2. Run 02_log200_ingest_raw.py")
        print("3. Run 04_log200_case_study.py")
        print("4. Run 05_log200_periodic_fetch.py (Manual Run)")
        print("5. Set Cron Job for 05_log200_periodic_fetch.py")
        print("6. Show Options")
        print("7. Set Options")
        print("8. Exit")
        choice = input("Select an option: ")

        config = load_config()

        if choice == "1":
            set_option(config, "01_log200_ingest_structured.py")
            run_script("01_log200_ingest_structured.py")
        elif choice == "2":
            set_option(config, "02_log200_ingest_raw.py")
            run_script("02_log200_ingest_raw.py")
        elif choice == "3":
            set_option(config, "04_log200_case_study.py")
            run_script("04_log200_case_study.py")
        elif choice == "4":
            set_option(config, "05_log200_periodic_fetch.py")
            run_script("05_log200_periodic_fetch.py")
        elif choice == "5":
            set_cron_job()
        elif choice == "6":
            script_name = input("Enter script name to show options (01, 02, 04, 05): ")
            script_map = {
                "01": "01_log200_ingest_structured.py",
                "02": "02_log200_ingest_raw.py",
                "04": "04_log200_case_study.py",
                "05": "05_log200_periodic_fetch.py"
            }
            if script_name in script_map:
                show_options(config, script_map[script_name])
            else:
                print("Invalid script name.")
        elif choice == "7":
            script_name = input("Enter script name to set options (01, 02, 04, 05): ")
            script_map = {
                "01": "01_log200_ingest_structured.py",
                "02": "02_log200_ingest_raw.py",
                "04": "04_log200_case_study.py",
                "05": "05_log200_periodic_fetch.py"
            }
            if script_name in script_map:
                set_option(config, script_map[script_name])
            else:
                print("Invalid script name.")
        elif choice == "8":
            break
        else:
            print("Invalid choice. Please try again.")

if __name__ == "__main__":
    menu()
