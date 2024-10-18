from flask import Blueprint
from controller.user_controller import register, login, change_role, get_all_users, get_user_by_id, reset_password

user_bp = Blueprint('user', __name__)

user_bp.route('/register', methods=['POST'])(register)
user_bp.route('/login', methods=['POST'])(login)
user_bp.route('/change_role', methods=['POST'])(change_role)
user_bp.route('/all_users', methods=['GET'])(get_all_users)  
user_bp.route('/user/<int:user_id>', methods=['GET'])(get_user_by_id)  
user_bp.route('/reset_password', methods=['POST'])(reset_password)  