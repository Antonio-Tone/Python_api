import mysql.connector
from mysql.connector import Error
from dotenv import load_dotenv
import os

# Load environment variables from .env file
load_dotenv()

# Define your database configuration using environment variables
db_config = {
    'host': os.getenv('DB_HOST'),
    'user': os.getenv('DB_USER'),
    'password': os.getenv('DB_PASSWORD'),
    'database': os.getenv('DB_NAME'),
    'port': int(os.getenv('DB_PORT'))  # Ensure port is an integer
}

def get_db_connection():
    try:
        connection = mysql.connector.connect(**db_config)
        if connection.is_connected():
            print("Successfully connected to the database")
            return connection
        else:
            print("Failed to connect to the database")
            return None
    except Error as e:
        print(f"Error connecting to database: {e}")
        return None

# Test the connection
connection = get_db_connection()

# Optional: If you want to perform any operations, you can add them here.
if connection:
    connection.close()
    print("Connection closed")