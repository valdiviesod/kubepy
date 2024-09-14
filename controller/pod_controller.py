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
            "hostname": ingress_hostname
        })

    return jsonify(pod_list), 200


def create_pod():
    data = request.json
    name = data.get('name')
    image = data.get('image')
    ports = data.get('ports', '')

    # Create Pod
    container = client.V1Container(
        name=name,
        image=image,
        ports=[client.V1ContainerPort(container_port=int(port)) for port in ports.split(",")]
    )
    pod_spec = client.V1PodSpec(containers=[container])
    pod = client.V1Pod(
        api_version="v1",
        kind="Pod",
        metadata=client.V1ObjectMeta(name=name),
        spec=pod_spec
    )
    v1.create_namespaced_pod(namespace="default", body=pod)

    # Wait for the pod to be ready
    while True:
        try:
            pod_status = v1.read_namespaced_pod(name=name, namespace="default").status.phase
            if pod_status == "Running":
                break
        except client.exceptions.ApiException:
            pass
        time.sleep(5)

    # Create a service to expose the pod
    service = client.V1Service(
        api_version="v1",
        kind="Service",
        metadata=client.V1ObjectMeta(name=name),
        spec=client.V1ServiceSpec(
            selector={"app": name},
            ports=[client.V1ServicePort(
                port=int(ports.split(",")[0]),  # Assuming single port for simplicity
                target_port=int(ports.split(",")[0])
            )]
        )
    )
    v1.create_namespaced_service(namespace="default", body=service)

    # Create ingress to expose the service
    ingress = client.V1Ingress(
        api_version="networking.k8s.io/v1",
        kind="Ingress",
        metadata=client.V1ObjectMeta(
            name=name,
            annotations={"nginx.ingress.kubernetes.io/rewrite-target": "/"}
        ),
        spec=client.V1IngressSpec(
            rules=[client.V1IngressRule(
                host=f"{name}.example.com",  # Replace with actual domain or use a placeholder
                http=client.V1HTTPIngressRuleValue(
                    paths=[client.V1HTTPIngressPath(
                        path="/",
                        path_type="Prefix",
                        backend=client.V1IngressBackend(
                            service=client.V1IngressServiceBackend(
                                port=client.V1ServiceBackendPort(number=int(ports.split(",")[0])),
                                name=name
                            )
                        )
                    )]
                )
            )]
        )
    )
    networking_v1.create_namespaced_ingress(namespace="default", body=ingress)

    # Store pod info in the database
    current_user = User.query.filter_by(username=get_jwt_identity()).first()
    new_pod = Pod(
        name=name,
        image=image,
        ports=ports,
        user_id=current_user.id
    )
    db.session.add(new_pod)
    db.session.commit()

    return jsonify({"message": "Pod created successfully"}), 201

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