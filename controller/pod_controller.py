from flask import request, jsonify
from flask_jwt_extended import get_jwt_identity, jwt_required
from kubernetes import client, config
from model.user import User
from model.pod import Pod
from model.group import Group
from database.db import db
from sqlalchemy.orm import aliased
from flask_jwt_extended import jwt_required

config.load_kube_config()
v1 = client.CoreV1Api()
apps_v1 = client.AppsV1Api()

@jwt_required()
def get_pods():
    current_user = User.query.filter_by(username=get_jwt_identity()).first()
    if not current_user:
        return jsonify({"msg": "User not found"}), 404

    # Obtiene todos los pods que pertenecen directamente al usuario
    user_pods = Pod.query.filter_by(user_id=current_user.id).all()

    # Obtiene todos los grupos del usuario
    user_groups = current_user.groups

    # Encuentra todos los pods que pertenecen a los grupos del usuario
    group_pods = []
    for group in user_groups:
        group_pods.extend(group.pods)

    # Elimina duplicados en la lista de pods
    all_pods = list({pod.id: pod for pod in user_pods + group_pods}.values())

    # Formatea la respuesta incluyendo node_ports
    pods_data = []
    for pod in all_pods:
        pod_data = {
            "id": pod.id,
            "name": pod.name,
            "image": pod.image,
            "ports": pod.ports,
            "node_ports": pod.node_ports.split(',') if pod.node_ports else []  # Convert string to list
        }
        # Convert node_ports to integers
        if pod_data["node_ports"]:
            pod_data["node_ports"] = [int(port) for port in pod_data["node_ports"]]
        pods_data.append(pod_data)

    return jsonify(pods=pods_data), 200

def create_pod():
    current_user = User.query.filter_by(username=get_jwt_identity()).first()
    if not current_user:
        return jsonify({"msg": "User not found"}), 404

    data = request.get_json()
    name = data.get('name')
    image = data.get('image')
    ports = data.get('ports')

    if not name or not image or not ports:
        return jsonify({"msg": "Missing required fields"}), 400

    pod_name = f"{current_user.username}-{name}"

    try:
        # Convert ports to int and filter out invalid entries
        ports = [int(port) for port in ports.split(',') if port.strip().isdigit()]
    except ValueError:
        return jsonify({"msg": "Invalid port value"}), 400

    if not ports:
        return jsonify({"msg": "No valid ports provided"}), 400

    # Ensure nodePorts are unique and not used already
    existing_services = v1.list_namespaced_service(namespace="default")
    used_node_ports = {port.node_port for svc in existing_services.items for port in svc.spec.ports if svc.spec.type == "NodePort"}

    node_ports = []
    for i, port in enumerate(ports):
        node_port = 30000 + i
        while node_port in used_node_ports:
            node_port += 1
        node_ports.append(node_port)
        used_node_ports.add(node_port)

    # Create Deployment
    deployment = client.V1Deployment(   
        api_version="apps/v1",
        kind="Deployment",
        metadata=client.V1ObjectMeta(name=pod_name),
        spec=client.V1DeploymentSpec(
            selector=client.V1LabelSelector(
                match_labels={"app": pod_name}
            ),
            template=client.V1PodTemplateSpec(
                metadata=client.V1ObjectMeta(labels={"app": pod_name}),
                spec=client.V1PodSpec(
                    containers=[
                        client.V1Container(
                            name=pod_name,
                            image=image,
                            ports=[client.V1ContainerPort(container_port=port) for port in ports]
                        )
                    ]
                )
            )
        )
    )

    try:
        apps_v1.create_namespaced_deployment(namespace="default", body=deployment)
    except client.exceptions.ApiException as e:
        return jsonify({"msg": f"Error creating deployment: {str(e)}"}), 500

    # Create Service
    service_ports = [
        client.V1ServicePort(
            name=f"port-{i}",
            port=port,
            target_port=port,
            node_port=node_ports[i] if i < len(node_ports) else None
        )
        for i, port in enumerate(ports)
    ]
    
    service = client.V1Service(
        api_version="v1",
        kind="Service",
        metadata=client.V1ObjectMeta(name=pod_name),
        spec=client.V1ServiceSpec(
            type="NodePort",
            selector={"app": pod_name},
            ports=service_ports
        )
    )

    try:
        v1.create_namespaced_service(namespace="default", body=service)
    except client.exceptions.ApiException as e:
        return jsonify({"msg": f"Error creating service: {str(e)}"}), 500

    # Convert ports and node_ports lists to comma-separated strings
    ports_str = ','.join(map(str, ports))
    node_ports_str = ','.join(map(str, node_ports))

    # Save Pod to Database
    new_pod = Pod(
        name=pod_name,
        image=image,
        ports=ports_str,
        node_ports=node_ports_str,  # Save node_ports as comma-separated string
        user_id=current_user.id
    )
    db.session.add(new_pod)
    db.session.commit()

    return jsonify({
        "msg": "Pod created successfully",
        "pod_name": pod_name,
        "node_ports": node_ports
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
