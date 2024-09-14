from flask import request, jsonify
from flask_jwt_extended import get_jwt_identity
from kubernetes import client, config
from model.user import User
from model.pod import Pod
from database.db import db
import random

config.load_kube_config()
v1 = client.CoreV1Api()
apps_v1 = client.AppsV1Api()

def get_pods():
    current_user = User.query.filter_by(username=get_jwt_identity()).first()
    user_pods = Pod.query.filter_by(user_id=current_user.id).all()
    
    pod_list = []
    for pod in user_pods:
        try:
            k8s_pod = v1.read_namespaced_pod(name=pod.name, namespace="default")
            status = k8s_pod.status.phase
            pod_ip = k8s_pod.status.pod_ip

            pod_list.append({
                "name": pod.name,
                "image": pod.image,
                "ports": pod.ports,
                "status": status,
                "ip": pod_ip
            })

        except client.exceptions.ApiException:
            pod_list.append({
                "name": pod.name,
                "status": "Not Found in Kubernetes",
                "ip": "Not Available"
            })

    return jsonify(pod_list), 200

def create_pod():
    current_user = get_jwt_identity()
    
    data = request.get_json()
    name = data.get('name')
    image = data.get('image')
    ports = data.get('ports')  # Lista de puertos, e.g., [80, 8080]
    
    if not name or not image or not ports:
        return jsonify({'msg': 'Name, image, and ports are required'}), 400

    deployment_manifest = {
        "apiVersion": "apps/v1",
        "kind": "Deployment",
        "metadata": {
            "name": name,
            "labels": {
                "app": name
            }
        },
        "spec": {
            "selector": {
                "matchLabels": {
                    "app": name
                }
            },
            "template": {
                "metadata": {
                    "labels": {
                        "app": name
                    }
                },
                "spec": {
                    "containers": [
                        {
                            "name": name,
                            "image": image,
                            "ports": [{"containerPort": port} for port in ports]
                        }
                    ]
                }
            }
        }
    }

    try:
        apps_v1.create_namespaced_deployment(namespace="default", body=deployment_manifest)
    except client.exceptions.ApiException as e:
        return jsonify({'msg': f'Error creating deployment: {e}'}), 500

    node_port = random.randint(30000, 32767)
    
    service_manifest = {
        "apiVersion": "v1",
        "kind": "Service",
        "metadata": {
            "name": f"{name}-service"
        },
        "spec": {
            "type": "NodePort",
            "selector": {
                "app": name
            },
            "ports": [
                {
                    "port": ports[0],  # Puerto expuesto
                    "targetPort": ports[0],  # Primer puerto del contenedor
                    "nodePort": node_port  # Puerto NodePort dinámico
                }
            ]
        }
    }

    try:
        v1.create_namespaced_service(namespace="default", body=service_manifest)
    except client.exceptions.ApiException as e:
        return jsonify({'msg': f'Error creating service: {e}'}), 500

    try:
        service = v1.read_namespaced_service(name=f"{name}-service", namespace="default")
    except client.exceptions.ApiException as e:
        return jsonify({'msg': f'Error retrieving service details: {e}'}), 500

    nodes = v1.list_node()
    internal_ip = None
    for node in nodes.items:
        if node.status.addresses:
            for address in node.status.addresses:
                if address.type == 'InternalIP':
                    internal_ip = address.address
                    break
        if internal_ip:
            break

    if not internal_ip:
        return jsonify({'msg': 'No internal IP found for nodes'}), 500

    return jsonify({
        'msg': 'Pod and service created successfully',
        'podName': name,
        'serviceName': f"{name}-service",
        'nodePort': node_port,
        'internalIP': internal_ip,
        'accessURL': f'http://{internal_ip}:{node_port}'
    }), 201

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
        pods = v1.list_namespaced_pod(namespace="default")
        pod_names = [pod.metadata.name for pod in pods.items]
        return jsonify({"msg": "Kubernetes connection successful"}), 200
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
