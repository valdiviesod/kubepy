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
    try:
        current_user = User.query.filter_by(username=get_jwt_identity()).first()

        if not current_user:
            return jsonify({"message": "User not found"}), 404

        # Get the request data for the pod creation
        pod_name = request.json.get("name")
        image = request.json.get("image", "nginx")
        ports = request.json.get("ports", [80])

        if not pod_name:
            return jsonify({"message": "Pod name is required"}), 400

        # Create a Kubernetes deployment for the pod
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
                                name="web-server",
                                image=image,
                                ports=[
                                    client.V1ContainerPort(container_port=int(port))
                                    for port in ports
                                ],
                            )
                        ]
                    ),
                ),
            ),
        )

        # Create the deployment in Kubernetes
        apps_v1.create_namespaced_deployment(namespace="default", body=deployment)

        # Create a NodePort service without specifying the nodePort, allowing Kubernetes to assign a dynamic NodePort
        service = client.V1Service(
            api_version="v1",
            kind="Service",
            metadata=client.V1ObjectMeta(name=f"{pod_name}-service"),
            spec=client.V1ServiceSpec(
                selector={"app": pod_name},
                type="NodePort",
                ports=[
                    client.V1ServicePort(
                        port=80,
                        target_port=80,
                    )
                ],
            ),
        )

        # Create the service in Kubernetes
        created_service = v1.create_namespaced_service(namespace="default", body=service)

        # Add the pod to the database
        new_pod = Pod(
            name=pod_name,
            image=image,
            ports=ports,
            user_id=current_user.id,
            created_at=time.time()
        )
        db.session.add(new_pod)
        db.session.commit()

        # Get the dynamically assigned NodePort
        node_port = created_service.spec.ports[0].node_port if created_service.spec.ports else None

        # Get a Node IP to expose the service
        node_list = v1.list_node()
        node_ip = next(
            (addr.address for addr in node_list.items[0].status.addresses
             if addr.type == "ExternalIP"), "localhost"
        )

        # Check if node_ip and node_port are valid
        if not node_ip:
            node_ip = "localhost"
        if not node_port:
            return jsonify({"message": "Error: NodePort not assigned"}), 500

        # Return information for accessing the pod
        return jsonify({
            "message": "Pod created successfully",
            "name": pod_name,
            "image": image,
            "node_ip": node_ip,
            "node_port": node_port  # The dynamically assigned NodePort for external access
        }), 201

    except client.exceptions.ApiException as e:
        return jsonify({"msg": f"Kubernetes API error: {e.reason}"}), e.status
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