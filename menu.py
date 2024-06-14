import os
import json

# Set the base directory relative to the script location
base_dir = os.path.dirname(__file__)
config_path = os.path.join(base_dir, 'config.json')

def load_config():
    with open(config_path, 'r') as file:
        return json.load(file)

def save_config(config):
    with open(config_path, 'w') as file:
        json.dump(config, file, indent=4)

def print_header():
    print("\n" + "="*40)
    print("     WELCOME TO LOGSCALE SETUP MENU")
    print("="*40)

def show_options(required_fields, config):
    print("\nCurrent Configuration Values:")
    for field in required_fields:
        print(f"{field}: {config.get(field, 'Not Set')}")
    print("\n")

def prompt_for_value(prompt, hint):
    value = input(f"{prompt} ({hint}): ")
    return value

def validate_input(prompt, hint, validate_func):
    while True:
        value = prompt_for_value(prompt, hint)
        if validate_func(value):
            return value
        else:
            print(f"Invalid value. Please try again.")

def run_script(script_name, required_fields):
    config = load_config()
    update_needed = False

    while True:
        print_header()
        show_options(required_fields, config)
        print("1. Set a value")
        print("2. Run the script")
        print("3. Exit to main menu")
        choice = input("Select an option: ")

        if choice == '1':
            for field in required_fields:
                if field == "extreme_field":
                    hint = "temperature, wind_speed, precipitation, dew_point"
                elif field == "high":
                    hint = "true or false"
                elif field == "date_start" or field == "date_end":
                    hint = "YYYY-MM-DD"
                else:
                    hint = "Provide a valid value"
                value = validate_input(f"Enter value for {field}", hint, lambda x: bool(x))
                config[field] = value
                update_needed = True
            if update_needed:
                save_config(config)
        elif choice == '2':
            os.system(f"python3 {os.path.join(base_dir, script_name)}")
            break
        elif choice == '3':
            break
        else:
            print("Invalid option. Please try again.")

def main_menu():
    while True:
        print_header()
        print("1. Run 01_log200_ingest_structured")
        print("2. Run 02_log200_ingest_raw")
        print("3. Run 04_log200_case_study")
        print("4. Run 05_log200_periodic_fetch")
        print("5. Exit")
        choice = input("Select an option: ")

        if choice == '1':
            run_script("01_log200_ingest_structured.py", ["alias", "encounter_id", "logscale_api_token_structured"])
        elif choice == '2':
            run_script("02_log200_ingest_raw.py", ["alias", "encounter_id", "logscale_api_token_raw"])
        elif choice == '3':
            run_script("04_log200_case_study.py", ["alias", "encounter_id", "logscale_api_token_case_study"])
        elif choice == '4':
            run_script("05_log200_periodic_fetch.py", ["alias", "encounter_id", "logscale_api_token_periodic", "extreme_field", "high"])
        elif choice == '5':
            print("Exiting... Goodbye!")
            break
        else:
            print("Invalid option. Please try again.")

if __name__ == "__main__":
    main_menu()