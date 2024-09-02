from flask import Flask
from flask_cors import CORS
from flask_jwt_extended import JWTManager
from database.db import db
from routes.user_routes import user_bp
from routes.pod_routes import pod_bp
from dotenv import load_dotenv
import os

# Load environment variables
load_dotenv()

app = Flask(__name__)
CORS(app)

# Configuration
app.config['SQLALCHEMY_DATABASE_URI'] = os.getenv('SQLALCHEMY_DATABASE_URI')
app.config['SQLALCHEMY_TRACK_MODIFICATIONS'] = False
app.config['JWT_SECRET_KEY'] = os.getenv('JWT_SECRET_KEY')
app.config['MAX_PODS_PER_USER'] = int(os.getenv('MAX_PODS_PER_USER', 5))

# Initialize extensions
db.init_app(app)
jwt = JWTManager(app)

# Register blueprints
app.register_blueprint(user_bp)
app.register_blueprint(pod_bp)

if __name__ == '__main__':
    with app.app_context():
        db.create_all()
    app.run(host='0.0.0.0', debug=True)