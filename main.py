from flask import Flask
from flask_cors import CORS
from flask_jwt_extended import JWTManager
from database.db import db
from routes.user_routes import user_bp
from routes.pod_routes import pod_bp
from dotenv import load_dotenv
import os
from werkzeug.serving import run_simple

load_dotenv()

app = Flask(__name__)
CORS(app)

app.config['SQLALCHEMY_DATABASE_URI'] = os.getenv('SQLALCHEMY_DATABASE_URI')
app.config['SQLALCHEMY_TRACK_MODIFICATIONS'] = False
app.config['JWT_SECRET_KEY'] = os.getenv('JWT_SECRET_KEY')

# Initialize extensions
jwt = JWTManager(app)

app.register_blueprint(user_bp)
app.register_blueprint(pod_bp)
app.register_blueprint(group_bp)

if __name__ == '__main__':
    with app.app_context():
        db.create_all()

    cert_path = "./STAR_bucaramanga_upb_edu_co.crt"
    key_path = "./web14.key"
    ca_bundle_path = "./STAR_bucaramanga_upb_edu_co.ca-bundle"

    run_simple('0.0.0.0', 5000, app, ssl_context=(cert_path, key_path))
