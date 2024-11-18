import signal
import sys
import threading
from flask import Flask, jsonify, render_template, request
from pyspark.sql import SparkSession
from pyspark.sql.functions import from_json, col, window, avg, to_timestamp
from pyspark.sql.types import StructType, StructField, StringType, DoubleType, LongType

# Initialize Spark session
spark = SparkSession.builder \
    .appName("IoTDataVisualization") \
    .master("yarn") \
    .getOrCreate()

# Flask app
app = Flask(__name__)

# Global variable to store data
data_store = {
    "temperature": [],
    "humidity": [],
    "devices": set()
}

# Define the schema of the IoT data
schema = StructType([
    StructField("device_id", StringType(), True),
    StructField("temperature", DoubleType(), True),
    StructField("humidity", DoubleType(), True),
    StructField("timestamp", DoubleType(), True)
])

# Read from Kafka topic 'iot-sensor-data'
kafka_df = spark.readStream \
    .format("kafka") \
    .option("kafka.bootstrap.servers", "localhost:9092") \
    .option("subscribe", "iot-sensor-data") \
    .load()

# Parse the Kafka message value (JSON format) into the schema
iot_data_df = kafka_df.select(from_json(col("value").cast("string"), schema).alias("data"))

# Flatten the struct data into individual columns
iot_data_df = iot_data_df.select("data.device_id", "data.temperature", "data.humidity", "data.timestamp")
iot_data_df = iot_data_df.withColumn("timestamp", to_timestamp(col("timestamp")))

# Function to store data for each batch
def process_batch(batch_df, batch_id):
    if not batch_df.isEmpty():
        # Convert to Pandas for easier manipulation in Flask
        batch_data = batch_df.toPandas()
        
        # Append temperature, humidity, and device info to the data store
        for _, row in batch_data.iterrows():
            data_store["temperature"].append({"time": row["timestamp"], "device": row["device_id"], "value": row["temperature"]})
            data_store["humidity"].append({"time": row["timestamp"], "device": row["device_id"], "value": row["humidity"]})
            data_store["devices"].add(row["device_id"])

# Define Spark Streaming query with foreachBatch
query = iot_data_df.writeStream \
    .outputMode("append") \
    .foreachBatch(process_batch) \
    .trigger(processingTime='5 seconds') \
    .start()

# Flask routes
@app.route('/')
def index():
    return render_template("index.html")

@app.route('/data')
def get_data():
    # Get selected device from query parameter
    device_filter = request.args.get("device")
    if device_filter and device_filter != "all":
        # Filter data for the specific device
        temperature_data = [d for d in data_store["temperature"] if d["device"] == device_filter]
        humidity_data = [d for d in data_store["humidity"] if d["device"] == device_filter]
    else:
        # Show data for all devices
        temperature_data = data_store["temperature"]
        humidity_data = data_store["humidity"]
    
    return jsonify({"temperature": temperature_data, "humidity": humidity_data, "devices": list(data_store["devices"])})

# Function to handle termination
def handle_termination(signal, frame):
    print("Stopping streaming query and Flask server...")
    query.stop()
    spark.stop()
    func = request.environ.get('werkzeug.server.shutdown')
    if func:
        func()

signal.signal(signal.SIGINT, handle_termination)

# Run Flask in a thread on port 5010
flask_thread = threading.Thread(target=lambda: app.run(debug=True, use_reloader=False, port=5010))
flask_thread.start()

# Await Spark streaming termination
query.awaitTermination()
