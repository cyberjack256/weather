import os
import json
import subprocess

config_path = 'config.json'

def load_config():
    with open(config_path, 'r') as file:
        return json.load(file)

def save_config(config):
    with open(config_path, 'w') as file:
        json.dump(config, file, indent=4)

def show_options(config, script_name):
    options = {
        "01_log200_ingest_structured.py": ["alias", "encounter_id", "logscale_api_token_structured"],
        "02_log200_ingest_raw.py": ["alias", "encounter_id", "logscale_api_token_raw"],
        "04_log200_case_study.py": ["alias", "encounter_id", "logscale_api_token_case_study", "city_name", "country_name", "latitude", "longitude", "date_start", "date_end", "units"],
        "05_log200_periodic_fetch.py": ["alias", "encounter_id", "logscale_api_token_case_study", "city_name", "country_name", "latitude", "longitude", "extreme_field", "high"]
    }
    print(f"\nOptions for {script_name}:")
    for option in options[script_name]:
        print(f"{option}: {config.get(option, 'Not Set')}")

def set_option(config, script_name):
    options = {
        "01_log200_ingest_structured.py": ["alias", "encounter_id", "logscale_api_token_structured"],
        "02_log200_ingest_raw.py": ["alias", "encounter_id", "logscale_api_token_raw"],
        "04_log200_case_study.py": ["alias", "encounter_id", "logscale_api_token_case_study", "city_name", "country_name", "latitude", "longitude", "date_start", "date_end", "units"],
        "05_log200_periodic_fetch.py": ["alias", "encounter_id", "logscale_api_token_case_study", "city_name", "country_name", "latitude", "longitude", "extreme_field", "high"]
    }
    for option in options[script_name]:
        value = input(f"Enter {option} (current: {config.get(option, 'Not Set')}): ")
        if value:
            config[option] = value
    save_config(config)

def run_script(script_name):
    subprocess.call(['python3', script_name])

def menu():
    while True:
        print("\nMenu:")
        print("1. Run 01_log200_ingest_structured.py")
        print("2. Run 02_log200_ingest_raw.py")
        print("3. Run 04_log200_case_study.py")
        print("4. Run 05_log200_periodic_fetch.py")
        print("5. Show Options")
        print("6. Set Options")
        print("7. Exit")
        choice = input("Select an option: ")

        config = load_config()

        if choice == "1":
            run_script("01_log200_ingest_structured.py")
        elif choice == "2":
            run_script("02_log200_ingest_raw.py")
        elif choice == "3":
            run_script("04_log200_case_study.py")
        elif choice == "4":
            run_script("05_log200_periodic_fetch.py")
        elif choice == "5":
            script_choice = input("Enter the script number (1-4) to show options: ")
            script_mapping = {
                "1": "01_log200_ingest_structured.py",
                "2": "02_log200_ingest_raw.py",
                "3": "04_log200_case_study.py",
                "4": "05_log200_periodic_fetch.py"
            }
            if script_choice in script_mapping:
                show_options(config, script_mapping[script_choice])
            else:
                print("Invalid script number. Please try again.")
        elif choice == "6":
            script_choice = input("Enter the script number (1-4) to set options: ")
            script_mapping = {
                "1": "01_log200_ingest_structured.py",
                "2": "02_log200_ingest_raw.py",
                "3": "04_log200_case_study.py",
                "4": "05_log200_periodic_fetch.py"
            }
            if script_choice in script_mapping:
                set_option(config, script_mapping[script_choice])
            else:
                print("Invalid script number. Please try again.")
        elif choice == "7":
            break
        else:
            print("Invalid choice. Please try again.")

if __name__ == "__main__":
    menu()
