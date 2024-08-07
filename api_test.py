from flask import Flask, request, jsonify
from flask_sqlalchemy import SQLAlchemy
from flask_bcrypt import Bcrypt
from flask_jwt_extended import JWTManager, jwt_required, create_access_token, get_jwt_identity
from kubernetes import client, config
import pymysql
pymysql.install_as_MySQLdb()chm


app = Flask(__name__)

# Configuration
app.config['SQLALCHEMY_DATABASE_URI'] = 'mysql://root:1701046@localhost/k8s_management' # Usuario y contraseña solo de testing
app.config['SQLALCHEMY_TRACK_MODIFICATIONS'] = False
app.config['JWT_SECRET_KEY'] = '1701046' # Clave secreta solo de testing  
app.config['MAX_PODS_PER_USER'] = 5

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

# Pod model
class Pod(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    name = db.Column(db.String(120), nullable=False)
    ip = db.Column(db.String(15), nullable=True)
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
    return jsonify([{"name": pod.name, "ip": pod.ip} for pod in user_pods]), 200

@app.route('/pods', methods=['POST'])
@jwt_required()
def create_pod():
    current_user = User.query.filter_by(username=get_jwt_identity()).first()
    pod_name = request.json.get('name')
    image = request.json.get('image')
    
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
                    "image": image
                }]
            }
        }
        
        api_response = v1.create_namespaced_pod(body=pod_manifest, namespace="default")
        
        # Wait for the pod to be running and get its IP
        while True:
            pod = v1.read_namespaced_pod(name=f"{current_user.username}-{pod_name}", namespace="default")
            if pod.status.phase == 'Running' and pod.status.pod_ip:
                pod_ip = pod.status.pod_ip
                break
        
        db_pod = Pod(name=f"{current_user.username}-{pod_name}", ip=pod_ip, user_id=current_user.id)
        db.session.add(db_pod)
        db.session.commit()
        
        return jsonify({"msg": "Pod created successfully", "name": db_pod.name, "ip": db_pod.ip}), 201
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

if __name__ == '__main__':
    db.create_all()
    app.run(debug=True)