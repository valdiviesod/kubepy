from flask import request, jsonify, current_app
from flask_jwt_extended import get_jwt_identity
from kubernetes import client, config
from model.user import User
from model.pod import Pod
from database.db import db
import time

config.load_kube_config()
v1 = client.CoreV1Api()
apps_v1 = client.AppsV1Api()
networking_v1 = client.NetworkingV1Api()

def get_pods():
    current_user = User.query.filter_by(username=get_jwt_identity()).first()
    user_pods = Pod.query.filter_by(user_id=current_user.id).all()
    
    pod_list = []
    for pod in user_pods:
        try:
            k8s_pod = v1.read_namespaced_pod(name=pod.name, namespace="default")
            status = k8s_pod.status.phase

            # Obtain the IP address of the pod
            pod_ip = k8s_pod.status.pod_ip

            # Obtain the hostname from the ingress
            ingress_list = networking_v1.list_namespaced_ingress(namespace="default")
            ingress_hostname = next(
                (rule.host for rule in ingress_list.items[0].spec.rules
                 if rule.host.startswith(pod.name)), 
                "Not Found"
            )

        except client.exceptions.ApiException:
            status = "Not Found in Kubernetes"
            pod_ip = "Not Available"
            ingress_hostname = "Not Available"

        pod_list.append({
            "name": pod.name,
            "image": pod.image,
            "ports": pod.ports,
            "status": status,
            "ip": pod_ip,

        })

    return jsonify(pod_list), 200


def create_pod():
    # Obtener la información del usuario autenticado
    current_user = get_jwt_identity()
    
    # Obtener los datos del request
    data = request.get_json()
    name = data.get('name')
    image = data.get('image')
    ports = data.get('ports')  
    
    if not name or not image or not ports:
        return jsonify({'msg': 'Name, image, and ports are required'}), 400

    # Crear el pod
    pod_manifest = {
        "apiVersion": "v1",
        "kind": "Pod",
        "metadata": {
            "name": name,
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

    try:
        v1.create_namespaced_pod(namespace="default", body=pod_manifest)
    except client.exceptions.ApiException as e:
        return jsonify({'msg': f'Error creating pod: {e}'}), 500

    # Crear el servicio de tipo NodePort
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
                    "port": 80,
                    "targetPort": ports[0],  # Usar el primer puerto del contenedor
                    "nodePort": node_port
                }
            ]
        }
    }

    try:
        v1.create_namespaced_service(namespace="default", body=service_manifest)
    except client.exceptions.ApiException as e:
        return jsonify({'msg': f'Error creating service: {e}'}), 500

    # Obtener la IP interna del nodo
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

    # Devolver la información al usuario
    return jsonify({
        'msg': 'Pod and service created successfully',
        'nodePort': node_port,
        'internalIP': internal_ip,
        'accessURL': f'http://cca.bucaramanga.upb.edu.co}:{node_port}'
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
        # Intenta listar los pods en el namespace "default"
        pods = v1.list_namespaced_pod(namespace="default")
        pod_names = [pod.metadata.name for pod in pods.items]
        
        return jsonify({
            "msg": "Kubernetes connection successful"
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