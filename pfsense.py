import json
import os
import random
import requests
import uuid
from datetime import datetime, timedelta

# Set up logging
import logging
logging.basicConfig(level=logging.DEBUG)

CONFIG_FILE = 'config.json'
REQUIRED_FIELDS = ['logscale_api_token_raw', 'encounter_id', 'alias']
LOGSCALE_URL = 'https://cloud.us.humio.com/api/v1/ingest/raw'

# Load configuration
def load_config():
    if os.path.exists(CONFIG_FILE):
        with open(CONFIG_FILE, 'r') as file:
            return json.load(file)
    return {}

# Validate configuration
def validate_config():
    config = load_config()
    missing_fields = [field for field in REQUIRED_FIELDS if field not in config or config[field] == '']
    if missing_fields:
        print(f"\nMissing required fields: {', '.join(missing_fields)}")
        return False
    return True

def generate_uuid():
    return str(uuid.uuid4())

def generate_ip():
    return f"192.0.{random.randint(0, 255)}.{random.randint(0, 255)}"

def generate_proofpoint_logs(encounter_id, alias):
    """
    Generate fake Proofpoint logs.
    Args:
        encounter_id (str): The encounter ID for the event.
        alias (str): The alias for the event.
    Returns:
        str: The generated raw log entry.
    """
    current_time = datetime.utcnow()
    
    clicks_permitted_log = {
        "campaignId": generate_uuid(),
        "classification": "MALWARE",
        "clickIP": generate_ip(),
        "clickTime": (current_time - timedelta(minutes=random.randint(1, 5))).isoformat() + "Z",
        "GUID": generate_uuid(),
        "id": generate_uuid(),
        "messageID": generate_uuid(),
        "recipient": "bruce.wayne@pharmtech.zz",
        "sender": f"{generate_uuid()}@badguy.zz",
        "senderIP": generate_ip(),
        "threatID": generate_uuid(),
        "threatTime": (current_time - timedelta(minutes=random.randint(1, 5))).isoformat() + "Z",
        "threatURL": f"https://threatinsight.proofpoint.com/#/{generate_uuid()}/threat/u/{generate_uuid()}",
        "threatStatus": "active",
        "url": "http://badguy.zz/",
        "userAgent": "Mozilla/5.0 (Windows NT 6.1; WOW64; rv:27.0) Gecko/20100101 Firefox/27.0"
    }

    messages_blocked_log = {
        "GUID": generate_uuid(),
        "QID": "r2FNwRHF004109",
        "ccAddresses": ["bruce.wayne@university-of-education.zz"],
        "clusterId": "pharmtech_hosted",
        "completelyRewritten": "true",
        "fromAddress": "badguy@evil.zz",
        "headerCC": "\"Bruce Wayne\" <bruce.wayne@university-of-education.zz>",
        "headerFrom": "\"A. Badguy\" <badguy@evil.zz>",
        "headerReplyTo": None,
        "headerTo": "\"Clark Kent\" <clark.kent@pharmtech.zz>; \"Diana Prince\" <diana.prince@pharmtech.zz>",
        "impostorScore": 0,
        "malwareScore": 100,
        "messageID": f"{current_time.strftime('%Y%m%d%H%M%S')}.mail@evil.zz",
        "messageParts": [
            {
                "contentType": "text/plain",
                "disposition": "inline",
                "filename": "text.txt",
                "md5": "008c5926ca861023c1d2a36653fd88e2",
                "oContentType": "text/plain",
                "sandboxStatus": "unsupported",
                "sha256": "85738f8f9a7f1b04b5329c590ebcb9e425925c6d0984089c43a022de4f19c281"
            },
            {
                "contentType": "application/pdf",
                "disposition": "attached",
                "filename": "Invoice for Pharmtech.pdf",
                "md5": "5873c7d37608e0d49bcaa6f32b6c731f",
                "oContentType": "application/pdf",
                "sandboxStatus": "threat",
                "sha256": "2fab740f143fc1aa4c1cd0146d334c5593b1428f6d062b2c406e5efe8abe95ca"
            }
        ],
        "messageTime": current_time.isoformat() + "Z",
        "modulesRun": ["pdr", "sandbox", "spam", "urldefense"],
        "phishScore": 46,
        "policyRoutes": ["default_inbound", "executives"],
        "quarantineFolder": "Attachment Defense",
        "quarantineRule": "module.sandbox.threat",
        "recipient": ["clark.kent@pharmtech.zz", "diana.prince@pharmtech.zz"],
        "replyToAddress": None,
        "sender": f"{generate_uuid()}@evil.zz",
        "senderIP": generate_ip(),
        "spamScore": 4,
        "subject": "Please find a totally safe invoice attached.",
        "threatsInfoMap": [
            {
                "campaignId": generate_uuid(),
                "classification": "MALWARE",
                "threat": "2fab740f143fc1aa4c1cd0146d334c5593b1428f6d062b2c406e5efe8abe95ca",
                "threatId": "2fab740f143fc1aa4c1cd0146d334c5593b1428f6d062b2c406e5efe8abe95ca",
                "threatStatus": "active",
                "threatTime": current_time.isoformat() + "Z",
                "threatType": "ATTACHMENT",
                "threatUrl": f"https://threatinsight.proofpoint.com/#/{generate_uuid()}/threat/u/{generate_uuid()}"
            },
            {
                "campaignId": generate_uuid(),
                "classification": "MALWARE",
                "threat": "badsite.zz",
                "threatId": generate_uuid(),
                "threatTime": (current_time - timedelta(minutes=random.randint(1, 5))).isoformat() + "Z",
                "threatType": "URL",
                "threatUrl": f"https://threatinsight.proofpoint.com/#/{generate_uuid()}/threat/u/{generate_uuid()}"
            }
        ],
        "toAddresses": ["clark.kent@pharmtech.zz", "diana.prince@pharmtech.zz"]
    }

    log_data = {
        "clicksPermitted": [clicks_permitted_log],
        "messagesBlocked": [messages_blocked_log],
        "queryEndTime": current_time.isoformat() + "Z"
    }

    return json.dumps(log_data)

