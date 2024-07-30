from flask import Blueprint, request, jsonify, make_response
import mysql.connector
from mysql.connector import Error
import os
from dotenv import load_dotenv
import bcrypt
import jwt
from datetime import datetime, timedelta

# JWT secret
JWT_SECRET = os.getenv('JWT_SECRET')

# Define the blueprint
users_bp = Blueprint('users', __name__)

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

@users_bp.route('/users', methods=['GET'])
def fetch_users():
    connection = get_db_connection()
    if connection is None:
        return jsonify({"status": 500, "msg": "Internal server Error"}),500
    
    cursor = connection.cursor(dictionary=True)
    query = "SELECT userID, userName, lastName, gender, age, emailAdd FROM users"
    cursor.execute(query)
    data = cursor.fetchall()
    cursor.close()
    connection.close()

    if len(data) == 0:
        return jsonify({"status": 404, "msg": "No users found"})
         
    else:
        return jsonify({"status":200, "msg": "Success", "result": data})
    
@users_bp.route('/user/<int:id>', methods=['GET'])
def fetch_user(id):
    connection = get_db_connection()
    if connection is None:
        return jsonify({"status": 500, "msg": "Internal server error"}), 500

    cursor = connection.cursor(dictionary=True)
    query = "SELECT userID, userName, lastName, gender,age,emailAdd FROM users WHERE userID = %s"
    cursor.execute(query, (id,))
    result = cursor.fetchall()
    cursor.close()
    connection.close()

    if len(result) == 0:
        return jsonify({"status": 404, "msg": "User not found"}), 404

    return jsonify({"status": 200, "msg": "success", "result": result})

@users_bp.route('/user/<int:id>', methods=['DELETE'])
def delete_user(id):
    connection = get_db_connection()
    if connection is None:
        return jsonify({"status": 500, "msg": "Internal server error"}), 500

    cursor = connection.cursor()
    query = "DELETE FROM users WHERE userID = %s"
    cursor.execute(query, (id,))
    connection.commit()
    affected_rows = cursor.rowcount
    cursor.close()
    connection.close()

    if affected_rows == 0:
        return jsonify({"status": 404, "msg": "User not found or already deleted"}), 404

    return jsonify({"status": 200, "msg": "Removed User successfully"})   

 
@users_bp.route('/user/<int:id>', methods=['PATCH'])
def update_user(id):
    connection = get_db_connection()
    if connection is None:
        return jsonify({"status": 500, "msg": "Internal server error"}), 500

    data = request.json

    if not data:
        return jsonify({"status": 400, "msg": "No data provided"}), 400

    # Build the SET clause dynamically
    set_clause = ", ".join(f"{key} = %s" for key in data.keys())
    values = list(data.values()) + [id]

    query = f"UPDATE users SET {set_clause} WHERE userID = %s"
    
    cursor = connection.cursor()
    cursor.execute(query, values)
    connection.commit()
    affected_rows = cursor.rowcount
    cursor.close()
    connection.close()

    if affected_rows == 0:
        return jsonify({"status": 404, "msg": "User not found"}), 404

    return jsonify({"status": 200, "msg": "User updated successfully"})

# login and register code below:

@users_bp.route('/register', methods=['POST'])
def register():
    data = request.json
    email = data.get('emailAdd')
    password = data.get('userPass')
    name = data.get('userName')
    surname = data.get('lastName')
    age = data.get('age')
    gender = data.get('gender')

    if not email or not password or not name or not surname or not age or not gender:
        return jsonify({'status': 400, 'msg': 'All fields are required'}), 400
    
    # Hash the password
    hashed_password = bcrypt.hashpw(password.encode('utf-8'), bcrypt.gensalt(12))

    connection = get_db_connection()
    if connection is None:
        return jsonify({'status': 500, 'msg': 'Internal server error'}), 500

    cursor = connection.cursor(dictionary=True)

    # Check if email is already in use
    check_query = "SELECT COUNT(*) AS count FROM users WHERE emailAdd = %s"
    cursor.execute(check_query, (email,))
    check_result = cursor.fetchone()

    if check_result['count'] > 0:
        cursor.close()
        connection.close()
        return jsonify({'status': 400, 'msg': 'Email already in use'}), 400

    # Insert user into the database
    columns = 'emailAdd, userPass, userName, lastName, age, gender'
    placeholders = '%s, %s, %s, %s, %s, %s'
    insert_query = f"INSERT INTO users ({columns}) VALUES ({placeholders})"
    values = (email, hashed_password, name, surname, age, gender)

    try:
        cursor.execute(insert_query, values)
        connection.commit()
    except Error as insert_err:
        print(f"Error inserting user: {insert_err}")
        cursor.close()
        connection.close()
        return jsonify({'status': 500, 'msg': 'Internal server error'}), 500

    cursor.close()
    connection.close()

    # Create token
    token = jwt.encode({'emailAdd': email, 'exp': datetime.utcnow() + timedelta(hours=2)}, JWT_SECRET, algorithm='HS256')

    response = make_response(jsonify({'status': 200, 'msg': 'User registered successfully!'}))
    response.set_cookie('newUser', token, httponly=True, expires=datetime.utcnow() + timedelta(hours=2))

    return response

@users_bp.route('/login', methods=['POST'])
def login():
    data = request.json
    email = data.get('emailAdd')
    password = data.get('userPass')

    if not email or not password:
        return jsonify({'status': 400, 'msg': 'Email and password are required'}), 400

    connection = get_db_connection()
    if connection is None:
        return jsonify({'status': 500, 'msg': 'Internal server error'}), 500

    cursor = connection.cursor(dictionary=True)
    
    query = "SELECT userID, userName, lastName, gender, age, emailAdd, userPass FROM users WHERE emailAdd = %s"
    cursor.execute(query, (email,))
    result = cursor.fetchone()
    cursor.close()
    connection.close()

    if result is None:
        return jsonify({'status': 400, 'msg': 'Email is incorrect'}), 400

    if not bcrypt.checkpw(password.encode('utf-8'), result['userPass'].encode('utf-8')):
        return jsonify({'status': 400, 'msg': 'Password is incorrect'}), 400

    token = jwt.encode(
        {'emailAdd': email, 'exp': datetime.utcnow() + timedelta(hours=2)},
        JWT_SECRET,
        algorithm='HS256'
    )

    response = jsonify({
        'status': 200,
        'msg': 'Successful login',
        'token': token,
        'result': result
    })
    response.set_cookie('newUser', token, httponly=True, expires=datetime.utcnow() + timedelta(hours=2))

    return response
