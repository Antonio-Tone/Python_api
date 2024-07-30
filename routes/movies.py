from flask import Blueprint, request, jsonify
import mysql.connector
from mysql.connector import Error
import os
from dotenv import load_dotenv

# Define the blueprint
movies_bp = Blueprint('movies', __name__)

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
    
@movies_bp.route('/movies', methods=['GET'])
def fetch_movies():
    connection = get_db_connection()
    if connection is None:
        return jsonify({'status': 500, 'msg':"Internal server Error"}), 500
    cursor = connection.cursor(dictionary = True)
    query = "SELECT movieID, movie_poster, movie_title, release_year, rating, duration, discription, star FROM movies"
    cursor.execute(query)
    data = cursor.fetchall()
    cursor.close()
    connection.close()

    if len(data) == 0:
        return jsonify({'status':404, "msg": "Movie not found" })
    else:
        return jsonify({'status':200,'msg':'success', 'result':data})

@movies_bp.route('/movie/<int:id>', methods=['GET'])
def fetch_movie(id):
    connection = get_db_connection()
    if connection is None:
        return jsonify({'status':500,'msg':"Internal server error"}), 500
    
    cursor = connection.cursor(dictionary=True)
    query = "SELECT movieID, movie_poster, movie_title, release_year, rating, duration, discription, star FROM movies WHERE movieID = %s"
    cursor.execute(query, (id,))
    result = cursor.fetchall()
    cursor.close()
    connection.close()


    if len(result) == 0:
        return jsonify({'status': 404, "msg":"Movie not found"})
    
    else:
        return jsonify({'status':200, "msg":"Success", "result":result})

@movies_bp.route('/movie/<int:id>', methods=['DELETE'])
def delete_movie(id):
    connection = get_db_connection()
    if connection is None:
        return jsonify({"status": 500, "msg": "Internal Server Erorr"}), 500
    
    cursor = connection.cursor()
    query = "DELETE FROM movies WHERE movieID = %s"
    cursor.execute(query,(id,))
    connection.commit()
    affected_rows = cursor._rowcount
    cursor.close()
    connection.close()

    if affected_rows == 0:
        return jsonify({"status":404, "msg": "Movie not found or is already deleted"})
    else:
        return jsonify({"status":200, "msg": "Movie removed successfully"})
   
@movies_bp.route('/movie/<int:id>', methods=['PATCH'])
def update_movie(id):
    connection = get_db_connection()
    if connection is None:
        return jsonify({"status":500, "msg": "Internal server error"}), 500
    
    data = request.json

    if not data:
        return jsonify({"status":500, "msg": "No data provided"}), 500
    
    # Build the SET clause dynamically
    set_clause =  ", ".join(f"{key} =%s" for key in data.keys())
    values = list(data.values()) + [id]

    query= f"UPDATE movies SET {set_clause} WHERE movieID = %s"
    cursor = connection.cursor()
    cursor.execute(query, values)
    connection.commit()
    affected_rows = cursor.rowcount
    cursor.close()
    connection.close()
    
    if affected_rows == 0:
        return jsonify({"status": 404, 'msg': "Movie not found"})
    
    else:
        return jsonify({"status":200, 'msg': "Movie updated successfully"})
    
@movies_bp.route('/movie', methods=['POST'])
def add_movie():
    connection = get_db_connection()
    if connection is None:
        return jsonify({"status":500, "msg": "Internal Server Error"}),500
    
    data = request.json
    
    # Prepare SQL query and values
    columns = ', '.join(data.keys())
    placeholders = ', '.join(['%s'] * len(data))
    query = f"INSERT INTO movies ({columns}) VALUES ({placeholders})"
    values = tuple(data.values())

    cursor = connection.cursor()
    
    try:
        cursor.execute(query,values)
        connection.commit()
    except Error as e:
        print(f"Error adding movie: {e}")
        connection.rollback()
        return jsonify({'status':500, "msg": "internal server error"}), 500
    finally:
        cursor.close()
        connection.close()
    return jsonify({'status':200, "msg": "successfully added movie"}), 200

