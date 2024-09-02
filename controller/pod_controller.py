from flask import request, jsonify, current_app
from flask_jwt_extended import get_jwt_identity
from kubernetes import client, config
from kubernetes.stream import stream
from model.user import User
from model.pod import Pod
from database.db import db
import time

config.load_kube_config()
v1 = client.CoreV1Api()

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
            "status": status
        })

    return jsonify(pod_list), 200

def create_pod():
    current_user = User.query.filter_by(username=get_jwt_identity()).first()
    pod_name = request.json.get('name')
    image = request.json.get('image')
    ports = request.json.get('ports')
    
    if not pod_name or not image:
        return jsonify({"msg": "Missing pod name or image"}), 400
    
    user_pod_count = Pod.query.filter_by(user_id=current_user.id).count()
    if user_pod_count >= current_app.config['MAX_PODS_PER_USER']:
        return jsonify({"msg": f"Maximum number of pods ({current_app.config['MAX_PODS_PER_USER']}) reached for this user"}), 400

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
        timeout = 300  # Timeout in seconds
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

def get_pod_terminal(pod_name):
    current_user = User.query.filter_by(username=get_jwt_identity()).first()
    db_pod = Pod.query.filter_by(name=f"{current_user.username}-{pod_name}", user_id=current_user.id).first()
    
    if not db_pod:
        return jsonify({"msg": "Pod not found or not owned by user"}), 404
    
    # Return terminal access (TO DO)
    return jsonify({"msg": "Terminal access details", "pod_ip": db_pod.ip}), 200

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

def exec_in_pod(pod_name):
    current_user = User.query.filter_by(username=get_jwt_identity()).first()
    db_pod = Pod.query.filter_by(name=f"{current_user.username}-{pod_name}", user_id=current_user.id).first()
    
    if not db_pod:
        return jsonify({"msg": "Pod not found or not owned by user"}), 404
    
    command = request.json.get('command')
    
    if not command:
        return jsonify({"msg": "Missing command"}), 400
    
    try:
        exec_command = ['/bin/sh', '-c', command]
        resp = stream(
            v1.connect_get_namespaced_pod_exec,
            name=db_pod.name,
            namespace='default',
            command=exec_command,
            stderr=True, stdin=False,
            stdout=True, tty=False
        )
        
        return jsonify({"output": resp}), 200
    except Exception as e:
        return jsonify({"msg": f"Error executing command: {str(e)}"}), 500