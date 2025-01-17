from flask import Flask
from flask_cors import CORS
import os
from dotenv import load_dotenv
# Load environment variables from .env file
load_dotenv()

app = Flask(__name__)
CORS(app, origins=['http://localhost:3000'])

# Import the blueprint
from routes.users import users_bp
from routes.movies import movies_bp
from routes.orders import orders_bp

# Register the blueprint without a URL prefix
app.register_blueprint(users_bp)
app.register_blueprint(movies_bp)
app.register_blueprint(orders_bp)

if __name__ == '__main__':
    port = int(os.environ.get('PORT', 5000))
    app.run(host='0.0.0.0', port=port)