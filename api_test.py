from flask import Flask, request, jsonify
from flask_sqlalchemy import SQLAlchemy
from flask_bcrypt import Bcrypt
from flask_jwt_extended import JWTManager, jwt_required, create_access_token, get_jwt_identity
from kubernetes import client, config
from flask_cors import CORS
import pymysql
from dotenv import load_dotenv
import os
import time
pymysql.install_as_MySQLdb()

app = Flask(__name__)
CORS(app)

# Load environment variables
load_dotenv()

# Configuration
app.config['SQLALCHEMY_DATABASE_URI'] = os.getenv('SQLALCHEMY_DATABASE_URI')
app.config['SQLALCHEMY_TRACK_MODIFICATIONS'] = False
app.config['JWT_SECRET_KEY'] = os.getenv('JWT_SECRET_KEY')
app.config['MAX_PODS_PER_USER'] = int(os.getenv('MAX_PODS_PER_USER', 5))  # Default to 5 if not set

# Initialize extensions
db = SQLAlchemy(app)
bcrypt = Bcrypt(app)
jwt = JWTManager(app)

# Load Kubernetes configuration
config.load_kube_config()
v1 = client.CoreV1Api()

class User(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    username = db.Column(db.String(80), unique=True, nullable=False)
    password = db.Column(db.String(120), nullable=False)
    pods = db.relationship('Pod', backref='user', lazy=True)

class Pod(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    name = db.Column(db.String(120), nullable=False)
    image = db.Column(db.String(120), nullable=False)
    ports = db.Column(db.String(120), nullable=True)
    ip = db.Column(db.String(15), nullable=True)
    status = db.Column(db.String(50), nullable=True)
    user_id = db.Column(db.Integer, db.ForeignKey('user.id'), nullable=False)

@app.route('/register', methods=['POST'])
def register():
    username = request.json.get('username', None)
    password = request.json.get('password', None)
    
    if not username or not password:
        return jsonify({"msg": "Missing username or password"}), 400
    
    if User.query.filter_by(username=username).first():
        return jsonify({"msg": "Username already exists"}), 400
    
    hashed_password = bcrypt.generate_password_hash(password).decode('utf-8')
    new_user = User(username=username, password=hashed_password)
    db.session.add(new_user)
    db.session.commit()
    
    return jsonify({"msg": "User created successfully"}), 201

@app.route('/login', methods=['POST'])
def login():
    username = request.json.get('username', None)
    password = request.json.get('password', None)
    
    user = User.query.filter_by(username=username).first()
    if user and bcrypt.check_password_hash(user.password, password):
        access_token = create_access_token(identity=username)
        return jsonify(access_token=access_token), 200
    
    return jsonify({"msg": "Invalid username or password"}), 401

@app.route('/pods', methods=['GET'])
@jwt_required()
def get_pods():
    current_user = User.query.filter_by(username=get_jwt_identity()).first()
    user_pods = Pod.query.filter_by(user_id=current_user.id).all()
    
    pod_list = []
    for pod in user_pods:
        try:
            k8s_pod = v1.read_namespaced_pod(name=pod.name, namespace="default")
            status = k8s_pod.status.phase
        except client.exceptions.ApiException:
            status = "Not Found in Kubernetes"

        pod_list.append({
            "name": pod.name,
            "image": pod.image,
            "ports": pod.ports,
            "ip": pod.ip,
            "status": status
        })

    return jsonify(pod_list), 200


@app.route('/pods', methods=['POST'])
@jwt_required()
def create_pod():
    current_user = User.query.filter_by(username=get_jwt_identity()).first()
    pod_name = request.json.get('name')
    image = request.json.get('image')
    ports = request.json.get('ports')
    
    if not pod_name or not image:
        return jsonify({"msg": "Missing pod name or image"}), 400
    
    user_pod_count = Pod.query.filter_by(user_id=current_user.id).count()
    if user_pod_count >= app.config['MAX_PODS_PER_USER']:
        return jsonify({"msg": f"Maximum number of pods ({app.config['MAX_PODS_PER_USER']}) reached for this user"}), 400

    try:
        pod_manifest = {
            "apiVersion": "v1",
            "kind": "Pod",
            "metadata": {
                "name": f"{current_user.username}-{pod_name}",
                "labels": {
                    "user": current_user.username
                }
            },
            "spec": {
                "containers": [{
                    "name": pod_name,
                    "image": image,
                    "ports": [{"containerPort": int(port)} for port in ports.split(',')] if ports else []
                }]
            }
        }
        
        api_response = v1.create_namespaced_pod(body=pod_manifest, namespace="default")
        
        # Wait for the pod to be running and get its IP
        start_time = time.time()
        timeout = 60  # Timeout in seconds
        while True:
            pod = v1.read_namespaced_pod(name=f"{current_user.username}-{pod_name}", namespace="default")
            if pod.status.phase == 'Running' and pod.status.pod_ip:
                pod_ip = pod.status.pod_ip
                status = pod.status.phase
                break
            if time.time() - start_time > timeout:
                return jsonify({"msg": "Timeout while waiting for pod to be running"}), 504
            time.sleep(1)  # Sleep before polling again
        
        db_pod = Pod(
            name=f"{current_user.username}-{pod_name}",
            image=image,
            ports=ports,
            ip=pod_ip,
            status=status,
            user_id=current_user.id
        )
        db.session.add(db_pod)
        db.session.commit()
        
        return jsonify({
            "msg": "Pod created successfully",
            "name": db_pod.name,
            "image": db_pod.image,
            "ports": db_pod.ports,
            "ip": db_pod.ip,
            "status": db_pod.status
        }), 201
    except Exception as e:
        return jsonify({"msg": f"Error creating pod: {str(e)}"}), 500


@app.route('/pods/<pod_name>', methods=['DELETE'])
@jwt_required()
def delete_pod(pod_name):
    current_user = User.query.filter_by(username=get_jwt_identity()).first()
    db_pod = Pod.query.filter_by(name=f"{current_user.username}-{pod_name}", user_id=current_user.id).first()
    
    if not db_pod:
        return jsonify({"msg": "Pod not found or not owned by user"}), 404
    
    try:
        v1.delete_namespaced_pod(name=db_pod.name, namespace="default")
        db.session.delete(db_pod)
        db.session.commit()
        return jsonify({"msg": "Pod deleted successfully"}), 200
    except Exception as e:
        return jsonify({"msg": f"Error deleting pod: {str(e)}"}), 500

@app.route('/pods/<pod_name>/terminal', methods=['GET'])
@jwt_required()
def get_pod_terminal(pod_name):
    current_user = User.query.filter_by(username=get_jwt_identity()).first()
    db_pod = Pod.query.filter_by(name=f"{current_user.username}-{pod_name}", user_id=current_user.id).first()
    
    if not db_pod:
        return jsonify({"msg": "Pod not found or not owned by user"}), 404
    
    # Return terminal access (TO DO)
    return jsonify({"msg": "Terminal access details", "pod_ip": db_pod.ip}), 200

def update_pod_status():
    pods = Pod.query.all()
    for pod in pods:
        try:
            k8s_pod = v1.read_namespaced_pod(name=pod.name, namespace="default")
            pod.status = k8s_pod.status.phase
            pod.ip = k8s_pod.status.pod_ip
        except client.exceptions.ApiException:
            pod.status = "Not Found in Kubernetes"
    db.session.commit()

@app.route('/check', methods=['GET'])
def check_k8s_connection():
    try:
        # Intenta listar los pods en el namespace "default"
        pods = v1.list_namespaced_pod(namespace="default")
        pod_names = [pod.metadata.name for pod in pods.items]
        
        return jsonify({
            "msg": "Kubernetes connection successful",
            "pods": pod_names
        }), 200
    except Exception as e:
        return jsonify({"msg": f"Error connecting to Kubernetes: {str(e)}"}), 500


if __name__ == '__main__':
    with app.app_context():
        db.create_all()
    app.run(host='0.0.0.0', debug=True)
