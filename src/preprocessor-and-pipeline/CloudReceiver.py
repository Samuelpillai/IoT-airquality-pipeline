import pika
import pandas as pd
import json
import matplotlib.pyplot as plt
from datetime import datetime
from ml_engine import MLPredictor
import matplotlib.dates as mdates
import threading
import time

# List to store received data
data_storage = []

# Function to parse received messages from RabbitMQ
def parse_message(body):
    try:
        message = json.loads(body.decode('utf-8'))
        print(f"Received Message: {message}")

        # Extract and format timestamp and value
        timestamp = datetime.utcfromtimestamp(message['Timestamp'] / 1000.0).strftime('%Y-%m-%d %H:%M:%S')
        pm25_value = message['AveragePM2.5']

        print(f"Formatted Data: Timestamp = {timestamp}, PM2.5 Value = {pm25_value}")
        data_storage.append({'Timestamp': timestamp, 'Value': pm25_value})
    except Exception as e:
        print(f"Error parsing message: {e}")

# Function to start consuming messages from RabbitMQ
def start_consuming(rabbitmq_host='192.168.0.100', queue_name='CSC8112'):
    connection = pika.BlockingConnection(pika.ConnectionParameters(host=rabbitmq_host))
    channel = connection.channel()
    channel.queue_declare(queue=queue_name, durable=True)

    def callback(ch, method, properties, body):
        parse_message(body)

    channel.basic_consume(queue=queue_name, on_message_callback=callback, auto_ack=True)
    print(f"Listening for messages on queue '{queue_name}'...")
    channel.start_consuming()

# Function to plot PM2.5 data as a line chart
def plot_pm25_data(data_df):
    plt.figure(figsize=(10, 6))
    plt.plot(data_df['ds'], data_df['y'], marker='o', linestyle='-', color='b')
    plt.title('Daily Average PM2.5 Levels')
    plt.xlabel('Date')
    plt.ylabel('PM2.5')
    plt.gca().xaxis.set_major_locator(mdates.DayLocator(interval=1))
    plt.gca().xaxis.set_major_formatter(mdates.DateFormatter('%Y-%m-%d'))
    plt.xticks(rotation=45)
    plt.tight_layout()
    plt.savefig('pm25_data_plot.png')
    plt.show()

# Function to plot predictions
def plot_predictions(forecast):
    plt.figure(figsize=(10, 6))
    plt.plot(forecast['ds'], forecast['yhat'], marker='o', linestyle='-', color='r', label='Predicted PM2.5')
    plt.title('Predicted PM2.5 Levels (Next 15 Days)')
    plt.xlabel('Date')
    plt.ylabel('Predicted PM2.5')
    plt.gca().xaxis.set_major_locator(mdates.DayLocator(interval=1))
    plt.gca().xaxis.set_major_formatter(mdates.DateFormatter('%Y-%m-%d'))
    plt.xticks(rotation=45)
    plt.tight_layout()
    plt.savefig('pm25_predictions_plot.png')
    plt.show()

# Main workflow for data visualization and prediction
def main():
    # Start RabbitMQ consumer in a background thread
    consumer_thread = threading.Thread(target=start_consuming, args=('192.168.0.100', 'CSC8112'))
    consumer_thread.start()

    # Wait for data accumulation
    print("Waiting for data to accumulate...")
    time.sleep(60)

    if not data_storage:
        print("No data received. Exiting.")
        return

    # Convert data into a DataFrame
    data_df = pd.DataFrame(data_storage)
    data_df.rename(columns={'Timestamp': 'ds', 'Value': 'y'}, inplace=True)

    # Plot historical data
    print("Plotting PM2.5 data...")
    plot_pm25_data(data_df)

    # Predict future values
    print("Predicting future PM2.5 levels...")
    predictor = MLPredictor(data_df)
    predictor.train()
    forecast = predictor.predict()

    # Plot predictions
    print("Plotting predictions...")
    plot_predictions(forecast)

    consumer_thread.join()

# Entry point
if __name__ == "__main__":
    main()