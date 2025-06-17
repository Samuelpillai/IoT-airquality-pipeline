import json
import requests
import time
import paho.mqtt.client as mqtt

# EMQX Broker Configuration
BROKER_HOST = '192.168.0.102'
BROKER_PORT = 1883
MQTT_TOPIC = "sensor/pm2.5"

# URL for Newcastle Urban Observatory API
url = "https://gist.githubusercontent.com/ringosham/fbd66654dc53c40bd4581d2828acc94e/raw/d56a0fcfd27ff7ea31e2aec3765eb2c5d64adb79/uo_data.min.json"

try:
    # Initialize the MQTT client with a unique client ID
    client = mqtt.Client(client_id="data_injector")

    # Step 1: Retrieve data from API
    response = requests.get(url)
    print(f"Status Code: {response.status_code}")
    
    if response.status_code == 200:
        raw_data = response.json()
    elif response.status_code == 500:
        print(f"API Error: {response.text}")
        raw_data = {}
    else:
        print(f"Failed to retrieve data. Status code: {response.status_code}")
        raw_data = {}

    # Step 2: Filter for PM2.5 data
    pm25_data = []
    for sensor in raw_data.get("sensors", []):
        data_entries = sensor.get("data", {})

        for key, entries in data_entries.items():
            if isinstance(entries, list):
                for item in entries:
                    if isinstance(item, dict) and item.get("Variable") == "PM2.5":
                        pm25_entry = {
                            "timestamp": item["Timestamp"],
                            "value": item["Value"]
                        }
                        pm25_data.append(pm25_entry)

    print("Filtered PM2.5 Data:")
    for entry in pm25_data:
        print(f"Timestamp: {entry['timestamp']}, Value: {entry['value']}")

    # Step 3: Connect to EMQX and publish PM2.5 data
    try:
        print(f"Attempting to connect to MQTT broker at {BROKER_HOST}:{BROKER_PORT}...")
        client.connect(BROKER_HOST, BROKER_PORT, keepalive=60)
    except Exception as e:
        print(f"Failed to connect to MQTT broker: {e}")
        raise

    client.loop_start()  # Start background network loop

    for data_point in pm25_data:
        message = json.dumps(data_point)
        client.publish(MQTT_TOPIC, message)
        print(f"Sent data to EMQX: {message}")
        time.sleep(0.3)  # Slight delay to avoid overwhelming the broker

except requests.RequestException as e:
    print(f"An error occurred while fetching data: {e}")

except Exception as e:
    print(f"An error occurred: {e}")

finally:
    try:
        client.loop_stop()
        client.disconnect()
    except Exception as e:
        print(f"An error occurred during disconnect: {e}")