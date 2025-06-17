import paho.mqtt.client as mqtt
import json
import time
import pika
from collections import defaultdict
from datetime import datetime
import logging

# Configure logging
logging.basicConfig(format='%(asctime)s - %(message)s', datefmt='%Y-%m-%d %H:%M:%S', level=logging.INFO)

# RabbitMQ Configuration
rabbitmq_address = "192.168.0.100"
rabbitmq_port_number = 5672
queue_name = "data_queue"

# MQTT Broker Configuration
mqtt_server = "192.168.0.102"
mqtt_port_number = 1883
mqtt_channel = "sensor/pm2.5"

# Structures to organize daily data
collected_data_per_day = defaultdict(list)
initial_timestamp_per_day = {}
processed_days = set()

# Function triggered on receiving MQTT data
def handle_message(client, userdata, message):
    try:
        payload = json.loads(message.payload.decode('utf-8'))
        logging.info(f"MQTT Data Received: {payload}")

        data_timestamp = payload.get('timestamp')
        pm25_value = payload.get('value')

        if pm25_value > 50:
            logging.info(f"Outlier value: {pm25_value} (Timestamp: {data_timestamp})")
            return

        if data_timestamp:
            timestamp_obj = datetime.utcfromtimestamp(data_timestamp / 1000.0)
            day_key = timestamp_obj.strftime('%Y-%m-%d')

            collected_data_per_day[day_key].append({
                'timestamp': timestamp_obj,
                'value': pm25_value
            })

            if day_key not in initial_timestamp_per_day:
                initial_timestamp_per_day[day_key] = timestamp_obj

            logging.info(f"Data stored for {day_key}: {pm25_value} at {timestamp_obj}")

            # If we've collected >= 10 samples for the day and haven't processed it
            if len(collected_data_per_day[day_key]) >= 10 and day_key not in processed_days:
                send_daily_average_to_rabbitmq(day_key)
                processed_days.add(day_key)

        else:
            logging.warning("Received data without a valid timestamp.")
    except json.JSONDecodeError as e:
        logging.error(f"Failed to decode JSON payload: {e}")
    except Exception as error:
        logging.error(f"MQTT message processing error: {error}")

# Send average PM2.5 value to RabbitMQ
def send_daily_average_to_rabbitmq(day_key):
    try:
        data_list = collected_data_per_day[day_key]
        avg = sum(d['value'] for d in data_list) / len(data_list)
        initial_time = int(initial_timestamp_per_day[day_key].timestamp() * 1000)

        message_payload = {
            'Timestamp': initial_time,
            'AveragePM2.5': round(avg, 2)
        }

        serialized_payload = json.dumps(message_payload)

        connection = pika.BlockingConnection(pika.ConnectionParameters(host=rabbitmq_address, port=rabbitmq_port_number))
        channel = connection.channel()
        channel.queue_declare(queue=queue_name, durable=True)

        channel.basic_publish(
            exchange='',
            routing_key=queue_name,
            body=serialized_payload,
            properties=pika.BasicProperties(
                delivery_mode=2,
                content_type='application/json'
            )
        )

        logging.info(f"Data sent to RabbitMQ: {serialized_payload}")
        connection.close()

    except Exception as e:
        logging.error(f"RabbitMQ transmission error: {e}")

# Configure MQTT Client
def initialize_mqtt_client():
    mqtt_client = mqtt.Client()
    mqtt_client.on_message = handle_message
    mqtt_client.connect(mqtt_server, mqtt_port_number, keepalive=60)
    mqtt_client.subscribe(mqtt_channel)
    return mqtt_client

# Main
if __name__ == "__main__":
    logging.info("Initializing MQTT client...")
    mqtt_client_instance = initialize_mqtt_client()
    mqtt_client_instance.loop_start()

    try:
        while True:
            time.sleep(1)
    except KeyboardInterrupt:
        logging.info("Terminating...")
        mqtt_client_instance.loop_stop()
        mqtt_client_instance.disconnect()
        logging.info("MQTT client disconnected.")