def construct_curl_command(logscale_api_url, logscale_api_token, raw_log):
    """
    Construct a curl command for sending the log to LogScale.
    Args:
        logscale_api_url (str): The LogScale API URL.
        logscale_api_token (str): The LogScale API token.
        raw_log (str): The raw log message.
    Returns:
        str: The constructed curl command.
    """
    curl_command = f"curl {logscale_api_url} -X POST -H 'Authorization: Bearer {logscale_api_token}' -H 'Content-Type: text/plain' --data '{raw_log}'"
    return curl_command

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
    curl_command = construct_curl_command(logscale_api_url, logscale_api_token, raw_log)
    
    print(f"\nExample Log:\n{raw_log}")
    print(f"\nExample Curl Command:\n{curl_command}")
    print("\nBreakdown of Curl Command:")
    print("1. `curl`: Command line tool for transferring data with URLs.")
    print(f"2. `{logscale_api_url}`: The URL to which the data is sent.")
    print("3. `-X POST`: Specifies the request method to be POST.")
    print("4. `-H 'Authorization: Bearer {logscale_api_token}'`: Adds the authorization header with the Bearer token for authentication.")
    print("5. `-H 'Content-Type: text/plain'`: Specifies the content type of the data being sent as plain text.")
    print("6. `--data '{raw_log}'`: The actual raw log data to be sent in the body of the POST request.")
    
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
        if not validate_config():
            return

        config = load_config()
        logscale_api_url = LOGSCALE_URL
        logscale_api_token = config['logscale_api_token_raw']
        encounter_id = config['encounter_id']
        alias = config['alias']

        raw_log = generate_proofpoint_logs(encounter_id, alias)
        logging.info(f"Generated raw log: {raw_log}")
        status_code, response_text = send_to_logscale(logscale_api_url, logscale_api_token, raw_log)
        logging.info(f"Status Code: {status_code}, Response: {response_text}")

        # Display an example log line for user reference
        print("\nExample Log Line:")
        print(raw_log)

        # Description of the log line structure
        print("\nDescription:")
        print("The log line includes various details such as:")
        print("- campaignId (campaignId)")
        print("- classification (classification)")
        print("- clickIP (clickIP)")
        print("- clickTime (clickTime)")
        print("- GUID (GUID)")
        print("- id (id)")
        print("- messageID (messageID)")
        print("- recipient (recipient)")
        print("- sender (sender)")
        print("- senderIP (senderIP)")
        print("- threatID (threatID)")
        print("- threatTime (threatTime)")
        print("- threatURL (threatURL)")
        print("- threatStatus (threatStatus)")
        print("- url (url)")
        print("- userAgent (userAgent)")
        print("\nThe raw data is ingested into LogScale using the raw API endpoint.")

        # How to search for the data in LogScale
        print("\nHow to Search for Your Data in LogScale:")
        print(f"1. Go to your LogScale view and set the time range from the past week.")
        print(f"2. Use the following query to search for your data:")
        print(f"observer.id={encounter_id} AND observer.alias={alias}")

    except Exception as e:
        logging.error("An error occurred: ", exc_info=True)
        print(e)

if __name__ == "__main__":
    main()
