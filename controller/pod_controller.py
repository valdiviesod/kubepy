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
        except client.exceptions.ApiException:
            status = "Not Found in Kubernetes"

        pod_list.append({
            "name": pod.name,
            "image": pod.image,
            "ports": pod.ports,
            "status": status,
            "hostname": f"{pod.name}.{current_app.config['DOMAIN']}"
        })

    return jsonify(pod_list), 200

from flask import request, jsonify, current_app
from flask_jwt_extended import get_jwt_identity
from kubernetes import client, config
from model.user import User
from model.pod import Pod
from database.db import db

config.load_kube_config()
apps_v1_api = client.AppsV1Api()
core_v1_api = client.CoreV1Api()
networking_v1_api = client.NetworkingV1Api()

def create_pod():
    current_user = User.query.filter_by(username=get_jwt_identity()).first()
    pod_name = request.json.get('name')
    image = request.json.get('image')
    ports = request.json.get('ports', '80')  # Default to port 80 if not specified

    if not pod_name or not image:
        return jsonify({"msg": "Missing pod name or image"}), 400

    try:
        # Create Deployment
        container = client.V1Container(
            name=pod_name,
            image=image,
            ports=[client.V1ContainerPort(container_port=int(port)) for port in ports.split(',')]
        )
        template = client.V1PodTemplateSpec(
            metadata=client.V1ObjectMeta(labels={"app": pod_name}),
            spec=client.V1PodSpec(containers=[container])
        )
        spec = client.V1DeploymentSpec(
            replicas=1,
            selector=client.V1LabelSelector(
                match_labels={"app": pod_name}
            ),
            template=template
        )
        deployment = client.V1Deployment(
            api_version="apps/v1",
            kind="Deployment",
            metadata=client.V1ObjectMeta(name=f"{current_user.username}-{pod_name}"),
            spec=spec
        )
        apps_v1_api.create_namespaced_deployment(
            namespace="default", body=deployment
        )

        # Create Service
        service_ports = [
            client.V1ServicePort(port=int(port), target_port=int(port))
            for port in ports.split(',')
        ]
        service = client.V1Service(
            api_version="v1",
            kind="Service",
            metadata=client.V1ObjectMeta(
                name=f"{current_user.username}-{pod_name}-service"
            ),
            spec=client.V1ServiceSpec(
                selector={"app": pod_name},
                ports=service_ports
            )
        )
        core_v1_api.create_namespaced_service(namespace="default", body=service)

        # Create Ingress
        ingress = client.V1Ingress(
            api_version="networking.k8s.io/v1",
            kind="Ingress",
            metadata=client.V1ObjectMeta(
                name=f"{current_user.username}-{pod_name}-ingress",
                annotations={
                    "nginx.ingress.kubernetes.io/rewrite-target": "/"
                }
            ),
            spec=client.V1IngressSpec(
                rules=[client.V1IngressRule(
                    host=f"{current_user.username}-{pod_name}.{current_app.config['DOMAIN']}",
                    http=client.V1HTTPIngressRuleValue(
                        paths=[client.V1HTTPIngressPath(
                            path="/",
                            path_type="Prefix",
                            backend=client.V1IngressBackend(
                                service=client.V1IngressServiceBackend(
                                    port=client.V1ServiceBackendPort(
                                        number=int(ports.split(',')[0])
                                    ),
                                    name=f"{current_user.username}-{pod_name}-service"
                                )
                            )
                        )]
                    )
                )]
            )
        )
        networking_v1_api.create_namespaced_ingress(
            namespace="default",
            body=ingress
        )

        # Wait for the pod to be running
        while True:
            pod_list = core_v1_api.list_namespaced_pod(
                namespace="default",
                label_selector=f"app={pod_name}"
            )
            if pod_list.items and pod_list.items[0].status.phase == 'Running':
                pod_ip = pod_list.items[0].status.pod_ip
                break

        # Save pod information to database
        db_pod = Pod(
            name=f"{current_user.username}-{pod_name}",
            image=image,
            ports=ports,
            ip=pod_ip,
            status='Running',
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
            "status": db_pod.status,
            "hostname": f"{current_user.username}-{pod_name}.{current_app.config['DOMAIN']}"
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