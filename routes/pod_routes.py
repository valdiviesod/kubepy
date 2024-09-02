from flask import Blueprint
from flask_jwt_extended import jwt_required
from controller.pod_controller import get_pods, create_pod, delete_pod, get_pod_terminal, check_k8s_connection, exec_in_pod

pod_bp = Blueprint('pod', __name__)

pod_bp.route('/pods', methods=['GET'])(jwt_required()(get_pods))
pod_bp.route('/pods', methods=['POST'])(jwt_required()(create_pod))
pod_bp.route('/pods/<pod_name>', methods=['DELETE'])(jwt_required()(delete_pod))
pod_bp.route('/pods/<pod_name>/terminal', methods=['GET'])(jwt_required()(get_pod_terminal))
pod_bp.route('/check', methods=['GET'])(check_k8s_connection)
pod_bp.route('/pods/<pod_name>/exec', methods=['POST'])(jwt_required()(exec_in_pod))