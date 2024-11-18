# Real-Time Kafka IoT Data Visualization with Apache Spark and Flask

## Prerequisites

1. **Hadoop Cluster (Should be already installed)**  
   Ensure your Hadoop cluster is up and running. Note the `core-site.xml` and `hdfs-site.xml` configurations for Spark integration.

2. **Apache Kafka**  
   Install Kafka to manage the IoT data streams.

3. **Apache Spark (Should be already installed)**  
   Use Spark without its embedded Hadoop distribution by linking it to your existing Hadoop setup.

4. **Python Environment (Should be already installed)**  
   Install Python (>=3.8) with required libraries.

---

## Step 1: Install Kafka

1. Download Kafka:

   ```bash
   wget https://downloads.apache.org/kafka/3.5.1/kafka_2.13-3.5.1.tgz
   tar -xvzf kafka_2.13-3.5.1.tgz
   mv kafka_2.13-3.5.1 /home/<USER>/kafka
   ```

2. Update environment variables:

   ```bash
   export KAFKA_HOME=/home/<USER>/kafka
   export PATH=$PATH:$KAFKA_HOME/bin
   ```

3. Start Kafka:

   ```bash
   zookeeper-server-start.sh $KAFKA_HOME/config/zookeeper.properties &
   kafka-server-start.sh $KAFKA_HOME/config/server.properties &
   ```

4. Create a Kafka topic:

   ```bash
   kafka-topics.sh --create --topic iot-sensor-data --bootstrap-server localhost:9092 --partitions 3 --replication-factor 1
   ```

---

## Step 2: Configure Spark (Skip if Spark is already installed and configured)

1. **Download Spark (without bundled Hadoop):**

   ```bash
   wget https://downloads.apache.org/spark/spark-3.5.3/spark-3.5.3-bin-without-hadoop.tgz
   tar -xvzf spark-3.5.3-bin-without-hadoop.tgz
   mv spark-3.5.3-bin-without-hadoop /home/<USER>/spark
   ```

2. **Set environment variables:**

   ```bash
   export SPARK_HOME=/home/<USER>/spark
   export PATH=$PATH:$SPARK_HOME/bin
   ```

3. **Link Spark to your Hadoop cluster:**
   - Copy your Hadoop configuration files (`core-site.xml` and `hdfs-site.xml`) to `$SPARK_HOME/conf/`.
   - Test the connection:

     ```bash
     hdfs dfs -ls /
     ```

4. **Install PySpark:**

   ```bash
   pip install pyspark
   ```

---

## Step 3: Set Up Kafka Producer for IoT Data

1. Create a Python script (`kafka_producer.py`) to send simulated IoT data (existed in kafka/kafka_producer.py):

   ```python
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
   ```

2. Run the producer:

   ```bash
   python kafka_producer.py
   ```

---

## Step 4: Run the Spark Streaming Application

1. Create the Spark Streaming script (`spark_streaming.py`):
   *(Refer to the full script shared earlier)*

2. Submit the Spark application:

   ```bash
   spark-submit \
   --master yarn \
   --deploy-mode client \
   --conf spark.hadoop.fs.defaultFS=hdfs://localhost:8020 \
   spark_streaming.py
   ```

---

## Step 5: Set Up Application for consuming data

1. Create the application to consume the data. There are 2 examples for consuming data on this module.

    ```
    real-time-iot-visualization
    ├── ...
    ├── spark
    │   ├── raw-data
    │   └── visualize-graph-data  
    └── ...
    ```

### Step 5A: Set Up Web Application for consuming data

2. Install required libraries:

   ```bash
   pip install flask matplotlib
   ```

3. Run the Flask app (For visualize-graph-data):

   ```bash
   python kafka-web.py
   ```

4. Access the visualization in your browser at:

   ```
   http://<your-server-ip>:5010
   ```

### Step 5B: Set Up Application for consuming data and print to terminal

3. Run the Python app (For raw-data):

   ```bash
   python raw-data.py
   ```

---

## Step 6: Monitor and Visualize Data

- Kafka will continuously stream IoT data.
- Spark processes the data and sends results to Flask for real-time visualization.
- Use filters in the Flask app to focus on specific devices or parameters (e.g., temperature or humidity).

---

## Notes

1. **Debugging Connections**:
   - Ensure that your Hadoop and Kafka endpoints are reachable from Spark.
   - Check `spark-defaults.conf` for accurate configurations.

2. **Performance Tuning**:
   - Optimize Spark's resource usage with `executor` and `driver` memory settings.

3. **Logs**:
   - Check logs for Spark and Flask for troubleshooting. Logs can be found in `/spark/logs` and `/app/logs` (if configured).
