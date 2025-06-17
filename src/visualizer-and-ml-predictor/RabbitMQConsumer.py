import pika
import json
from datetime import datetime

# RabbitMQ Configuration
rabbitmq_address = "192.168.0.100"
rabbitmq_port_number = 5672
queue_name = "data_queue"

def consume_from_rabbitmq():
    """Consume averaged PM2.5 data from RabbitMQ, reformat timestamps, and print."""
    try:
        # Establish a connection to RabbitMQ
        connection = pika.BlockingConnection(
            pika.ConnectionParameters(host=rabbitmq_address, port=rabbitmq_port_number)
        )
        channel = connection.channel()

        # Ensure the queue exists
        channel.queue_declare(queue=queue_name, durable=True)

        # Define the callback function
        def callback(ch, method, properties, body):
            """Callback function to process incoming messages."""
            try:
                # Decode the received message
                message = body.decode('utf-8')
                data = json.loads(message)

                # Extract and reformat the timestamp and PM2.5 value
                timestamp = data.get('Timestamp')
                pm25_value = data.get('AveragePM2.5')

                if timestamp:
                    # Convert timestamp from milliseconds to readable format
                    formatted_time = datetime.utcfromtimestamp(timestamp / 1000.0).strftime('%Y-%m-%d %H:%M:%S')
                    print(f"Received Message: Timestamp = {formatted_time}, PM2.5 Value = {pm25_value}")
                else:
                    print("Message missing 'Timestamp' field")

            except Exception as e:
                print(f"Error processing message: {e}")

        # Start consuming messages
        channel.basic_consume(queue=queue_name, on_message_callback=callback, auto_ack=True)
        print(f"Waiting for messages in queue '{queue_name}'. To exit press CTRL+C")
        channel.start_consuming()

    except Exception as e:
        print(f"Error connecting to RabbitMQ: {e}")

if __name__ == "__main__":
    consume_from_rabbitmq()