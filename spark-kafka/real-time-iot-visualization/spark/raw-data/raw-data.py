import signal
import sys
from pyspark.sql import SparkSession
from pyspark.sql.functions import from_json, col, window, avg, to_timestamp
from pyspark.sql.types import StructType, StructField, StringType, DoubleType, LongType

# Initialize Spark session
spark = SparkSession.builder \
    .appName("IoTDataVisualization") \
    .master("yarn") \
    .getOrCreate()

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

# Parse the Kafka message value (which is in JSON format) into the schema
iot_data_df = kafka_df.select(from_json(col("value").cast("string"), schema).alias("data"))

# Flatten the struct data to individual columns
iot_data_df = iot_data_df.select("data.device_id", "data.temperature", "data.humidity", "data.timestamp")

# Convert the timestamp from LONG to TIMESTAMP type
iot_data_df = iot_data_df.withColumn("timestamp", to_timestamp(col("timestamp")))

# Aggregate the data by time window
aggregated_df = iot_data_df.groupBy(window("timestamp", "1 minute"), "device_id") \
    .agg(
        avg("temperature").alias("average_temperature"),
        avg("humidity").alias("average_humidity")
    )

# Function to print the processed data to terminal
def print_batch_data(batch_df, batch_id):

    if not batch_df.isEmpty():
       # Check column names and schema to ensure 'window.start' exists
        print("Schema:", batch_df.schema)
        print("Columns:", batch_df.columns)
        
        # Convert to Pandas dataframe to check contents
        latest_data = batch_df.toPandas()

        # Print first few rows
        print("Data in current batch:")
        print(latest_data.head())

        # Ensure 'window.start' exists in the data
        if 'window.start' in latest_data.columns:
            print(latest_data[['device_id', 'average_temperature', 'average_humidity', 'window.start']])
        else:
            print("Column 'window.start' not found in the data.")
    else:
        print(f"Batch {batch_id} is empty.")

# Function to handle termination (Ctrl+C)
def handle_termination(signal, frame):
    print("Termination signal received, stopping streaming query...")
    query.stop()  # Stop the streaming query
    print("Streaming query stopped.")
    
    spark.stop()  # Stop the Spark session
    print("Spark session stopped.")
    
    sys.exit(0)  # Exit the program

# Register termination signal handler
# signal.signal(signal.SIGINT, handle_termination)

# Set up streaming query with foreachBatch to print data
query = aggregated_df.writeStream \
    .outputMode("update") \
    .foreachBatch(print_batch_data) \
    .trigger(processingTime='5 seconds') \
    .start()

# Await termination
query.awaitTermination()
