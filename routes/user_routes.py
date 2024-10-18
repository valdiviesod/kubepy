from flask import Blueprint
from controller.user_controller import register, login, change_role, get_users

user_bp = Blueprint('user', __name__)

user_bp.route('/register', methods=['POST'])(register)
user_bp.route('/login', methods=['POST'])(login)
user_bp.route('/change_role', methods=['POST'])(change_role)
user_bp.route('/get_users', methods=['GET'])(get_users)  