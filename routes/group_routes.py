from flask import Blueprint
from controller.group_controller import create_group, update_group, delete_group, get_all_groups, get_group

group_bp = Blueprint('group', __name__)

group_bp.route('/create_group', methods=['POST'])(create_group)
group_bp.route('/update_group/<int:group_id>', methods=['PUT'])(update_group)
group_bp.route('/delete_group/<int:group_id>', methods=['DELETE'])(delete_group)
group_bp.route('/all_groups', methods=['GET'])(get_all_groups)  
group_bp.route('/group/<int:group_id>', methods=['GET'])(get_group) 
