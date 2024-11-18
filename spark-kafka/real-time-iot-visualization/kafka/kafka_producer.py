from kafka import KafkaProducer
import json
import time
import random

producer = KafkaProducer(
    bootstrap_servers='localhost:9092', # Use local broker to send data, change it to real broker IP
    value_serializer=lambda v: json.dumps(v).encode('utf-8') # Format string to bytes
)

def generate_iot_data():
    # Create dummy data with device_id, temperature, humidity and timestamp
    data = {
        'device_id': f'device_{random.randint(0, 10)}',
        'temperature': round(random.uniform(20.0, 33.0)), # Random temperature from 20.0 to 33.0
        'humidity': round(random.uniform(20.0, 90.0)), # Random humidity from 20.0% to 90.0%
        'timestamp': time.time() # Random
    }

    return data

try:
    while True:
        iot_data = generate_iot_data()
        producer.send('iot-sensor-data', iot_data) # Topic name: iot-sensor-data
        print(f'Send data: {iot_data}')
        time.sleep(1) # Delay one second
except KeyboardInterrupt:
    print('Keyboard press detected, program closed.')
finally:
    producer.stop()