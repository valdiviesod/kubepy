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

    apps_v1.create_namespaced_deployment(namespace="default", body=deployment)

    # Create Service
    node_port = 32000  # Manually assigned NodePort
    service = client.V1Service(
        api_version="v1",
        kind="Service",
        metadata=client.V1ObjectMeta(name=pod_name),
        spec=client.V1ServiceSpec(
            type="NodePort",
            selector={"app": pod_name},
            ports=[
                client.V1ServicePort(
                    port=ports[0],
                    target_port=ports[0],
                    node_port=node_port
                )
            ]
        )
    )

    v1.create_namespaced_service(namespace="default", body=service)

    # Save Pod to Database
    new_pod = Pod(
        name=pod_name,
        image=image,
        ports=ports,
        user_id=current_user.id
    )
    db.session.add(new_pod)
    db.session.commit()

    return jsonify({
        "pod_name": pod_name,
        "node_port": node_port
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
