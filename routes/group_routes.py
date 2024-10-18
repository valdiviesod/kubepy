from flask import Blueprint
from controller.group_controller import create_group, update_group, delete_group, get_groups

group_bp = Blueprint('group', __name__)

group_bp.route('/create_group', methods=['POST'])(create_group)
group_bp.route('/update_group/<int:group_id>', methods=['PUT'])(update_group)
group_bp.route('/delete_group/<int:group_id>', methods=['DELETE'])(delete_group)
group_bp.route('/get_groups', methods=['POST'])(get_groups)

