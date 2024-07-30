from flask import Flask
from dotenv import load_dotenv

# Load environment variables from .env file
load_dotenv()

app = Flask(__name__)

# Import the blueprint
from routes.users import users_bp
from routes.movies import movies_bp
from routes.orders import orders_bp

# Register the blueprint
app.register_blueprint(users_bp, url_prefix='/api')
app.register_blueprint(movies_bp, url_prefix='/api')
app.register_blueprint(orders_bp, url_prefix='/api')

if __name__ == '__main__':
    app.run(debug=True)
