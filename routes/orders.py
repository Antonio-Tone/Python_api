from flask import Blueprint, request, jsonify
import mysql.connector
from mysql.connector import Error
import os
from dotenv import load_dotenv

# Define the blueprint
orders_bp = Blueprint('orders', __name__)

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
        return connection
    except Error as e:
        print(f"Error connecting to database: {e}")
        return None

@orders_bp.route('/orders', methods=['GET'])
def fetch_orders():
    connection = get_db_connection()
    if connection is None:
        return jsonify({"status": 500, "msg": "Internal server error"}), 500

    cursor = connection.cursor(dictionary=True)
    query = "SELECT orderID, price, userID, movieID FROM orders"
    cursor.execute(query)
    data = cursor.fetchall()
    cursor.close()
    connection.close()

    if len(data) == 0:
        return jsonify({"status": 404, "msg": "No orders found"}), 404

    return jsonify({"status": 200, "msg": "success", "result": data})

@orders_bp.route('/order/<int:id>', methods=['GET'])
def fetch_order(id):
    connection = get_db_connection()
    if connection is None:
        return jsonify({"status": 500, "msg": "Internal server error"}), 500

    cursor = connection.cursor(dictionary=True)
    query = "SELECT orderID, price, userID, movieID FROM orders WHERE orderID = %s"
    cursor.execute(query, (id,))
    result = cursor.fetchall()
    cursor.close()
    connection.close()

    if len(result) == 0:
        return jsonify({"status": 404, "msg": "Order not found"}), 404

    return jsonify({"status": 200, "msg": "success", "result": result})

@orders_bp.route('/order/<int:id>', methods=['DELETE'])
def delete_order(id):
    connection = get_db_connection()
    if connection is None:
        return jsonify({"status": 500, "msg": "Internal server error"}), 500

    cursor = connection.cursor()
    query = "DELETE FROM orders WHERE orderID = %s"
    cursor.execute(query, (id,))
    connection.commit()
    affected_rows = cursor.rowcount
    cursor.close()
    connection.close()

    if affected_rows == 0:
        return jsonify({"status": 404, "msg": "Order not found or already deleted"}), 404

    return jsonify({"status": 200, "msg": "Removed order successfully"})

@orders_bp.route('/order/<int:id>', methods=['PATCH'])
def update_order(id):
    connection = get_db_connection()
    if connection is None:
        return jsonify({"status": 500, "msg": "Internal server error"}), 500

    data = request.json

    if not data:
        return jsonify({"status": 400, "msg": "No data provided"}), 400

    # Build the SET clause dynamically
    set_clause = ", ".join(f"{key} = %s" for key in data.keys())
    values = list(data.values()) + [id]

    query = f"UPDATE orders SET {set_clause} WHERE orderID = %s"
    
    cursor = connection.cursor()
    cursor.execute(query, values)
    connection.commit()
    affected_rows = cursor.rowcount
    cursor.close()
    connection.close()

    if affected_rows == 0:
        return jsonify({"status": 404, "msg": "Order not found"}), 404

    return jsonify({"status": 200, "msg": "Order updated successfully"})


@orders_bp.route('/order', methods=['POST'])
def add_order():
    connection = get_db_connection()
    if connection is None:
        return jsonify({"status": 500, "msg": "Internal server error"}), 500

    data = request.json


    # Prepare SQL query and values
    columns = ', '.join(data.keys())
    placeholders = ', '.join(['%s'] * len(data))
    query = f"INSERT INTO orders ({columns}) VALUES ({placeholders})"
    values = tuple(data.values())

    cursor = connection.cursor()
    try:
        cursor.execute(query, values)
        connection.commit()
    except Error as e:
        print(f"Error adding order: {e}")
        connection.rollback()
        return jsonify({"status": 500, "msg": "Internal server error"}), 500
    finally:
        cursor.close()
        connection.close()

    return jsonify({"status": 200, "msg": "Successfully placed order"})

